"""Output file helpers."""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import fcntl


def write_output(output_path: Path, content: str) -> bool:
    created_parent = not output_path.parent.exists()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with _output_lock(output_path):
        temp_path = _temp_output_path(output_path)
        temp_path.write_text(content, encoding="utf-8")
        os.replace(temp_path, output_path)
    return created_parent


@contextmanager
def _output_lock(output_path: Path):
    lock_path = output_path.with_name(f"{output_path.name}.lock")
    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _temp_output_path(output_path: Path) -> Path:
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
        text=True,
    )
    os.close(fd)
    return Path(temp_name)
