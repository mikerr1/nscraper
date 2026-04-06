"""Scraper implementations and engine selection."""

from ..models import ScrapeOptions
from .base import BaseScraper
from .http import HttpScraper
from .seleniumbase import SeleniumBaseScraper


def get_scraper(options: ScrapeOptions) -> BaseScraper:
    if options.engine == "seleniumbase":
        return SeleniumBaseScraper(options)
    return HttpScraper(options)


__all__ = ["BaseScraper", "HttpScraper", "SeleniumBaseScraper", "get_scraper"]
