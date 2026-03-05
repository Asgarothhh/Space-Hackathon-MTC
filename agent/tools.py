"""Инструменты работы с файлами: чтение, листинг, поиск в подпапках, редактирование."""
import os
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool
from agent.utils import resolve_abs_path
from langchain_core.tools import tool
from typing import Dict, Any
import json


def _skip_dir(name: str) -> bool:
    return name.startswith(".") or name == "__pycache__" or name == "node_modules" or name == ".git"


@tool
def read_file(filename: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """Читает файл проекта. Критично для анализа зависимостей (requirements.txt, package.json, Dockerfile и т.д.)."""
    full_path = resolve_abs_path(filename)
    try:
        content = full_path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        content = "(бинарный или не UTF-8 файл)"
    total_lines = len(content.splitlines())
    return {"file_path": str(full_path), "content": content, "total_lines": total_lines}


@tool
def list_files(path: str, recursive: bool = False, pattern: str = "*") -> Dict[str, Any]:
    """Список файлов проекта. Используй для анализа структуры перед генерацией Docker.
    Рекомендуется recursive=True для полного проекта."""
    full_path = resolve_abs_path(path)
    all_entries: List[Dict[str, Any]] = []
    if not recursive:
        for item in sorted(full_path.iterdir(), key=lambda x: x.name.lower()):
            if _skip_dir(item.name):
                continue
            all_entries.append({
                "path": str(item),
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
            })
        return {"path": str(full_path), "entries": all_entries, "recursive": False}
    for p in full_path.rglob(pattern):
        if not p.is_file():
            continue
        rel = p.relative_to(full_path)
        if any(_skip_dir(part) for part in rel.parts):
            continue
        all_entries.append({"path": str(p), "relative": str(rel), "name": p.name})
    return {"path": str(full_path), "entries": all_entries[:500], "recursive": True}


@tool
def search_in_files(directory: str, query: str, file_pattern: str = "*.py", max_files: int = 50) -> Dict[str, Any]:
    """Поиск по всему проекту. Примеры запросов:
    - 'flask' или 'django' или 'fastapi'
    - 'FROM ' (для поиска существующих Dockerfile)
    - 'postgres' / 'redis' / 'mysql'
    - 'requirements.txt' или 'package.json'"""
    root = resolve_abs_path(directory)
    results: List[Dict[str, Any]] = []
    query_lower = query.lower()
    n = 0
    for f in root.rglob(file_pattern):
        if not f.is_file() or n >= max_files:
            break
        if any(_skip_dir(part) for part in f.relative_to(root).parts):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            if query_lower in text.lower():
                lines = [i + 1 for i, line in enumerate(text.splitlines()) if query_lower in line.lower()]
                results.append({"file": str(f), "lines": lines[:20]})
                n += 1
        except Exception:
            continue
    return {"query": query, "directory": str(root), "matches": results}


@tool
def edit_file(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """Редактирует существующий файл (например, добавляет volume в docker-compose)."""
    full_path = resolve_abs_path(path)
    if old_str == "":
        before_text = ""
        before_total_lines = 0
        snapshot_id = ""
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if full_path.exists():
            before_text = full_path.read_text(encoding="utf-8", errors="ignore")
            before_total_lines = len(before_text.splitlines())
        full_path.write_text(new_str, encoding="utf-8")
        lines = len(new_str.splitlines())
        after_total_lines = lines
        return {
            "path": str(full_path),
            "action": "created_file",
            "lines": lines,
            "before_total_lines": before_total_lines,
            "after_total_lines": after_total_lines,
            "delta_total_lines": after_total_lines - before_total_lines,
            "total_lines": after_total_lines,
            "snapshot_id": snapshot_id,
        }
    try:
        original = full_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"path": str(full_path), "action": "file_not_found"}
    before_total_lines = len(original.splitlines())
    if old_str not in original:
        return {"path": str(full_path), "action": "old_str not found"}
    edited = original.replace(old_str, new_str, 1)
    full_path.write_text(edited, encoding="utf-8")
    old_lines = len(old_str.splitlines())
    new_lines = len(new_str.splitlines())
    total_lines = len(edited.splitlines())
    return {
        "path": str(full_path),
        "action": "edited",
        "lines_before": old_lines,
        "lines_after": new_lines,
        "lines_delta": new_lines - old_lines,
        "total_lines": total_lines,
        "before_total_lines": before_total_lines,
        "after_total_lines": total_lines,
        "delta_total_lines": total_lines - before_total_lines,
    }


@tool
def write_file(path: str, content: str) -> Dict[str, Any]:
    """Создаёт/перезаписывает Dockerfile или docker-compose.yml.
    Всегда используй для генерации Docker-файлов."""
    full_path = resolve_abs_path(path)
    before_text = ""
    before_total_lines = 0
    snapshot_id = ""
    full_path.parent.mkdir(parents=True, exist_ok=True)
    if full_path.exists():
        before_text = full_path.read_text(encoding="utf-8", errors="ignore")
        before_total_lines = len(before_text.splitlines())
    full_path.write_text(content, encoding="utf-8")
    total_lines = len(content.splitlines())
    return {
        "path": str(full_path),
        "action": "written",
        "total_lines": total_lines,
        "before_total_lines": before_total_lines,
        "after_total_lines": total_lines,
        "delta_total_lines": total_lines - before_total_lines,
        "snapshot_id": snapshot_id,
    }


@tool
def get_file_line_count(path: str) -> Dict[str, Any]:
    """Возвращает количество строк в файле. Полезно для отображения состояния файла."""
    full_path = resolve_abs_path(path)
    text = full_path.read_text(encoding="utf-8", errors="ignore")
    total_lines = len(text.splitlines())
    return {"path": str(full_path), "total_lines": total_lines}


@tool
def analyze_project(project_root: str) -> Dict[str, Any]:
    """Комплексный анализ проекта для рекомендаций по серверу и генерации Docker.
    Анализирует структуру, определяет языки, фреймворки, базы данных, тип приложения,
    реальный размер проекта и ключевые файлы.
    Используется перед recommend_server_specs и generate_docker_files."""

    root = project_root.rstrip("/")

    try:
        # 1. Получаем полный список файлов
        files_result = list_files.invoke({"path": root, "recursive": True})
        entries = files_result.get("entries", [])
        file_count = len(entries)

        # 2. Реальный расчёт размера проекта (в МБ)
        total_size_bytes = 0
        file_paths = []
        file_names = []
        for entry in entries:
            p_str = entry.get("path") or entry.get("relative")
            if p_str:
                file_paths.append(p_str)
                file_names.append(entry.get("name", "").lower())
                try:
                    total_size_bytes += Path(p_str).stat().st_size
                except Exception:
                    pass  # пропускаем недоступные файлы

        total_size_mb = round(total_size_bytes / (1024 * 1024), 1)

        # 3. Чтение ключевых manifest-файлов (для точного определения зависимостей)
        tech_stack = {"languages": set(), "frameworks": set(), "databases": set(), "key_files": []}

        # Python
        for manifest in ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]:
            if manifest in file_names:
                path = next((p for p in file_paths if p.lower().endswith(manifest)), None)
                if path:
                    content = read_file.invoke({"filename": path}).get("content", "").lower()
                    tech_stack["languages"].add("Python")
                    tech_stack["key_files"].append(manifest)

                    if "fastapi" in content:
                        tech_stack["frameworks"].add("FastAPI")
                    elif "flask" in content:
                        tech_stack["frameworks"].add("Flask")
                    elif "django" in content:
                        tech_stack["frameworks"].add("Django")
                    break

        # Node.js
        if "package.json" in file_names:
            path = next((p for p in file_paths if p.lower().endswith("package.json")), None)
            if path:
                content = read_file.invoke({"filename": path}).get("content", "").lower()
                tech_stack["languages"].add("JavaScript/TypeScript")
                tech_stack["key_files"].append("package.json")

                if "express" in content:
                    tech_stack["frameworks"].add("Express")
                elif '"next"' in content or "next" in content:
                    tech_stack["frameworks"].add("Next.js")
                elif "nestjs" in content:
                    tech_stack["frameworks"].add("NestJS")

        # Java / PHP / Go
        if any(f in file_names for f in ["pom.xml", "build.gradle"]):
            tech_stack["languages"].add("Java")
            tech_stack["frameworks"].add("Spring Boot" if "spring" in str(file_names).lower() else "Java")
            tech_stack["key_files"].append("pom.xml")
        if "composer.json" in file_names:
            tech_stack["languages"].add("PHP")
            tech_stack["frameworks"].add("Laravel")
            tech_stack["key_files"].append("composer.json")
        if "go.mod" in file_names:
            tech_stack["languages"].add("Go")
            tech_stack["key_files"].append("go.mod")

        # 4. Поиск баз данных и брокеров (по содержимому кода)
        db_search = search_in_files.invoke({
            "directory": root,
            "query": "postgres|postgresql|mysql|mariadb|mongodb|redis|sqlite|prisma|sqlalchemy|mongoose|typeorm",
            "file_pattern": "*.*",
            "max_files": 40
        })
        db_text = " ".join(str(m).lower() for m in db_search.get("matches", []))
        if "postgres" in db_text or "postgresql" in db_text:
            tech_stack["databases"].add("PostgreSQL")
        if "mysql" in db_text or "mariadb" in db_text:
            tech_stack["databases"].add("MySQL")
        if "redis" in db_text:
            tech_stack["databases"].add("Redis")
        if "mongodb" in db_text:
            tech_stack["databases"].add("MongoDB")
        if "sqlite" in db_text:
            tech_stack["databases"].add("SQLite")

        # 5. Определение типа приложения
        app_type = "web_api"
        if "Next.js" in tech_stack["frameworks"] or any(
                "pages/" in p.lower() or "app/" in p.lower() for p in file_paths):
            app_type = "fullstack"
        elif any(x in " ".join(file_names).lower() for x in ["worker", "celery", "queue", "task", "background"]):
            app_type = "background_worker"
        elif any(x in " ".join(file_names).lower() for x in ["bot", "telegram", "discord"]):
            app_type = "bot"

        # 6. Наличие Docker
        has_docker = any("dockerfile" in name or "docker-compose" in name for name in file_names)

        # 7. Итоговый summary (удобно для recommend_server_specs)
        languages = sorted(tech_stack["languages"]) or ["Unknown"]
        frameworks = sorted(tech_stack["frameworks"])
        dbs = sorted(tech_stack["databases"])

        summary = f"{', '.join(languages)}"
        if frameworks:
            summary += f" + {', '.join(frameworks)}"
        if dbs:
            summary += f" + БД: {', '.join(dbs)}"
        summary += f". Тип: {app_type}. Файлов: {file_count} ({total_size_mb} МБ)"

        return {
            "project_root": root,
            "detected_languages": languages,
            "frameworks": frameworks,
            "databases": dbs,
            "app_type": app_type,
            "file_count": file_count,
            "total_size_mb": total_size_mb,
            "has_docker": has_docker,
            "key_manifest_files": tech_stack["key_files"][:6],
            "summary": summary,
            "confidence": "high" if languages and languages[0] != "Unknown" else "medium",
            "raw_data": {
                "framework_matches": len(db_search.get("matches", [])),
                "entrypoint_candidates": [f for f in file_names if f in ("main.py", "app.py", "server.js", "index.js")]
            }
        }

    except Exception as e:
        return {
            "error": str(e),
            "project_root": root,
            "status": "failed",
            "summary": "Не удалось проанализировать проект (проверьте путь и права доступа)",
            "confidence": "low"
        }


