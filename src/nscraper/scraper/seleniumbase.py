"""SeleniumBase scraper implementation placeholder."""

from __future__ import annotations

import time
from ..errors import NscraperError
from ..logging import debug_logger
from ..utils import classify_response_type
from .base import BaseScraper


class SeleniumBaseScraper(BaseScraper):
    """Scraper implementation backed by SeleniumBase."""

    def send_request(self) -> str:
        logger = debug_logger(True)
        started_at = time.perf_counter()
        try:
            sb_class = self._import_seleniumbase()
        except NscraperError:
            logger.log("request_failed", error_type="MissingDependencyError", elapsed_ms=logger.elapsed_ms(started_at))
            raise

        logger.log("request_start", url=self.options.url, timeout_s=self.options.timeout)
        try:
            with sb_class() as sb:
                self._open_page(sb)
                content = self._read_page_source(sb)
        except Exception as exc:  # pragma: no cover - backend-specific failures
            logger.log(
                "request_failed",
                url=self.options.url,
                error_type=type(exc).__name__,
                elapsed_ms=logger.elapsed_ms(started_at),
            )
            raise NscraperError(f"seleniumbase failure while fetching {self.options.url}") from exc

        self.content_type = "text/html"
        self.response_type = classify_response_type(self.content_type)
        self.request_obj = None
        self.response_obj = None
        logger.log(
            "request_done",
            status="ok",
            response_bytes=len(content.encode("utf-8")),
            content_type=self.content_type,
            elapsed_ms=logger.elapsed_ms(started_at),
        )
        return content

    def _import_seleniumbase(self):
        try:
            from seleniumbase import SB
        except ImportError as exc:
            raise NscraperError(
                "seleniumbase engine requires the seleniumbase package; install it to use --engine seleniumbase"
            ) from exc
        return SB

    def _open_page(self, sb: object) -> None:
        open_page = getattr(sb, "open", None)
        if open_page is None:
            raise NscraperError("seleniumbase browser object does not support open()")
        open_page(self.options.url)

    def _read_page_source(self, sb: object) -> str:
        get_page_source = getattr(sb, "get_page_source", None)
        if get_page_source is None:
            raise NscraperError("seleniumbase browser object does not support get_page_source()")
        content = get_page_source()
        if not isinstance(content, str):
            raise NscraperError("seleniumbase page source must be text")
        return content
