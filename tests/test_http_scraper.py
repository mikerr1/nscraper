from dataclasses import replace
import niquests
import pytest

from nscraper import (
    InvalidHeadersError,
    NetworkError,
    RequestError,
    ScrapeOptions,
    UnsupportedContentTypeError,
)
from nscraper.scraper.http import HttpScraper


class DummyResponse:
    def __init__(self, text: str, *, raise_exc: Exception | None = None) -> None:
        self.text = text
        self._raise_exc = raise_exc
        self.status_code = 200
        self.headers = {"Content-Type": "text/html"}

    def raise_for_status(self) -> None:
        if self._raise_exc is not None:
            raise self._raise_exc


def make_options(**overrides):
    base = ScrapeOptions(
        url="https://example.com",
        headers={"Accept": "text/html"},
        cookies=None,
        output_path=None,
        transform=None,
    )
    return replace(base, **overrides)


def test_http_scraper_returns_raw_response(monkeypatch):
    response = DummyResponse("<html>Hello</html>")
    calls = {}

    def fake_get(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return response

    monkeypatch.setattr("niquests.get", fake_get)
    scraper = HttpScraper(make_options())

    result = scraper.scrape()

    assert result.content == "<html>Hello</html>"
    assert result.result.content_type == "text/html"
    assert result.network.response is response
    assert calls["url"] == "https://example.com"
    assert calls["kwargs"]["headers"] == {"Accept": "text/html"}


def test_http_scraper_forwards_cookies(monkeypatch):
    response = DummyResponse("<html>Hello</html>")
    calls = {}

    def fake_get(url, **kwargs):
        calls["kwargs"] = kwargs
        return response

    monkeypatch.setattr("niquests.get", fake_get)
    scraper = HttpScraper(make_options(cookies={"sessionid": "abc123"}))

    result = scraper.scrape()

    assert result.content == "<html>Hello</html>"
    assert calls["kwargs"]["cookies"] == {"sessionid": "abc123"}


def test_http_scraper_accepts_default_headers_string(monkeypatch):
    response = DummyResponse("<html>Hello</html>")
    calls = {}

    def fake_get(url, **kwargs):
        calls["kwargs"] = kwargs
        return response

    monkeypatch.setattr("niquests.get", fake_get)
    scraper = HttpScraper(make_options(headers="default"))

    result = scraper.scrape()

    assert result.content == "<html>Hello</html>"
    assert "User-Agent" in calls["kwargs"]["headers"]


def test_http_scraper_applies_basic_html_transform(monkeypatch):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("<script>x</script><div>Hello</div>"))
    scraper = HttpScraper(make_options(transform="basic"))

    result = scraper.scrape()
    assert "<div>Hello</div>" in result.content
    assert "<script>" not in result.content


def test_http_scraper_applies_fast_html_transform(monkeypatch):
    monkeypatch.setattr(
        "niquests.get",
        lambda *args, **kwargs: DummyResponse("<head><title>X</title></head><script>x</script><div>Hello</div>"),
    )
    scraper = HttpScraper(make_options(transform="fast"))

    result = scraper.scrape()
    assert "<div>Hello</div>" in result.content
    assert "<script>" not in result.content
    assert "<title>X</title>" in result.content


def test_http_scraper_pretty_formats_output(monkeypatch):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("<html><body><div>Hello</div></body></html>"))
    scraper = HttpScraper(make_options(pretty=True))

    result = scraper.scrape()
    assert "\n" in result.content
    assert "Hello" in result.content


def test_http_scraper_pretty_formats_json(monkeypatch):
    response = DummyResponse('{"ok":true}')
    response.headers = {"Content-Type": "application/json"}
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: response)
    scraper = HttpScraper(make_options(pretty=True))

    result = scraper.scrape()
    assert '\n  "ok": true\n' in result.content


def test_http_scraper_skips_html_transform_for_json(monkeypatch):
    response = DummyResponse('{"ok":true}')
    response.headers = {"Content-Type": "application/json"}
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: response)
    scraper = HttpScraper(make_options(transform="basic"))

    result = scraper.scrape()
    assert result.content == '{"ok":true}'


def test_http_scraper_rejects_plain_text(monkeypatch):
    response = DummyResponse("plain text body")
    response.headers = {"Content-Type": "text/plain"}
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: response)
    scraper = HttpScraper(make_options(pretty=True, transform="fast"))

    with pytest.raises(UnsupportedContentTypeError, match="unsupported content type"):
        scraper.scrape()


