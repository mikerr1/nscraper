"""Minimal runtime logging helpers."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

BYTE_FIELD_SUFFIXES = ("bytes",)


@dataclass(frozen=True, slots=True)
class DebugLogger:
    """Write structured runtime events to stderr when enabled."""

    enabled: bool = False

    def log(self, event: str, **fields: object) -> None:
        if not self.enabled:
            return
        pairs = [f"{key}={self._format_field(key, value)}" for key, value in fields.items()]
        suffix = f" {' '.join(pairs)}" if pairs else ""
        print(f"[nscraper] {event}{suffix}", file=sys.stderr)

    def elapsed_ms(self, started_at: float) -> str:
        from time import perf_counter

        elapsed = (perf_counter() - started_at) * 1000
        return f"{elapsed:.2f}"

    def share_of_total(self, elapsed_ms: float, total_ms: float) -> str:
        if total_ms <= 0:
            return "0.0%"
        return f"{(elapsed_ms / total_ms) * 100:.1f}%"

    def _serialize(self, value: object) -> str:
        if isinstance(value, Path):
            return str(value)
        return str(value)

    def _format_field(self, key: str, value: object) -> str:
        if isinstance(value, int) and key.endswith(BYTE_FIELD_SUFFIXES):
            return self._humanize_bytes(value)
        return self._serialize(value)

    def _humanize_bytes(self, value: int) -> str:
        units = ("B", "KB", "MB", "GB", "TB")
        size = float(value)
        unit = units[0]
        for unit in units:
            if size < 1024 or unit == units[-1]:
                break
            size /= 1024
        if unit == "B":
            return f"{int(size)}{unit}"
        return f"{size:.2f}{unit}"


def debug_logger(enabled: bool) -> DebugLogger:
    return DebugLogger(enabled=enabled)
