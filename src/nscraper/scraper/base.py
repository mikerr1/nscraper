"""Base scraper contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ScrapeOptions
from ..utils import basic_html_transform, write_output


class BaseScraper(ABC):
    """Base scraper contract."""

    def __init__(self, options: ScrapeOptions) -> None:
        self.options = options

    @abstractmethod
    def send_request(self) -> str:
        """Send the underlying request and return raw content."""

    def transform(self, content: str) -> str:
        if self.options.transform == "basic_html":
            return basic_html_transform(content)
        return content

    def store(self, content: str) -> None:
        if self.options.output_path:
            write_output(self.options.output_path, content)

    def scrape(self) -> str:
        content = self.send_request()
        content = self.transform(content)
        self.store(content)
        return content
