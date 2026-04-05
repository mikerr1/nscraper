from argparse import Namespace

import pytest

from nscraper import InvalidCookiesError, ScrapeOptions
from nscraper.__main__ import _build_options
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
            transform="raw",
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
            transform="raw",
        )
    )

    assert options.headers == {"Accept": "application/json"}
    assert isinstance(options, ScrapeOptions)


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
            transform="raw",
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
            transform="raw",
        )
    )

    assert options.cookies == {"sessionid": "abc123"}


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
                transform="raw",
            )
        )
