"""HTTP scraper implementation."""

from __future__ import annotations

import time

import niquests

from ..errors import (
    InvalidHeadersError,
    NetworkError,
    RequestError,
    UnsupportedContentTypeError,
)
from ..logging import debug_logger
from ..utils import classify_response_type, normalize_headers, validate_url
from .base import BaseScraper


class HttpScraper(BaseScraper):
    """Scraper implementation backed by niquests."""

    def send_request(self) -> str:
        logger = debug_logger(True)
        started_at = time.perf_counter()
        url = validate_url(self.options.url)
        headers = normalize_headers(self.options.headers) or {}
        if not headers:
            raise InvalidHeadersError("headers are required")
        kwargs: dict[str, object] = {"headers": headers, "timeout": self.options.timeout}
        if self.options.proxy:
            kwargs["proxies"] = {"http": self.options.proxy, "https": self.options.proxy}
        if self.options.cookies:
            kwargs["cookies"] = self.options.cookies
        logger.log("request_start", url=url, timeout_s=self.options.timeout)
        try:
            response = niquests.get(url, **kwargs)
            response.raise_for_status()
        except niquests.exceptions.HTTPError as exc:
            logger.log("request_failed", url=url, error_type=type(exc).__name__, elapsed_ms=logger.elapsed_ms(started_at))
            raise RequestError(f"request failed for {url}") from exc
        except niquests.exceptions.RequestException as exc:
            logger.log("request_failed", url=url, error_type=type(exc).__name__, elapsed_ms=logger.elapsed_ms(started_at))
            raise NetworkError(f"network failure while fetching {url}") from exc
        content_type = ""
        if hasattr(response, "headers") and response.headers:
            content_type = str(response.headers.get("Content-Type", ""))
        self.request_obj = getattr(response, "request", None)
        self.response_obj = response
        self.content_type = content_type
        self.response_type = classify_response_type(content_type)
        if not self.response_type.is_supported:
            logger.log(
                "request_failed",
                url=url,
                error_type="UnsupportedContentTypeError",
                content_type=content_type or "unknown",
                elapsed_ms=logger.elapsed_ms(started_at),
            )
            raise UnsupportedContentTypeError(
                f"unsupported content type: {content_type or 'unknown'}"
            )
        logger.log(
            "request_done",
            status=getattr(response, "status_code", "unknown"),
            response_bytes=len(response.text.encode("utf-8")),
            content_type=content_type,
            elapsed_ms=logger.elapsed_ms(started_at),
        )
        return response.text
