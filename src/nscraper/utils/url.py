"""URL validation helpers."""

from __future__ import annotations

from urllib.parse import urlparse

from ..errors import InvalidUrlError


def validate_url(url: str) -> str:
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    if (
        not cleaned
        or parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or " " in cleaned
        or not parsed.hostname
    ):
        raise InvalidUrlError("invalid url")
    return cleaned
