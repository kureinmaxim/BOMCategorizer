# -*- coding: utf-8 -*-
"""
Тесты для модуля парсинга файлов (parsers.py)
"""
import pytest
import os
from pathlib import Path
from bom_categorizer.parsers import (
    normalize_dashes,
    normalize_cell,
    count_from_reference,
    parse_txt_like,
)


# ──────────────────────────────────────────────────────────────────────
# normalize_dashes
# ──────────────────────────────────────────────────────────────────────
class TestNormalizeDashes:
    """Тесты нормализации тире"""

    def test_en_dash(self):
        """EN DASH (–) → обычный дефис"""
        assert normalize_dashes("С2\u201333") == "С2-33"

    def test_em_dash(self):
        """EM DASH (—) → обычный дефис"""
        assert normalize_dashes("С2\u201433") == "С2-33"

    def test_minus_sign(self):
        """MINUS SIGN (−) → обычный дефис"""
        assert normalize_dashes("С2\u221233") == "С2-33"

    def test_hyphen_variants(self):
        """HYPHEN (‐) и NON-BREAKING HYPHEN (‑) → обычный дефис"""
        assert "-" in normalize_dashes("С2\u201033")
        assert "-" in normalize_dashes("С2\u201133")

    def test_normal_dash_unchanged(self):
        """Обычный дефис не меняется"""
        assert normalize_dashes("С2-33") == "С2-33"

    def test_empty_and_none(self):
        """Пустая строка и None"""
        assert normalize_dashes("") == ""
        assert normalize_dashes(None) is None


# ──────────────────────────────────────────────────────────────────────
# normalize_cell
# ──────────────────────────────────────────────────────────────────────
class TestNormalizeCell:
    """Тесты нормализации содержимого ячеек"""

    def test_strips_whitespace(self):
        """Удаление пробелов по краям"""
        assert normalize_cell("  hello  ") == "hello"

    def test_normalizes_dashes(self):
        """Тире внутри текста нормализуются"""
        result = normalize_cell("С2\u201333")
        assert "\u2013" not in result
        assert "-" in result

    def test_none_returns_empty(self):
        """None → пустая строка"""
        assert normalize_cell(None) == ""

    def test_number_converted(self):
        """Числа конвертируются в строку"""
        assert normalize_cell(123) == "123"

    def test_preserves_tabs_and_newlines(self):
        """Табуляция и переводы строк сохраняются"""
        result = normalize_cell("a\tb\nc")
        assert "\t" in result
        assert "\n" in result


# ──────────────────────────────────────────────────────────────────────
# count_from_reference
# ──────────────────────────────────────────────────────────────────────
class TestCountFromReference:
    """Тесты подсчёта количества из позиционного обозначения"""

    def test_single_element(self):
        """R1 → 1"""
        assert count_from_reference("R1") == 1

    def test_comma_separated(self):
        """R1, R2 → 2"""
        assert count_from_reference("R1, R2") == 2

    def test_range(self):
        """R1-R6 → 6"""
        assert count_from_reference("R1-R6") == 6

    def test_prefixed_range(self):
        """FU1-FU6 → 6"""
        assert count_from_reference("FU1-FU6") == 6

    def test_mixed_range_and_single(self):
        """C1, C2, C3-C5 → 5"""
        assert count_from_reference("C1, C2, C3-C5") == 5

    def test_empty_reference(self):
        """Пустая строка → 1"""
        assert count_from_reference("") == 1

    def test_none_reference(self):
        """None → 1"""
        assert count_from_reference(None) == 1


# ──────────────────────────────────────────────────────────────────────
# parse_txt_like
# ──────────────────────────────────────────────────────────────────────
class TestParseTxtLike:
    """Тесты парсинга TXT файлов"""

    def test_simple_txt_file(self, temp_dir):
        """Парсинг простого UTF-8 TXT файла"""
        txt_path = temp_dir / "test_bom.txt"
        content = (
            "R1\tРезистор 100 Ом ± 5%\t10\n"
            "C1\tКонденсатор 100 нФ\t5\n"
        )
        txt_path.write_text(content, encoding='utf-8')

        df = parse_txt_like(str(txt_path))
        assert df is not None
        assert len(df) > 0

    def test_empty_file(self, temp_dir):
        """Пустой файл"""
        txt_path = temp_dir / "empty.txt"
        txt_path.write_text("", encoding='utf-8')

        df = parse_txt_like(str(txt_path))
        # Может вернуть пустой DataFrame или DataFrame с одной строкой
        assert df is not None

    def test_returns_dataframe(self, temp_dir):
        """Результат — всегда DataFrame"""
        import pandas as pd
        txt_path = temp_dir / "simple.txt"
        txt_path.write_text("R1 Резистор 100 Ом", encoding='utf-8')

        result = parse_txt_like(str(txt_path))
        assert isinstance(result, pd.DataFrame)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
