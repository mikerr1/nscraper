"""Module entry point for nscraper."""

from __future__ import annotations

import argparse
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from .errors import InvalidOutputPathError, NscraperError
from .models import ScrapeOptions
from .logging import debug_logger
from .scraper import get_scraper
from .utils import DEFAULT_HEADERS, load_cookies_file, normalize_headers, parse_headers, validate_url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nscraper")
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    parser.add_argument(
        "-e",
        "--engine",
        choices=("http", "seleniumbase"),
        default="http",
        help="Request engine",
    )
    parser.add_argument("-p", "--proxy", help="Proxy URL")
    parser.add_argument("-H", "--headers", required=True, help='Headers as JSON string or "default"')
    parser.add_argument("-c", "--cookies-file", help="Path to a JSON cookies file")
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds")
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        const="",
        help="Output path for HTML. Missing parent directories are created automatically.",
    )
    parser.add_argument("--print", action="store_true", dest="print_output", help="Print result to stdout")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the final HTML output")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Compatibility flag. Runtime status lines are printed by default.",
    )
    parser.add_argument(
        "-t",
        "--transform",
        choices=("raw", "basic", "fast"),
        help="Transform mode",
    )
    return parser


def _build_options(args: argparse.Namespace) -> ScrapeOptions:
    url = validate_url(args.url)
    headers = DEFAULT_HEADERS if args.headers == "default" else parse_headers(args.headers)
    output_path, auto_output = _resolve_output_path(url, args.output)
    return ScrapeOptions(
        url=url,
        engine=args.engine,
        proxy=args.proxy,
        headers=normalize_headers(headers),
        cookies=load_cookies_file(args.cookies_file),
        timeout=args.timeout,
        output_path=output_path,
        auto_output=auto_output,
        transform=args.transform,
        pretty=args.pretty,
        debug=args.debug,
    )


def _resolve_output_path(url: str, raw_output: str | None) -> tuple[Path | None, bool]:
    if raw_output is None:
        return None, False
    if raw_output == "":
        return _default_output_path(url), True
    output_path = Path(raw_output)
    if output_path.is_absolute():
        return output_path, False
    raise InvalidOutputPathError("output path must be absolute, or use bare -o for automatic output")


def _default_output_path(url: str) -> Path:
    parsed = urlparse(url)
    netloc = parsed.netloc or "output"
    path_label = _path_label(parsed.path, parsed.query)
    return Path(".nscraper") / netloc / path_label


def _path_label(path: str, query: str = "") -> str:
    cleaned = path.strip("/")
    if not cleaned:
        base = "index"
    else:
        segments = [_sanitize_path_segment(segment) for segment in cleaned.split("/") if segment]
        base = str(Path(*segments)) if segments else "index"
    if not query:
        return base
    query_hash = hashlib.sha1(query.encode("utf-8")).hexdigest()[:8]
    path_obj = Path(base)
    return str(path_obj.parent / f"{path_obj.name}__{query_hash}") if path_obj.parent != Path(".") else f"{path_obj.name}__{query_hash}"


def _sanitize_path_segment(segment: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", segment).strip("._")
    return normalized or "index"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started_at = time.perf_counter()
    try:
        options = _build_options(args)
        logger = debug_logger(True)
        logger.log(
            "options_ready",
            engine=options.engine,
            transform=options.transform,
            output=options.output_path,
        )
        scraper = get_scraper(options)
        scrape_result = scraper.scrape()
    except NscraperError as exc:
        raise SystemExit(str(exc)) from exc
    logger.log("main_complete", total_ms=logger.elapsed_ms(started_at))
    if args.print_output:
        written_path = scraper.written_output_path if options.output_path else None
        output = written_path.read_text(encoding="utf-8") if written_path else scrape_result.content
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
