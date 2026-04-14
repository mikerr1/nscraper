from dataclasses import replace
import builtins
from html.parser import HTMLParser
import os
import sys
import types

import pytest

from nscraper import NscraperError, ScrapeOptions
from nscraper.scraper import get_scraper
from nscraper.scraper.seleniumbase import SeleniumBaseScraper


class FakeSB:
    instances = []

    def __init__(self) -> None:
        self.opened_urls: list[str] = []
        self.closed = False
        self.page_source = "<html><body><div>Hello</div></body></html>"
        FakeSB.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True
        return False

    def open(self, url: str) -> None:
        self.opened_urls.append(url)

    def get_page_source(self) -> str:
        return self.page_source


class H1Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture_depth = 0
        self._capture_tag: str | None = None
        self._buffer: list[str] = []
        self.h1_texts: list[str] = []
        self.h2_texts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        lowered = tag.lower()
        if lowered in {"h1", "h2"}:
            self._capture_depth += 1
            self._capture_tag = lowered

    def handle_endtag(self, tag: str):
        lowered = tag.lower()
        if lowered not in {"h1", "h2"} or self._capture_depth <= 0:
            return
        self._capture_depth -= 1
        if self._capture_depth == 0:
            text = "".join(self._buffer).strip()
            if text:
                if self._capture_tag == "h1":
                    self.h1_texts.append(text)
                elif self._capture_tag == "h2":
                    self.h2_texts.append(text)
            self._buffer.clear()
            self._capture_tag = None

    def handle_data(self, data: str):
        if self._capture_depth > 0:
            self._buffer.append(data)


def make_options(**overrides):
    base = ScrapeOptions(
        url="https://example.com",
        engine="seleniumbase",
        headers={"Accept": "text/html"},
        cookies=None,
        output_path=None,
        transform=None,
    )
    return replace(base, **overrides)


def test_get_scraper_returns_seleniumbase_scraper():
    scraper = get_scraper(make_options())

    assert isinstance(scraper, SeleniumBaseScraper)


def test_seleniumbase_scraper_returns_page_source(monkeypatch):
    monkeypatch.setitem(sys.modules, "seleniumbase", types.SimpleNamespace(SB=FakeSB))
    FakeSB.instances.clear()
    scraper = SeleniumBaseScraper(make_options())

    result = scraper.scrape()

    assert result.content == "<html><body><div>Hello</div></body></html>"
    assert result.result.content_type == "text/html"
    assert FakeSB.instances[0].opened_urls == ["https://example.com"]
    assert FakeSB.instances[0].closed is True


def test_seleniumbase_scraper_applies_transform_and_pretty(monkeypatch):
    monkeypatch.setitem(sys.modules, "seleniumbase", types.SimpleNamespace(SB=FakeSB))
    FakeSB.instances.clear()

    def fake_source(self):
        return "<html><body><script>x</script><div>Hello</div></body></html>"

    monkeypatch.setattr(FakeSB, "get_page_source", fake_source, raising=True)
    scraper = SeleniumBaseScraper(make_options(transform="basic", pretty=True))

    result = scraper.scrape()

    assert "<script>" not in result.content
    assert "\n" in result.content
    assert "Hello" in result.content


def test_seleniumbase_scraper_writes_output(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "seleniumbase", types.SimpleNamespace(SB=FakeSB))
    FakeSB.instances.clear()
    output = tmp_path / "page.html"
    scraper = SeleniumBaseScraper(make_options(output_path=output))

    result = scraper.scrape()

    assert result.result.output_path == output
    assert output.read_text(encoding="utf-8") == result.content


def test_seleniumbase_scraper_missing_dependency(monkeypatch):
    monkeypatch.delitem(sys.modules, "seleniumbase", raising=False)
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "seleniumbase":
            raise ImportError("No module named seleniumbase")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    scraper = SeleniumBaseScraper(make_options())

    with pytest.raises(NscraperError, match="requires the seleniumbase package"):
        scraper.scrape()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("NSCRAPER_RUN_INTEGRATION"),
    reason="requires NSCRAPER_RUN_INTEGRATION=1 and network access",
)
def test_seleniumbase_scraper_opens_kompas():
    scraper = SeleniumBaseScraper(
        make_options(
            url="http://detik.com",
            headers="default",
            timeout=10.0,
        )
    )

    result = scraper.scrape()

    assert result.content
    assert "<html" in result.content.lower()
    parser = H1Collector()
    parser.feed(result.content)
    h1_texts = parser.h1_texts
    h2_texts = parser.h2_texts
    for h1_text in h1_texts:
        print(f"h1={h1_text}")
    for h2_text in h2_texts:
        print(f"h2={h2_text}")
    assert h1_texts
