from pathlib import Path

import pytest

from nscraper import InvalidCookiesError
from nscraper.utils import load_cookies_file, write_output


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


def test_write_output_creates_missing_parent_directories(tmp_path):
    output_path = tmp_path / "scraped_data" / "kompas.com.html"

    created_parent = write_output(output_path, "<html></html>")

    assert created_parent is True
    assert output_path.read_text(encoding="utf-8") == "<html></html>"


def test_write_output_overwrites_existing_file_atomically(tmp_path):
    output_path = tmp_path / "scraped_data" / "kompas.com.html"
    write_output(output_path, "old")

    created_parent = write_output(output_path, "new")

    assert created_parent is False
    assert output_path.read_text(encoding="utf-8") == "new"


def test_write_output_creates_lock_file(tmp_path):
    output_path = tmp_path / "scraped_data" / "kompas.com.html"

    write_output(output_path, "<html></html>")

    lock_path = output_path.with_name("kompas.com.html.lock")
    assert lock_path.exists()
