from pathlib import Path

import pytest

from nscraper import (
    apply_pretty_format,
    auto_output_path,
    classify_response_type,
    InvalidHeadersError,
    InvalidUrlError,
    basic_html_transform,
    fast_html_transform,
    parse_headers,
    pretty_html,
    pretty_json,
    ResponseTypeClassifier,
    validate_url,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://example.com", "http://example.com"),
        ("https://example.com", "https://example.com"),
    ],
)
def test_validate_url_accepts_standard_urls(url, expected):
    assert validate_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "https://example.com/path with space",
        "ftp://example.com",
        "http://",
    ],
)
def test_validate_url_rejects_invalid_urls(url):
    with pytest.raises(InvalidUrlError, match="invalid url"):
        validate_url(url)


def test_parse_headers_rejects_missing():
    with pytest.raises(InvalidHeadersError):
        parse_headers(None)


def test_parse_headers_accepts_json_object():
    headers = parse_headers('{"Accept": "text/html"}')
    assert headers == {"Accept": "text/html"}


def test_basic_html_transform_removes_tags():
    cleaned = basic_html_transform("<html><body>Hello</body></html>")
    assert "<html" in cleaned
    assert "<body>" in cleaned
    assert "Hello" in cleaned


def test_basic_html_transform_strips_scripts_and_styles():
    html = """
    <html>
      <head>
        <style>body { color: red; }</style>
        <script>alert('x')</script>
      </head>
      <body><noscript>ignore</noscript><div>Hello</div></body>
    </html>
    """
    cleaned = basic_html_transform(html)
    assert "<script>" not in cleaned
    assert "<style>" not in cleaned
    assert "<noscript>" not in cleaned
    assert "body { color: red; }" not in cleaned
    assert "alert('x')" not in cleaned
    assert "Hello" in cleaned
    assert "<html>" in cleaned


def test_basic_html_transform_handles_broken_markup():
    html = "<div>Hello<script>bad()</script><style>.x{}</style><span>World</span>"
    cleaned = basic_html_transform(html)
    assert "<script>" not in cleaned
    assert "<style>" not in cleaned
    assert "Hello" in cleaned
    assert "World" in cleaned
    assert "<div>" in cleaned or "<span>" in cleaned


def test_basic_html_transform_removes_hidden_and_ad_like_nodes():
    html = """
    <html>
      <body>
        <div class="ads">Ad</div>
        <div class="newsletter">Newsletter</div>
        <div aria-hidden="true">Hidden</div>
        <div hidden>Hidden attr</div>
        <div class="content">Keep</div>
      </body>
    </html>
    """
    cleaned = basic_html_transform(html)
    assert "Ad" not in cleaned
    assert "Newsletter" not in cleaned
    assert "Hidden" not in cleaned
    assert "Keep" in cleaned


def test_fast_html_transform_keeps_head_and_ad_like_nodes():
    html = """
    <html>
      <head><title>Keep</title><meta name="x" content="1"></head>
      <body>
        <div class="ads">Ad</div>
        <div hidden>Hidden attr</div>
        <script>bad()</script>
        <div class="content">Keep</div>
      </body>
    </html>
    """
    cleaned = fast_html_transform(html)
    assert "<script" not in cleaned
    assert "bad()" not in cleaned
    assert "Ad" in cleaned
    assert "Hidden attr" in cleaned
    assert "<title>Keep</title>" in cleaned
    assert "Keep" in cleaned


def test_pretty_html_formats_output_with_line_breaks():
    pretty = pretty_html("<html><body><div>Hello</div></body></html>")

    assert "<html>" in pretty
    assert "\n" in pretty
    assert "Hello" in pretty


def test_pretty_json_formats_output_with_indentation():
    pretty = pretty_json('{"ok":true}')

    assert "{\n" in pretty
    assert '  "ok": true\n' in pretty


def test_apply_pretty_format_uses_json_for_json_content_type():
    pretty = apply_pretty_format('{"ok":true}', classify_response_type("application/json"))

    assert '  "ok": true' in pretty


def test_response_type_classifier_detects_html_json_and_text():
    classifier = ResponseTypeClassifier()

    assert classifier.classify("text/html; charset=utf-8").kind == "html"
    assert classifier.classify("application/json").kind == "json"
    assert classifier.classify("text/plain").kind == "text"
    assert classifier.classify("application/xml").kind == "xml"


def test_auto_output_path_uses_json_suffix_for_json_content():
    path = auto_output_path(Path(".nscraper") / "httpbin.org", classify_response_type("application/json"))

    assert path == Path(".nscraper") / "httpbin.org.json"
