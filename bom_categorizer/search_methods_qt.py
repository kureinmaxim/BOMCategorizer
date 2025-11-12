# -*- coding: utf-8 -*-
"""
Методы глобального поиска для GUI

Содержит функции для выполнения поиска по файлам и базе данных
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .gui_qt import BOMCategorizerMainWindow


def perform_global_search(window: 'BOMCategorizerMainWindow', query: str) -> Dict[str, Any]:
    """Выполняет поиск по базе данных и загруженным файлам."""
    timestamp = datetime.now()
    results: Dict[str, Any] = {
        "query": query,
        "timestamp": timestamp,
        "duration_ms": None,
        "total_matches": 0,
        "database": None,
        "database_path": None,
        "inputs": [],
        "inputs_examined": len(window.input_files),
        "output": None,
        "comparison": [],
        "counts": {
            "database": 0,
            "inputs": 0,
            "output": 0,
            "comparison": 0
        },
        "notes": []
    }

    query_normalized = query.casefold()
    start_perf = time.perf_counter()
    seen_paths = set()

    # Поиск в базе данных компонентов
    try:
        from . import component_database as comp_db

        db_path = comp_db.get_database_path()
        results["database_path"] = db_path
        components = comp_db.load_component_database()

        matches = []
        for name, category_key in components.items():
            if not isinstance(name, str):
                name = str(name)
            category_label = comp_db.CATEGORY_NAMES.get(category_key, category_key)
            name_normalized = name.casefold()
            category_normalized = category_label.casefold() if isinstance(category_label, str) else ""

            if query_normalized in name_normalized or (category_normalized and query_normalized in category_normalized):
                matches.append({
                    "name": name,
                    "category": category_label
                })

        if matches:
            sample_limit = 20
            results["database"] = {
                "count": len(matches),
                "path": db_path,
                "matches": matches,
                "samples": matches[:sample_limit],
                "extra": max(0, len(matches) - sample_limit)
            }
            results["total_matches"] += len(matches)
            results["counts"]["database"] = len(matches)
    except Exception as exc:
        results["notes"].append({
            "source": "База данных",
            "message": f"Не удалось выполнить поиск в базе: {exc}"
        })

    # Поиск во входных файлах
    for path in window.input_files.keys():
        if not path:
            continue
        abs_path = os.path.abspath(path)
        if abs_path in seen_paths:
            continue
        seen_paths.add(abs_path)

        if not os.path.exists(path):
            results["notes"].append({
                "source": os.path.basename(path) or path,
                "message": "Файл не найден (возможно, перемещен или удален)."
            })
            continue

        entry = search_in_path(path, query_normalized)
        entry["source_type"] = "input"
        if entry["count"] > 0 or entry.get("error"):
            results["inputs"].append(entry)
            if entry["count"] > 0:
                results["total_matches"] += entry["count"]
                results["counts"]["inputs"] += entry["count"]
        if entry.get("error"):
            results["notes"].append({
                "source": entry.get("display", entry.get("filename", path)),
                "message": entry["error"]
            })

    # Поиск в выходном файле
    output_path = window.output_entry.text().strip() if hasattr(window, "output_entry") else ""
    if output_path:
        abs_output = os.path.abspath(output_path)
        if abs_output not in seen_paths and os.path.exists(output_path):
            entry = search_in_path(
                output_path,
                query_normalized,
                label=f"Выходной файл ({os.path.basename(output_path)})"
            )
            entry["source_type"] = "output"
            results["output"] = entry
            if entry["count"] > 0:
                results["total_matches"] += entry["count"]
                results["counts"]["output"] = entry["count"]
            if entry.get("error"):
                results["notes"].append({
                    "source": entry.get("display", "Выходной файл"),
                    "message": entry["error"]
                })
            seen_paths.add(abs_output)
        elif output_path and not os.path.exists(output_path):
            results["notes"].append({
                "source": "Выходной файл",
                "message": "Файл не найден. Выполните обработку, чтобы создать выходной файл."
            })

    # Поиск в файлах сравнения
    comparison_entries: List[Dict[str, Any]] = []
    comparison_sources = [
        ("Базовый файл сравнения", getattr(window, "compare_entry1", None)),
        ("Новый файл сравнения", getattr(window, "compare_entry2", None)),
        ("Результат сравнения", getattr(window, "compare_output_entry", None)),
    ]

    comparison_seen = set()
    for label, widget in comparison_sources:
        if widget is None:
            continue
        path = widget.text().strip()
        if not path:
            continue

        abs_path = os.path.abspath(path)
        if abs_path in comparison_seen:
            continue

        if not os.path.exists(path):
            results["notes"].append({
                "source": label,
                "message": "Файл не найден."
            })
            continue

        entry = search_in_path(
            path,
            query_normalized,
            label=f"{label} ({os.path.basename(path)})"
        )
        entry["source_type"] = "comparison"
        comparison_entries.append(entry)
        if entry["count"] > 0:
            results["total_matches"] += entry["count"]
            results["counts"]["comparison"] += entry["count"]
        if entry.get("error"):
            results["notes"].append({
                "source": entry.get("display", label),
                "message": entry["error"]
            })
        comparison_seen.add(abs_path)

    if comparison_entries:
        comparison_entries.sort(key=lambda item: item.get("count", 0), reverse=True)
        results["comparison"] = comparison_entries

    # Сортируем входные файлы по количеству совпадений
    if results["inputs"]:
        results["inputs"].sort(key=lambda item: item.get("count", 0), reverse=True)

    # Фиксируем длительность поиска
    elapsed_ms = int((time.perf_counter() - start_perf) * 1000)
    results["duration_ms"] = elapsed_ms

    return results


def search_in_path(file_path: str, query_lower: str, label: Optional[str] = None,
                   max_examples: int = 12) -> Dict[str, Any]:
    """Ищет совпадения в указанном файле."""
    display_name = label if label else (os.path.basename(file_path) or file_path)
    result: Dict[str, Any] = {
        "path": file_path,
        "display": display_name,
        "filename": os.path.basename(file_path) or file_path,
        "count": 0,
        "samples": [],
        "extra": 0,
        "error": None
    }

    if not query_lower:
        return result

    term = query_lower
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext in ('.xlsx', '.xlsm', '.xlsb', '.xls'):
            try:
                import pandas as pd
            except ImportError as exc:
                result["error"] = f"Не установлены зависимости для Excel (pandas/openpyxl): {exc}"
                return result

            try:
                xls = pd.ExcelFile(file_path, engine='openpyxl')
            except Exception as exc:
                result["error"] = f"Не удалось открыть Excel файл: {exc}"
                return result

            for sheet in xls.sheet_names:
                try:
                    df = xls.parse(sheet_name=sheet, dtype=str)
                except Exception as exc:
                    result["error"] = f"Ошибка чтения листа «{sheet}»: {exc}"
                    continue

                df = df.fillna('')
                records = df.to_dict(orient='records')
                for row_idx, row in enumerate(records, start=2):
                    for column, value in row.items():
                        text = str(value).strip()
                        if not text:
                            continue
                        normalized = text.casefold()
                        if normalized in ('nan', 'none'):
                            continue
                        if term in normalized:
                            result["count"] += 1
                            if len(result["samples"]) < max_examples:
                                location = f"{sheet}: {column} (строка {row_idx})"
                                result["samples"].append({
                                    "location": location,
                                    "context": make_snippet(text)
                                })

        elif ext in ('.txt', '.csv', '.log', '.md', '.json', '.ini', '.cfg'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_no, line in enumerate(f, start=1):
                        normalized = line.casefold()
                        if term in normalized:
                            result["count"] += 1
                            if len(result["samples"]) < max_examples:
                                result["samples"].append({
                                    "location": f"Строка {line_no}",
                                    "context": make_snippet(line)
                                })
            except Exception as exc:
                result["error"] = f"Не удалось прочитать файл: {exc}"

        elif ext in ('.docx',):
            try:
                from docx import Document
            except ImportError as exc:
                result["error"] = f"Не установлена библиотека python-docx: {exc}"
                return result

            try:
                doc = Document(file_path)
            except Exception as exc:
                result["error"] = f"Не удалось открыть DOCX: {exc}"
                return result

            for idx, para in enumerate(doc.paragraphs, start=1):
                text = para.text.strip()
                if not text:
                    continue
                if term in text.casefold():
                    result["count"] += 1
                    if len(result["samples"]) < max_examples:
                        result["samples"].append({
                            "location": f"Параграф {idx}",
                            "context": make_snippet(text)
                        })

        elif ext in ('.doc',):
            result["error"] = "Поиск в формате .doc не поддерживается. Конвертируйте файл в .docx."

        else:
            result["error"] = f"Формат {ext or 'неизвестен'} не поддерживается для поиска."

    except Exception as exc:
        result["error"] = f"Ошибка обработки файла: {exc}"
    finally:
        result["extra"] = max(0, result["count"] - len(result["samples"]))

    return result


def make_snippet(text: Any, max_length: int = 120) -> str:
    """Нормализует текст и ограничивает длину для отображения в результатах."""
    if text is None:
        return ""

    snippet = " ".join(str(text).split())
    if len(snippet) > max_length:
        return snippet[: max_length - 3] + "..."
    return snippet

