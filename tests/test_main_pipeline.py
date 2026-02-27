# -*- coding: utf-8 -*-
"""
Тесты для функций обработки пайплайна (main.py)
"""
import pytest
import pandas as pd
from bom_categorizer.main import (
    multiply_quantities,
    aggregate_duplicate_items,
    normalize_name_for_comparison,
    detect_comparison_file_type,
)


# ──────────────────────────────────────────────────────────────────────
# multiply_quantities
# ──────────────────────────────────────────────────────────────────────
class TestMultiplyQuantities:
    """Тесты умножения количества"""

    def test_multiplier_1_no_change(self):
        """Множитель 1 → без изменений"""
        df = pd.DataFrame({'description': ['R1'], 'qty': [10]})
        result = multiply_quantities(df, 1)
        assert result['qty'].iloc[0] == 10

    def test_multiplier_doubles(self):
        """Множитель 2 → удвоение"""
        df = pd.DataFrame({'description': ['R1'], 'количество': [10]})
        result = multiply_quantities(df, 2)
        assert result['количество'].iloc[0] == 20

    def test_finds_qty_column_variants(self):
        """Находит колонку 'количество' по ключевому слову"""
        df = pd.DataFrame({'description': ['R1'], 'количество': [5]})
        result = multiply_quantities(df, 3)
        assert result['количество'].iloc[0] == 15

    def test_no_qty_column_returns_unchanged(self):
        """Без колонки количества → без изменений"""
        df = pd.DataFrame({'description': ['R1'], 'name': ['test']})
        result = multiply_quantities(df, 5)
        assert len(result) == 1

    def test_nan_qty_handled(self):
        """NaN количества обрабатываются корректно"""
        df = pd.DataFrame({'description': ['R1', 'R2'], 'qty': [10, float('nan')]})
        result = multiply_quantities(df, 2)
        # Не должно выбрасывать ошибку
        assert len(result) == 2


# ──────────────────────────────────────────────────────────────────────
# aggregate_duplicate_items
# ──────────────────────────────────────────────────────────────────────
class TestAggregateDuplicateItems:
    """Тесты агрегации дубликатов"""

    def test_basic_deduplication(self):
        """Два одинаковых элемента объединяются"""
        df = pd.DataFrame({
            'description': ['Резистор 100 Ом', 'Резистор 100 Ом'],
            'ref': ['R1', 'R2'],
            'qty': [5, 3],
            'source_file': ['test.xlsx', 'test.xlsx'],
            'source_sheet': ['Sheet1', 'Sheet1'],
        })
        result = aggregate_duplicate_items(df, 'description')
        assert len(result) == 1
        assert result['qty'].iloc[0] == 8

    def test_different_items_not_merged(self):
        """Разные элементы не объединяются"""
        df = pd.DataFrame({
            'description': ['Резистор 100 Ом', 'Конденсатор 10 нФ'],
            'ref': ['R1', 'C1'],
            'qty': [5, 3],
            'source_file': ['test.xlsx', 'test.xlsx'],
            'source_sheet': ['Sheet1', 'Sheet1'],
        })
        result = aggregate_duplicate_items(df, 'description')
        assert len(result) == 2

    def test_different_source_files_not_merged(self):
        """Элементы из разных файлов не объединяются (combine=False)"""
        df = pd.DataFrame({
            'description': ['Резистор 100 Ом', 'Резистор 100 Ом'],
            'ref': ['R1', 'R2'],
            'qty': [5, 3],
            'source_file': ['file1.xlsx', 'file2.xlsx'],
            'source_sheet': ['Sheet1', 'Sheet1'],
        })
        result = aggregate_duplicate_items(df, 'description', combine_across_files=False)
        assert len(result) == 2

    def test_combine_across_files(self):
        """С combine_across_files=True элементы из разных файлов объединяются"""
        df = pd.DataFrame({
            'description': ['Резистор 100 Ом', 'Резистор 100 Ом'],
            'ref': ['R1', 'R2'],
            'qty': [5, 3],
            'source_file': ['file1.xlsx', 'file2.xlsx'],
            'source_sheet': ['Sheet1', 'Sheet1'],
        })
        result = aggregate_duplicate_items(df, 'description', combine_across_files=True)
        assert len(result) == 1

    def test_reference_concatenation(self):
        """Позиционные обозначения объединяются через запятую"""
        df = pd.DataFrame({
            'description': ['Резистор 100 Ом', 'Резистор 100 Ом'],
            'ref': ['R1', 'R2'],
            'qty': [5, 3],
            'source_file': ['test.xlsx', 'test.xlsx'],
            'source_sheet': ['Sheet1', 'Sheet1'],
        })
        result = aggregate_duplicate_items(df, 'description')
        if 'ref' in result.columns:
            ref_val = str(result['ref'].iloc[0])
            assert 'R1' in ref_val and 'R2' in ref_val


# ──────────────────────────────────────────────────────────────────────
# normalize_name_for_comparison
# ──────────────────────────────────────────────────────────────────────
class TestNormalizeNameForComparison:
    """Тесты нормализации названий для сравнения"""

    def test_strips_whitespace(self):
        """Удаление пробелов по краям"""
        assert normalize_name_for_comparison("  hello  ") == "hello"

    def test_collapses_spaces(self):
        """Множественные пробелы → один"""
        assert normalize_name_for_comparison("hello   world") == "hello world"

    def test_empty_returns_empty(self):
        """Пустая строка → пустая строка"""
        assert normalize_name_for_comparison("") == ""

    def test_none_returns_empty(self):
        """None → пустая строка"""
        assert normalize_name_for_comparison(None) == ""

    def test_nan_returns_empty(self):
        """NaN → пустая строка"""
        assert normalize_name_for_comparison(float('nan')) == ""


# ──────────────────────────────────────────────────────────────────────
# detect_comparison_file_type
# ──────────────────────────────────────────────────────────────────────
class TestDetectComparisonFileType:
    """Тесты определения типа файла для сравнения"""

    def test_bom_file_detected(self, make_temp_excel):
        """Файл с листами категорий → 'bom'"""
        path = make_temp_excel({
            'Резисторы': pd.DataFrame({'Наименование ИВП': ['R1']}),
            'Конденсаторы': pd.DataFrame({'Наименование ИВП': ['C1']}),
        }, "bom_test.xlsx")
        assert detect_comparison_file_type(str(path)) == 'bom'

    def test_flat_file_detected(self, make_temp_excel):
        """Файл с листом РКМ → 'flat'"""
        path = make_temp_excel({
            'РКМ': pd.DataFrame({'Наименование': ['Test']}),
        }, "flat_test.xlsx")
        assert detect_comparison_file_type(str(path)) == 'flat'

    def test_single_sheet_is_flat(self, make_temp_excel):
        """Один лист без категорий → 'flat'"""
        path = make_temp_excel({
            'Sheet1': pd.DataFrame({'col1': [1, 2, 3]}),
        }, "single_test.xlsx")
        assert detect_comparison_file_type(str(path)) == 'flat'

    def test_nonexistent_file(self):
        """Несуществующий файл → 'unknown'"""
        assert detect_comparison_file_type("/nonexistent/file.xlsx") == 'unknown'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
