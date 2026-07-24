# -*- coding: utf-8 -*-
"""Tests for terminal CLI argparse UX (bom_categorizer.main)."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPLIT = ROOT / "tools" / "split_bom.py"
PY = sys.executable


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(SPLIT), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class TestTerminalCliUx:
    def test_no_args_prints_help(self):
        r = _run()
        assert r.returncode == 0
        out = (r.stdout or "") + (r.stderr or "")
        assert "--inputs" in out
        assert "--xlsx" in out
        assert "Примеры" in out or "примеры" in out.lower() or "Подсказка" in out

    def test_missing_inputs_xlsx_shows_examples(self):
        r = _run("--combine")
        assert r.returncode == 2
        err = r.stderr or ""
        assert "[ОШИБКА]" in err
        assert "--inputs" in err or "inputs" in err.lower()
        assert "Примеры:" in err
        assert "--help" in err

    def test_compare_without_output(self):
        r = _run("--compare", "a.xlsx", "b.xlsx")
        assert r.returncode == 2
        err = r.stderr or ""
        assert "[ОШИБКА]" in err
        assert "compare-output" in err
        assert "Примеры:" in err

    def test_missing_input_file(self):
        r = _run("--inputs", "__no_such_bom__.xlsx", "--xlsx", "out.xlsx")
        assert r.returncode == 2
        err = r.stderr or ""
        assert "[ОШИБКА]" in err
        assert "не найден" in err.lower()

    def test_multiplier_suffix_is_stripped_for_existence(self):
        """GUI передаёт path:count — проверка существования должна игнорировать :N."""
        from bom_categorizer.main import _resolve_input_path
        assert _resolve_input_path(r"C:\data\bom.xlsx:3") == r"C:\data\bom.xlsx"
        readme = str(ROOT / "README.md")
        assert _resolve_input_path(f"{readme}:3") == readme
        r = _run("--inputs", f"{readme}:3", "--xlsx", str(ROOT / "_cli_ux_out.xlsx"))
        # Не должно упасть на «файл не найден» из‑за :3
        assert "не найден" not in (r.stderr or "").lower()
        # Может упасть позже на парсинге .md — это ок; главное не validation path
        if r.returncode == 2:
            assert "не найден" not in (r.stderr or "").lower()
