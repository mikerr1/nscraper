"""Cookie file helpers."""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import InvalidCookiesError


def load_cookies_file(cookies_file: Path | str | None) -> dict[str, str] | None:
    if cookies_file is None:
        return None
    path = Path(cookies_file)
    if not path.exists():
        raise InvalidCookiesError(f"cookies file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InvalidCookiesError("cookies file must contain valid JSON") from exc
    if not isinstance(payload, dict) or not payload:
        raise InvalidCookiesError("cookies file must contain a non-empty JSON object")
    cookies: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not key.strip():
            raise InvalidCookiesError("cookie names must be non-empty strings")
        if not isinstance(value, str):
            raise InvalidCookiesError("cookie values must be strings")
        cookies[key.strip()] = value
    return cookies
