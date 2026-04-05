"""Module entry point for nscraper."""

from __future__ import annotations

import argparse
from pathlib import Path

from .core import get_scraper
from .errors import NscraperError
from .models import ScrapeOptions
from .utils import DEFAULT_HEADERS, load_cookies_file, parse_headers


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
    parser.add_argument("-o", "--output", help="Output path for HTML")
    parser.add_argument(
        "-t",
        "--transform",
        choices=("raw", "basic_html"),
        default="raw",
        help="Transform mode",
    )
    return parser


def _build_options(args: argparse.Namespace) -> ScrapeOptions:
    headers = DEFAULT_HEADERS if args.headers == "default" else parse_headers(args.headers)
    return ScrapeOptions(
        url=args.url,
        engine=args.engine,
        proxy=args.proxy,
        headers=headers,
        cookies=load_cookies_file(args.cookies_file),
        timeout=args.timeout,
        output_path=Path(args.output) if args.output else None,
        transform=args.transform,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        options = _build_options(args)
        content = get_scraper(options).scrape()
    except NscraperError as exc:
        raise SystemExit(str(exc)) from exc
    if not options.output_path:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
