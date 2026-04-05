"""Data models for nscraper operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Engine = Literal["http", "seleniumbase"]
Transform = Literal["raw", "basic_html"]


@dataclass(frozen=True, slots=True)
class ScrapeOptions:
    """Normalized scrape configuration."""

    url: str
    engine: Engine = "http"
    proxy: str | None = None
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    timeout: float = 3.0
    output_path: Path | None = None
    transform: Transform = "raw"
