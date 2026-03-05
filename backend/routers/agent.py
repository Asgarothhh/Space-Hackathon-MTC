from __future__ import annotations

import logging
import tarfile
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Annotated, Literal, Optional

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException
)
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage

from agent.model import app

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])

MAX_ARCHIVE_SIZE_MB = 250


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


@router.post("/agent", response_model_exclude_none=True)
async def run_agent(
    # Общие поля
    user_message: Annotated[str, Form(...)],
    expected_load: Annotated[
        Literal["low", "medium", "high", "production"],
        Form(),
    ] = "medium",

    project_root: Annotated[
        Optional[str],
        Form(description="Путь к папке проекта на сервере (взаимоисключающе с archive_file)")
    ] = None,

    archive_file: Annotated[
        Optional[UploadFile],
        File(description="Архив проекта: .zip, .tar, .tar.gz, .tgz, .tar.bz2, .tar.xz, .7z, .rar (взаимоисключающе с project_root)")
    ] = None,
) -> JSONResponse:
    """
    Универсальный роутер для запуска агента.

    Поддерживаемые режимы:
    • project_root → работа с существующей папкой на сервере
    • archive_file → временная распаковка архива (zip, tar, tar.gz, tgz, tar.bz2, tar.xz, 7z, rar)
    """

    # Пользователь может задать вопрос без передачи проекта.
    # Но нельзя передавать и project_root, и archive_file одновременно.
    if project_root is not None and archive_file is not None:
        raise HTTPException(
            status_code=422,
            detail="Параметры project_root и archive_file взаимоисключающие"
        )

    project_root_path: str | None = None
    temp_dir: tempfile.TemporaryDirectory | None = None
    cleanup_needed = False

    try:
        if project_root is not None:
            p = Path(project_root).resolve()
            if not p.is_dir() or not p.exists():
                raise HTTPException(
                    status_code=400,
                    detail="Указанный project_root не существует или не является директорией"
                )
            project_root_path = str(p)

        elif archive_file is not None:
            suffix = _archive_suffix(archive_file.filename or "")
            if not suffix:
                raise HTTPException(
                    400,
                    detail=f"Неподдерживаемый формат. Разрешены: {', '.join(ALLOWED_ARCHIVE_SUFFIXES)}"
                )

            if archive_file.size and archive_file.size > MAX_ARCHIVE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"Файл слишком большой (максимум {MAX_ARCHIVE_SIZE_MB} МБ)"
                )

            temp_dir = tempfile.TemporaryDirectory(prefix="iaas-agent-upload-")
            temp_path = Path(temp_dir.name)
            archive_path = temp_path / f"upload-{uuid.uuid4()}{suffix}"

            # Сохраняем потоково
            with archive_path.open("wb") as f_out:
                while chunk := await archive_file.read(1024 * 1024):
                    if not chunk:
                        break
                    f_out.write(chunk)

            extract_dir = temp_path / "extracted"
            extract_dir.mkdir(exist_ok=True)

            try:
                if suffix == ".zip":
                    _extract_zip(archive_path, extract_dir)
                elif suffix == ".7z":
                    _extract_7z(archive_path, extract_dir)
                elif suffix == ".rar":
                    _extract_rar(archive_path, extract_dir)
                else:
                    _extract_tar(archive_path, extract_dir)
            except HTTPException:
                raise
            except zipfile.BadZipFile:
                raise HTTPException(400, "Повреждённый ZIP-архив")
            except tarfile.TarError as e:
                raise HTTPException(400, f"Повреждённый или неподдерживаемый tar-архив: {e}")
            except ValueError as e:
                raise HTTPException(400, str(e))
            except Exception as e:
                logger.exception("Ошибка распаковки архива")
                raise HTTPException(500, f"Не удалось распаковать архив: {str(e)}")

            # Определяем корень проекта
            contents = list(extract_dir.iterdir())
            if len(contents) == 1 and contents[0].is_dir():
                project_root_path = str(contents[0].resolve())
            else:
                project_root_path = str(extract_dir.resolve())

            cleanup_needed = True

        state = {
            "messages": [HumanMessage(content=user_message)],
            "project_root": project_root_path,
            "final_specs": None,
            "expected_load": expected_load,
        }

        try:
            result = app.invoke(state)
        except Exception as exc:
            logger.exception("Ошибка выполнения LangGraph")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка выполнения агента: {str(exc)}"
            ) from exc

        # Формируем ответ
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else {}
        response_text = getattr(last_message, "content", "") if hasattr(last_message, "content") else str(last_message)

        docker_created = any(
            "Dockerfile" in getattr(m, "content", "")
            for m in messages
        )

        return JSONResponse({
            "response": response_text.strip(),
            "specs": result.get("final_specs"),
            "docker_created": docker_created,
            "project_root_used": project_root_path,
        })

    finally:
        if cleanup_needed and temp_dir is not None:
            try:
                temp_dir.cleanup()
            except Exception:
                logger.warning("Не удалось удалить временную папку", exc_info=True)


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "graph_loaded": app is not None
    }
