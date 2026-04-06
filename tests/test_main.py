from argparse import Namespace
from pathlib import Path

import pytest

from nscraper import (
    InvalidCookiesError,
    InvalidOutputPathError,
    NetworkResult,
    ResultData,
    ScrapeOptions,
    ScrapeResult,
)
from nscraper.__main__ import _build_options, main
from nscraper.utils import DEFAULT_HEADERS


def test_default_headers_are_used_when_explicitly_requested():
    options = _build_options(
        Namespace(
            url="https://example.com",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output=None,
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.headers == DEFAULT_HEADERS
    assert options.headers["User-Agent"] == (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    )


def test_explicit_headers_override_defaults():
    options = _build_options(
        Namespace(
            url="https://example.com",
            engine="http",
            proxy=None,
            headers='{"Accept": "application/json"}',
            cookies_file=None,
            timeout=3.0,
            output=None,
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.headers == {"Accept": "application/json"}
    assert isinstance(options, ScrapeOptions)
    assert options.url == "https://example.com"


def test_cookie_file_is_optional(tmp_path):
    options = _build_options(
        Namespace(
            url="https://example.com",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output=None,
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.cookies is None


def test_cookie_file_is_loaded(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text('{"sessionid": "abc123"}', encoding="utf-8")
    options = _build_options(
        Namespace(
            url="https://example.com",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=cookie_file,
            timeout=3.0,
            output=None,
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.cookies == {"sessionid": "abc123"}


def test_relative_output_path_uses_dot_nscraper_netloc_filename():
    with pytest.raises(InvalidOutputPathError, match="output path must be absolute"):
        _build_options(
            Namespace(
                url="https://example.com/news",
                engine="http",
                proxy=None,
                headers="default",
                cookies_file=None,
                timeout=3.0,
                output="page.html",
                transform=None,
                pretty=False,
                debug=False,
            )
        )


def test_absolute_output_path_is_kept():
    options = _build_options(
        Namespace(
            url="https://example.com/news",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output="/tmp/page.html",
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert str(options.output_path) == "/tmp/page.html"
    assert options.auto_output is False


def test_bare_output_flag_uses_dot_nscraper_netloc_filename():
    options = _build_options(
        Namespace(
            url="https://example.com/news",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output="",
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.output_path == Path(".nscraper") / "example.com" / "news"
    assert options.auto_output is True


def test_bare_output_flag_preserves_nested_path_segments():
    options = _build_options(
        Namespace(
            url="https://example.com/news/world_index",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output="",
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.output_path == Path(".nscraper") / "example.com" / "news" / "world_index"
    assert options.auto_output is True


def test_bare_output_flag_adds_query_hash():
    options = _build_options(
        Namespace(
            url="https://example.com/get?test=1",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output="",
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.output_path == Path(".nscraper") / "example.com" / "get__16afe3e7"
    assert options.auto_output is True


def test_bare_output_flag_uses_index_for_root_path():
    options = _build_options(
        Namespace(
            url="https://example.com/",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output="",
            transform=None,
            pretty=False,
            debug=False,
        )
    )

    assert options.output_path == Path(".nscraper") / "example.com" / "index"
    assert options.auto_output is True


def test_cookie_file_invalid_json_fails_fast(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text("{not json}", encoding="utf-8")

    with pytest.raises(InvalidCookiesError, match="valid JSON"):
        _build_options(
            Namespace(
                url="https://example.com",
                engine="http",
                proxy=None,
                headers="default",
                cookies_file=cookie_file,
                timeout=3.0,
                output=None,
                transform=None,
                pretty=False,
                debug=False,
            )
        )


def test_build_options_sets_pretty_flag():
    options = _build_options(
        Namespace(
            url="https://example.com",
            engine="http",
            proxy=None,
            headers="default",
            cookies_file=None,
            timeout=3.0,
            output=None,
            transform=None,
            pretty=True,
            debug=False,
        )
    )

    assert options.pretty is True


def test_main_logs_to_stderr_by_default(monkeypatch, capsys):
    class DummyScraper:
        def scrape(self) -> ScrapeResult:
            return ScrapeResult(
                network=NetworkResult(),
                result=ResultData(),
                content="<html>Hello</html>",
            )

    monkeypatch.setattr("nscraper.__main__.get_scraper", lambda options: DummyScraper())

    exit_code = main(
        [
            "--url",
            "https://example.com",
            "-H",
            "default",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert "[nscraper] options_ready" in captured.err
    assert "[nscraper] main_complete" in captured.err


def test_main_debug_flag_keeps_same_runtime_logs(monkeypatch, capsys):
    class DummyScraper:
        def scrape(self) -> ScrapeResult:
            return ScrapeResult(
                network=NetworkResult(),
                result=ResultData(),
                content="<html>Hello</html>",
            )

    monkeypatch.setattr("nscraper.__main__.get_scraper", lambda options: DummyScraper())

    exit_code = main(["--url", "https://example.com", "-H", "default", "-d"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "[nscraper] options_ready" in captured.err
    assert "[nscraper] main_complete" in captured.err


def test_main_only_prints_when_explicitly_requested(monkeypatch, capsys):
    class DummyScraper:
        def scrape(self) -> ScrapeResult:
            return ScrapeResult(
                network=NetworkResult(),
                result=ResultData(),
                content="<html>Hello</html>",
            )

    monkeypatch.setattr("nscraper.__main__.get_scraper", lambda options: DummyScraper())

    exit_code = main(["--url", "https://example.com", "-H", "default", "--print"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "<html>Hello</html>" in captured.out


def test_main_prints_written_output_when_output_path_is_set(monkeypatch, capsys, tmp_path):
    class DummyScraper:
        def __init__(self, output_path):
            self.written_output_path = output_path

        def scrape(self) -> ScrapeResult:
            self.written_output_path.write_text("<html>From file</html>", encoding="utf-8")
            return ScrapeResult(
                network=NetworkResult(),
                result=ResultData(output_path=self.written_output_path, bytes_written=22, content_type="text/html"),
                content="<html>From scraper</html>",
            )

    output_path = tmp_path / "page.html"
    monkeypatch.setattr("nscraper.__main__.get_scraper", lambda options: DummyScraper(output_path))

    exit_code = main(
        [
            "--url",
            "https://example.com",
            "-H",
            "default",
            "--output",
            str(output_path),
            "--print",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "<html>From file</html>" in captured.out


def test_main_prints_written_json_output_from_auto_path(monkeypatch, capsys, tmp_path):
    class DummyScraper:
        def __init__(self) -> None:
            self.written_output_path = tmp_path / ".nscraper" / "example.com.json"

        def scrape(self) -> ScrapeResult:
            self.written_output_path.parent.mkdir(parents=True, exist_ok=True)
            self.written_output_path.write_text('{\n  "ok": true\n}', encoding="utf-8")
            return ScrapeResult(
                network=NetworkResult(),
                result=ResultData(output_path=self.written_output_path, bytes_written=16, content_type="application/json"),
                content='{"ok":true}',
            )

    monkeypatch.setattr("nscraper.__main__.get_scraper", lambda options: DummyScraper())

    exit_code = main(
        [
            "--url",
            "https://example.com/api",
            "-H",
            "default",
            "--output",
            "--print",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"ok": true' in captured.out
