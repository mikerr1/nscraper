"""Core library functions."""

from __future__ import annotations

from .models import ScrapeOptions
from .scraper import BaseScraper, HttpScraper, SeleniumBaseScraper


def hello(name: str = "world") -> str:
    """Return a friendly greeting."""
    cleaned = name.strip() or "world"
    return f"Hello, {cleaned}!"


def get_scraper(options: ScrapeOptions) -> BaseScraper:
    if options.engine == "seleniumbase":
        return SeleniumBaseScraper(options)
    return HttpScraper(options)
