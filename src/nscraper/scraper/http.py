"""HTTP scraper implementation."""

from __future__ import annotations

import niquests

from ..errors import InvalidHeadersError, NetworkError, RequestError
from ..utils import validate_url
from .base import BaseScraper


class HttpScraper(BaseScraper):
    """Scraper implementation backed by niquests."""

    def send_request(self) -> str:
        url = validate_url(self.options.url)
        headers = self.options.headers or {}
        if not headers:
            raise InvalidHeadersError("headers are required")
        kwargs: dict[str, object] = {"headers": headers, "timeout": self.options.timeout}
        if self.options.proxy:
            kwargs["proxies"] = {"http": self.options.proxy, "https": self.options.proxy}
        if self.options.cookies:
            kwargs["cookies"] = self.options.cookies
        try:
            response = niquests.get(url, **kwargs)
            response.raise_for_status()
        except niquests.exceptions.HTTPError as exc:
            raise RequestError(f"request failed for {url}") from exc
        except niquests.exceptions.RequestException as exc:
            raise NetworkError(f"network failure while fetching {url}") from exc
        return response.text
