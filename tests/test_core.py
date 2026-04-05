import pytest

from nscraper import InvalidHeadersError, InvalidUrlError, basic_html_transform, parse_headers, validate_url


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