@tool
def explain_metrics(metric: str) -> str:
    """Подробно объясняет метрику производительности облачного сервера (на русском).
    metric может быть: cpu_load, ram_usage, disk_io, network, requests_per_second,
    disk_space, cpu_steal, swap_usage, connection_count."""

    explanations = {
        "cpu_load": "CPU Load — средняя загрузка процессора за 1/5/15 минут (в %). "
                    "Норма: <70%. Критично: >85% длительно → приложение тормозит. "
                    "Рекомендация: апгрейд CPU или оптимизация кода.",

        "ram_usage": "RAM Usage — используемая оперативная память (в % и ГБ). "
                     "Норма: <80%. Если >90% и растёт — начинается свопинг и деградация производительности. "
                     "Рекомендация: увеличить RAM или добавить кэширование (Redis).",

        "disk_io": "Disk I/O — операции чтения/записи в секунду (IOPS) и пропускная способность (MB/s). "
                   "Высокие значения (>80% от лимита диска) приводят к задержкам. "
                   "Рекомендация: перейти на NVMe SSD или добавить кэш.",

        "network": "Network — входящий/исходящий трафик (Mbps) и пакеты в секунду. "
                   "Пределы зависят от тарифа. Если接近 лимиту — возможны потери пакетов и медленный ответ.",

        "requests_per_second": "Requests per Second (RPS) — количество HTTP-запросов в секунду. "
                               "Показывает реальную нагрузку на приложение. "
                               "Если RPS близок к максимуму сервера — нужен апгрейд или горизонтальное масштабирование.",

        "disk_space": "Disk Space — свободное место на диске. "
                      "Критично <10%. Docker-образы и логи быстро съедают место.",

        "cpu_steal": "CPU Steal — время, которое CPU тратит на других соседей по железу (только VPS). "
                     "Если >5% постоянно — провайдер перегружен, пора мигрировать.",

        "swap_usage": "Swap Usage — использование swap-файла. "
                      "Любое использование swap (>0%) = катастрофическая деградация скорости. "
                      "Решение: увеличить RAM.",

        "connection_count": "Connection Count — количество одновременных TCP-соединений. "
                            "Если >80% от лимита ОС — приложение перестаёт принимать новые соединения."
    }

    metric = metric.lower().strip()
    return explanations.get(
        metric,
        f"Метрика '{metric}' не найдена. Доступные: cpu_load, ram_usage, disk_io, network, "
        f"requests_per_second, disk_space, cpu_steal, swap_usage, connection_count."
    )
