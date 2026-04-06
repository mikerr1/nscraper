"""Response content classification helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .html import pretty_html


@dataclass(frozen=True, slots=True)
class ResponseType:
    """Normalized response content classification."""

    kind: str
    content_type: str = ""

    @property
    def is_html(self) -> bool:
        return self.kind == "html"

    @property
    def is_json(self) -> bool:
        return self.kind == "json"

    @property
    def supports_pretty(self) -> bool:
        return self.kind in {"html", "json"}

    @property
    def is_supported(self) -> bool:
        return self.kind in {"html", "json"}


class ResponseTypeClassifier:
    """Classify HTTP response content types into scraper-friendly groups."""

    def classify(self, content_type: str | None) -> ResponseType:
        lowered = (content_type or "").lower()
        if "json" in lowered:
            return ResponseType(kind="json", content_type=lowered)
        if "html" in lowered or "xhtml" in lowered:
            return ResponseType(kind="html", content_type=lowered)
        if "xml" in lowered:
            return ResponseType(kind="xml", content_type=lowered)
        if lowered.startswith("text/"):
            return ResponseType(kind="text", content_type=lowered)
        if lowered:
            return ResponseType(kind="binary", content_type=lowered)
        return ResponseType(kind="html", content_type="")


def pretty_json(content: str) -> str:
    payload = json.loads(content)
    return json.dumps(payload, indent=2, ensure_ascii=False)


def response_type_classifier() -> ResponseTypeClassifier:
    return ResponseTypeClassifier()


def classify_response_type(content_type: str | None) -> ResponseType:
    return response_type_classifier().classify(content_type)


def apply_pretty_format(content: str, response_type: ResponseType) -> str:
    if response_type.is_json:
        return pretty_json(content)
    return pretty_html(content)


def auto_output_path(path_stem: Path, response_type: ResponseType) -> Path:
    suffix = ".json" if response_type.is_json else ".html"
    return path_stem.parent / f"{path_stem.name}{suffix}"
