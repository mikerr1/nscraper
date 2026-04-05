"""Reusable utility functions for nscraper."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from justhtml import JustHTML

from .errors import InvalidCookiesError, InvalidHeadersError, InvalidUrlError

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}

BASIC_HTML_CLEANUP_SELECTORS = (
    "script",
    "style",
    "noscript",
    "iframe",
    "source",
    "svg",
    "template",
    "[aria-hidden='true']",
    "[hidden]",
    ".ads",
    ".advertisement",
    ".banner",
    ".social-share",
    ".newsletter",
)

_ARIA_HIDDEN_RE = re.compile(
    r"<(?P<tag>[a-zA-Z][\w:-]*)(?=[^>]*\baria-hidden=(['\"])true\2)[^>]*>.*?</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
_HIDDEN_RE = re.compile(
    r"<(?P<tag>[a-zA-Z][\w:-]*)(?=[^>]*\bhidden(?:\s|>|=))[^>]*>.*?</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)


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


def basic_html_transform(content: str) -> str:
    cleaned_input = _ARIA_HIDDEN_RE.sub("", content)
    cleaned_input = _HIDDEN_RE.sub("", cleaned_input)
    doc = JustHTML(cleaned_input, fragment=False)
    for selector in BASIC_HTML_CLEANUP_SELECTORS:
        for node in doc.query(selector):
            if node.parent:
                node.parent.remove_child(node)
    for head in doc.query("head"):
        while head.has_child_nodes():
            head.remove_child(head.children[0])
    return doc.to_html(pretty=True)


def write_output(output_path: Path, content: str) -> None:
    output_path.write_text(content, encoding="utf-8")
