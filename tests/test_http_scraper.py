from dataclasses import replace
import niquests
import pytest

from nscraper import InvalidHeadersError, NetworkError, RequestError, ScrapeOptions
from nscraper.scraper.http import HttpScraper


class DummyResponse:
    def __init__(self, text: str, *, raise_exc: Exception | None = None) -> None:
        self.text = text
        self._raise_exc = raise_exc

    def raise_for_status(self) -> None:
        if self._raise_exc is not None:
            raise self._raise_exc


def make_options(**overrides):
    base = ScrapeOptions(
        url="https://example.com",
        headers={"Accept": "text/html"},
        cookies=None,
        output_path=None,
        transform="raw",
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

    assert scraper.scrape() == "<html>Hello</html>"
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

    assert scraper.scrape() == "<html>Hello</html>"
    assert calls["kwargs"]["cookies"] == {"sessionid": "abc123"}


def test_http_scraper_applies_basic_html_transform(monkeypatch):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("<script>x</script><div>Hello</div>"))
    scraper = HttpScraper(make_options(transform="basic_html"))

    cleaned = scraper.scrape()
    assert "<div>Hello</div>" in cleaned
    assert "<script>" not in cleaned


def test_http_scraper_writes_output(monkeypatch, tmp_path):
    monkeypatch.setattr("niquests.get", lambda *args, **kwargs: DummyResponse("Hello"))
    output = tmp_path / "page.html"
    scraper = HttpScraper(make_options(output_path=output))

    assert scraper.scrape() == "Hello"
    assert output.read_text(encoding="utf-8") == "Hello"


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
