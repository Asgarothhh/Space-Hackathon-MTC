from pathlib import Path
from typing import Annotated, Literal, Optional
import tarfile
import tempfile
import uuid
import zipfile
from fastapi import HTTPException


ALLOWED_ARCHIVE_SUFFIXES = (
    ".zip", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz",
    ".tar", ".7z", ".rar",
)


def _archive_suffix(filename: str) -> str | None:
    """Возвращает подходящий суффикс из ALLOWED_ARCHIVE_SUFFIXES или None."""
    if not filename:
        return None
    lower = filename.lower()
    for suffix in ALLOWED_ARCHIVE_SUFFIXES:
        if lower.endswith(suffix):
            return suffix
    return None


def _extract_zip(archive_path: Path, extract_dir: Path) -> None:
    with zipfile.ZipFile(archive_path, "r") as zf:
        for member in zf.namelist():
            if member.startswith(("/", "\\")) or ".." in member:
                raise ValueError("Path traversal attempt detected")
        zf.extractall(extract_dir)


def _extract_tar(archive_path: Path, extract_dir: Path) -> None:
    with tarfile.open(archive_path, "r:*") as tf:
        for member in tf.getmembers():
            if member.name.startswith(("/", "\\")) or ".." in member.name:
                raise ValueError("Path traversal attempt detected")
        tf.extractall(extract_dir)


def _extract_7z(archive_path: Path, extract_dir: Path) -> None:
    try:
        import py7zr
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Поддержка 7z недоступна: установите пакет py7zr (pip install py7zr)"
        ) from None
    with py7zr.SevenZipFile(archive_path, "r") as zf:
        for name in zf.getnames():
            if name.startswith(("/", "\\")) or ".." in name:
                raise ValueError("Path traversal attempt detected")
        zf.extractall(path=extract_dir)


def _extract_rar(archive_path: Path, extract_dir: Path) -> None:
    try:
        import rarfile
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Поддержка RAR недоступна: установите пакет rarfile (pip install rarfile). Для распаковки нужен UnRAR в PATH."
        ) from None
    try:
        with rarfile.RarFile(archive_path, "r") as rf:
            for name in rf.namelist():
                if name.startswith(("/", "\\")) or ".." in name:
                    raise ValueError("Path traversal attempt detected")
            rf.extractall(path=extract_dir)
    except rarfile.NeedFirstVolume:
        raise HTTPException(400, "Многотомный RAR не поддерживается")
    except rarfile.BadRarFile as e:
        raise HTTPException(400, f"Повреждённый или неподдерживаемый RAR-архив: {e}")

