"""Data models for nscraper operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from niquests import PreparedRequest, Response

from .utils.headers import HeaderInput

Engine = Literal["http", "seleniumbase"]
Transform = Literal["raw", "basic", "fast"]
OutputPathInput = Path | str | None


@dataclass(frozen=True, slots=True)
class ScrapeOptions:
    """Normalized scrape configuration."""

    url: str
    engine: Engine = "http"
    proxy: str | None = None
    headers: HeaderInput = None
    cookies: dict[str, str] | None = None
    timeout: float = 3.0
    output_path: OutputPathInput = None
    auto_output: bool = False
    transform: Transform | None = None
    pretty: bool = False
    debug: bool = False


@dataclass(frozen=True, slots=True)
class NetworkResult:
    """Captured request/response transport objects."""

    request: PreparedRequest | None = None
    response: Response | None = None


@dataclass(frozen=True, slots=True)
class ResultData:
    """Persisted output metadata."""

    output_path: Path | None = None
    bytes_written: int = 0
    content_type: str = ""


@dataclass(frozen=True, slots=True)
class ScrapeResult:
    """Structured scrape result for library callers."""

    network: NetworkResult
    result: ResultData
    content: str
