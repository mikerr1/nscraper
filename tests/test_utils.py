from pathlib import Path

import pytest

from nscraper import InvalidCookiesError
from nscraper.utils import load_cookies_file


def test_load_cookies_file_returns_none_when_missing():
    assert load_cookies_file(None) is None


def test_load_cookies_file_reads_json(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text('{"sessionid": "abc123"}', encoding="utf-8")

    assert load_cookies_file(cookie_file) == {"sessionid": "abc123"}


def test_load_cookies_file_rejects_missing_file(tmp_path):
    with pytest.raises(InvalidCookiesError, match="cookies file not found"):
        load_cookies_file(tmp_path / "missing.json")


def test_load_cookies_file_rejects_invalid_json(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text("{not json}", encoding="utf-8")

    with pytest.raises(InvalidCookiesError, match="valid JSON"):
        load_cookies_file(cookie_file)


def test_load_cookies_file_rejects_non_object_json(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text('["sessionid", "abc123"]', encoding="utf-8")

    with pytest.raises(InvalidCookiesError, match="non-empty JSON object"):
        load_cookies_file(cookie_file)


def test_load_cookies_file_rejects_empty_object(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text("{}", encoding="utf-8")

    with pytest.raises(InvalidCookiesError, match="non-empty JSON object"):
        load_cookies_file(cookie_file)


def test_load_cookies_file_rejects_non_string_values(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text('{"sessionid": 123}', encoding="utf-8")

    with pytest.raises(InvalidCookiesError, match="cookie values must be strings"):
        load_cookies_file(cookie_file)
