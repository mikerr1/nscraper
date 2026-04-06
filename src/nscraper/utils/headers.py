"""Header-related helpers."""

from __future__ import annotations

import json
from typing import Literal

from ..errors import InvalidHeadersError

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}

HeaderInput = dict[str, str] | Literal["default"] | None


def parse_headers(raw_headers: str | None) -> dict[str, str]:
    if raw_headers is None or not raw_headers.strip():
        raise InvalidHeadersError("headers are required")
    try:
        value = json.loads(raw_headers)
    except json.JSONDecodeError as exc:
        raise InvalidHeadersError("headers must be valid JSON") from exc
    if not isinstance(value, dict) or not value:
        raise InvalidHeadersError("headers must be a non-empty object")
    headers: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise InvalidHeadersError("header names must be non-empty strings")
        if not isinstance(item, str):
            raise InvalidHeadersError("header values must be strings")
        headers[key.strip()] = item
    return headers


def normalize_headers(headers: HeaderInput) -> dict[str, str] | None:
    if headers == "default":
        return DEFAULT_HEADERS
    return headers
