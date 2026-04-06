"""Base scraper contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import time

from ..models import NetworkResult, ResultData, ScrapeOptions, ScrapeResult
from ..logging import debug_logger
from ..utils import (
    apply_pretty_format,
    auto_output_path,
    basic_html_transform,
    classify_response_type,
    fast_html_transform,
    ResponseType,
    write_output,
)


class BaseScraper(ABC):
    """Base scraper contract."""

    def __init__(self, options: ScrapeOptions) -> None:
        self.options = options
        self.content_type: str | None = None
        self.response_type = ResponseType(kind="html")
        self.written_output_path: Path | None = None
        self.request_obj: object | None = None
        self.response_obj: object | None = None
        self.bytes_written: int = 0

    @abstractmethod
    def send_request(self) -> str:
        """Send the underlying request and return raw content."""

    def transform(self, content: str) -> str:
        logger = debug_logger(True)
        if self.options.transform is None:
            return content
        started_at = time.perf_counter()
        input_bytes = len(content.encode("utf-8"))
        if self.options.transform == "basic" and self.response_type.is_html:
            content = basic_html_transform(content)
        elif self.options.transform == "fast" and self.response_type.is_html:
            content = fast_html_transform(content)
        output_bytes = len(content.encode("utf-8"))
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.log(
            "transform_done",
            mode=self.options.transform,
            input_bytes=input_bytes,
            output_bytes=output_bytes,
            removed_bytes=max(input_bytes - output_bytes, 0),
            elapsed_ms=f"{elapsed_ms:.2f}",
        )
        return content

    def pretty(self, content: str) -> str:
        logger = debug_logger(True)
        if not self.options.pretty or not self.response_type.supports_pretty:
            return content
        started_at = time.perf_counter()
        input_bytes = len(content.encode("utf-8"))
        content = apply_pretty_format(content, self.response_type)
        output_bytes = len(content.encode("utf-8"))
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.log(
            "pretty_done",
            input_bytes=input_bytes,
            output_bytes=output_bytes,
            added_bytes=max(output_bytes - input_bytes, 0),
            elapsed_ms=f"{elapsed_ms:.2f}",
        )
        return content

    def store(self, content: str) -> None:
        self.bytes_written = 0
        if self.options.output_path:
            logger = debug_logger(True)
            started_at = time.perf_counter()
            output_path = self._resolve_output_path()
            created_parent = write_output(output_path, content)
            self.written_output_path = output_path
            self.bytes_written = len(content.encode("utf-8"))
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            logger.log(
                "store_done",
                path=output_path,
                bytes=self.bytes_written,
                created_parent=created_parent,
                elapsed_ms=f"{elapsed_ms:.2f}",
            )

    def scrape(self) -> ScrapeResult:
        logger = debug_logger(True)
        started_at = time.perf_counter()
        content = self.send_request()
        content = self.transform(content)
        content = self.pretty(content)
        self.store(content)
        logger.log("run_done", scraper=self.__class__.__name__, total_ms=logger.elapsed_ms(started_at))
        return ScrapeResult(
            network=NetworkResult(request=self.request_obj, response=self.response_obj),
            result=ResultData(
                output_path=self.written_output_path,
                bytes_written=self.bytes_written,
                content_type=self.content_type or "",
            ),
            content=content,
        )

    def _resolve_output_path(self) -> Path:
        if not self.options.output_path:
            raise ValueError("output path is required")
        output_path = Path(self.options.output_path)
        if not self.options.auto_output:
            return output_path
        return auto_output_path(output_path, self.response_type)
