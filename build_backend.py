"""Minimal PEP 517 backend for offline editable and wheel installs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import csv
import hashlib
import io
import os
import tarfile
import tempfile
import zipfile

NAME = "nscraper"
VERSION = "0.1.0"
DIST_INFO = f"{NAME}-{VERSION}.dist-info"
SUMMARY = "A small importable Python module."
README_PATH = Path(__file__).resolve().parent / "README.md"


@dataclass(frozen=True)
class FileRecord:
    path: str
    data: bytes


def _normalize(path: str) -> str:
    return path.replace(os.sep, "/")


def _metadata_text() -> str:
    description = README_PATH.read_text(encoding="utf-8")
    return (
        "Metadata-Version: 2.1\n"
        f"Name: {NAME}\n"
        f"Version: {VERSION}\n"
        f"Summary: {SUMMARY}\n"
        "License: MIT\n"
        "Requires-Dist: niquests==3.18.4\n"
        "Requires-Dist: justhtml==1.14.0\n"
        "Description-Content-Type: text/markdown\n"
        "\n"
        f"{description}"
    )


def _wheel_metadata() -> list[FileRecord]:
    wheel = (
        "Wheel-Version: 1.0\n"
        "Generator: nscraper.build_backend\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    )
    meta = _metadata_text()
    entry_points = "[console_scripts]\nnscraper = nscraper.__main__:main\n"
    return [
        FileRecord(f"{DIST_INFO}/WHEEL", wheel.encode()),
        FileRecord(f"{DIST_INFO}/METADATA", meta.encode()),
        FileRecord(f"{DIST_INFO}/entry_points.txt", entry_points.encode()),
    ]


def _package_files() -> list[FileRecord]:
    root = Path(__file__).resolve().parent / "src" / NAME
    records: list[FileRecord] = []
    for path in root.rglob("*.py"):
        rel = _normalize(str(path.relative_to(root.parent)))
        records.append(FileRecord(rel, path.read_bytes()))
    return records


def _sdist_files(root: Path) -> list[tuple[Path, str]]:
    members = ["build_backend.py", "pyproject.toml", "README.md", "LICENSE"]
    files = [(root / member, f"{NAME}-{VERSION}/{member}") for member in members]
    for base in ("src", "tests"):
        for path in (root / base).rglob("*"):
            if path.is_dir() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            arcname = f"{NAME}-{VERSION}/{path.relative_to(root)}"
            files.append((path, arcname))
    return files


def _build_wheel_dir(wheel_directory: str, editable: bool = False) -> str:
    out = Path(wheel_directory)
    out.mkdir(parents=True, exist_ok=True)
    wheel_name = f"{NAME}-{VERSION}-py3-none-any.whl"
    wheel_path = out / wheel_name
    records = _wheel_metadata()
    if editable:
        pth = f"{NAME}.pth"
        src_dir = (Path(__file__).resolve().parent / "src").as_posix()
        records.append(FileRecord(pth, f"{src_dir}\n".encode()))
    else:
        records.extend(_package_files())
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for record in records:
                zf.writestr(record.path, record.data)
            dist_info = tmp / DIST_INFO
            dist_info.mkdir()
            record_file = dist_info / "RECORD"
            rows = []
            for record in records:
                digest = base64.urlsafe_b64encode(hashlib.sha256(record.data).digest()).rstrip(b"=").decode()
                rows.append((record.path, f"sha256={digest}", str(len(record.data))))
            rows.append((f"{DIST_INFO}/RECORD", "", ""))
            with record_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            zf.write(record_file, f"{DIST_INFO}/RECORD")
    return wheel_name


def get_requires_for_build_wheel(config_settings=None):
    return []


def get_requires_for_build_editable(config_settings=None):
    return []


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    dist = Path(metadata_directory) / DIST_INFO
    dist.mkdir(parents=True, exist_ok=True)
    for record in _wheel_metadata():
        if record.path.endswith(("WHEEL", "METADATA", "entry_points.txt")):
            (dist / Path(record.path).name).write_bytes(record.data)
    return DIST_INFO


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    return _build_wheel_dir(wheel_directory, editable=False)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    return _build_wheel_dir(wheel_directory, editable=True)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def build_sdist(sdist_directory, config_settings=None):
    out = Path(sdist_directory)
    out.mkdir(parents=True, exist_ok=True)
    sdist_name = f"{NAME}-{VERSION}.tar.gz"
    sdist_path = out / sdist_name
    root = Path(__file__).resolve().parent
    pkg_info = _metadata_text().encode("utf-8")
    with tarfile.open(sdist_path, "w:gz") as tf:
        for path, arcname in _sdist_files(root):
            tf.add(path, arcname=arcname)
        info = tarfile.TarInfo(name=f"{NAME}-{VERSION}/PKG-INFO")
        info.size = len(pkg_info)
        tf.addfile(info, fileobj=io.BytesIO(pkg_info))
    return sdist_name