def test_http_scraper_writes_output(monkeypatch, tmp_path):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("Hello"))
    output = tmp_path / "page.html"
    scraper = HttpScraper(make_options(output_path=output))

    result = scraper.scrape()
    assert result.content == "Hello"
    assert result.result.output_path == output
    assert result.result.bytes_written == 5
    assert output.read_text(encoding="utf-8") == "Hello"


def test_http_scraper_accepts_string_output_path(monkeypatch, tmp_path):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("Hello"))
    output = tmp_path / "page.html"
    scraper = HttpScraper(make_options(output_path=str(output)))

    result = scraper.scrape()

    assert result.result.output_path == output
    assert output.read_text(encoding="utf-8") == "Hello"


def test_http_scraper_auto_output_uses_json_extension(monkeypatch, tmp_path):
    response = DummyResponse('{"ok":true}')
    response.headers = {"Content-Type": "application/json"}
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: response)
    output = tmp_path / ".nscraper" / "httpbin.org"
    scraper = HttpScraper(make_options(url="https://httpbin.org/get", output_path=output, auto_output=True))

    result = scraper.scrape()
    assert result.content == '{"ok":true}'
    assert result.result.output_path == tmp_path / ".nscraper" / "httpbin.org.json"
    assert result.result.bytes_written == len('{"ok":true}'.encode("utf-8"))
    assert (tmp_path / ".nscraper" / "httpbin.org.json").read_text(encoding="utf-8") == '{"ok":true}'


def test_http_scraper_debug_logs_timings(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("Hello"))
    output = tmp_path / "page.html"
    scraper = HttpScraper(make_options(output_path=output, debug=True))

    result = scraper.scrape()
    assert result.content == "Hello"

    captured = capsys.readouterr()
    assert "[nscraper] request_start" in captured.err
    assert "[nscraper] request_done" in captured.err
    assert "[nscraper] transform_done" not in captured.err
    assert "[nscraper] store_done" in captured.err
    assert "[nscraper] run_done" in captured.err
    assert "elapsed_ms=" in captured.err
    assert "status=200" in captured.err
    assert "response_bytes=5B" in captured.err


def test_http_scraper_logs_transform_when_specified(monkeypatch, capsys):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("<script>x</script><div>Hello</div>"))
    scraper = HttpScraper(make_options(transform="basic"))

    result = scraper.scrape()
    assert result.content

    captured = capsys.readouterr()
    assert "[nscraper] transform_done" in captured.err


def test_http_scraper_logs_pretty_as_separate_step(monkeypatch, capsys):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("<html><body><div>Hello</div></body></html>"))
    scraper = HttpScraper(make_options(transform="fast", pretty=True))

    result = scraper.scrape()
    assert result.content

    captured = capsys.readouterr()
    assert "[nscraper] transform_done" in captured.err
    assert "[nscraper] pretty_done" in captured.err


def test_http_scraper_rejects_missing_headers(monkeypatch):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("Hello"))
    scraper = HttpScraper(make_options(headers=None))

    with pytest.raises(InvalidHeadersError, match="headers are required"):
        scraper.scrape()


def test_http_scraper_maps_request_error(monkeypatch):
    class Boom(niquests.exceptions.HTTPError):
        pass

    def fake_get(*args, **kwargs):
        return DummyResponse("ignored", raise_exc=Boom("bad status"))

    monkeypatch.setattr("niquests.get", fake_get)
    scraper = HttpScraper(make_options())

    with pytest.raises(RequestError, match="request failed for"):
        scraper.scrape()


def test_http_scraper_maps_network_error(monkeypatch):
    class Boom(niquests.exceptions.RequestException):
        pass

    def fake_get(*args, **kwargs):
        raise Boom("network down")

    monkeypatch.setattr("niquests.get", fake_get)
    scraper = HttpScraper(make_options())

    with pytest.raises(NetworkError, match="network failure while fetching"):
        scraper.scrape()


def test_http_scraper_rejects_unsupported_content_type(monkeypatch):
    response = DummyResponse("plain text body")
    response.headers = {"Content-Type": "text/plain"}
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: response)
    scraper = HttpScraper(make_options())

    with pytest.raises(UnsupportedContentTypeError, match="unsupported content type: text/plain"):
        scraper.scrape()
