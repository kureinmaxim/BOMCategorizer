# -*- coding: utf-8 -*-
"""
Тесты для функций сравнения BOM файлов (main.py)
"""
import pytest
import os
import pandas as pd
from bom_categorizer.main import (
    compare_processed_files,
    compare_flat_files,
)


# ──────────────────────────────────────────────────────────────────────
# compare_processed_files
# ──────────────────────────────────────────────────────────────────────
class TestCompareProcessedFiles:
    """Тесты сравнения обработанных BOM файлов (с категориями)"""

    def test_identical_files(self, make_temp_excel, temp_dir):
        """Сравнение файла с самим собой"""
        path = make_temp_excel({
            'Резисторы': pd.DataFrame({
                'Наименование ИВП': ['Резистор 100 Ом', 'Резистор 200 Ом'],
                'шт.': [10, 5],
            }),
            'Конденсаторы': pd.DataFrame({
                'Наименование ИВП': ['Конденсатор 100 нФ'],
                'шт.': [20],
            }),
        }, "bom1.xlsx")
        output = str(temp_dir / "compare_result.xlsx")
        result = compare_processed_files(str(path), str(path), output)
        assert result is True
        assert os.path.exists(output)

    def test_added_component(self, make_temp_excel, temp_dir):
        """Обнаружение добавленного компонента"""
        path1 = make_temp_excel({
            'Резисторы': pd.DataFrame({
                'Наименование ИВП': ['Резистор 100 Ом'],
                'шт.': [10],
            }),
        }, "bom_base.xlsx")
        path2 = make_temp_excel({
            'Резисторы': pd.DataFrame({
                'Наименование ИВП': ['Резистор 100 Ом', 'Резистор 200 Ом'],
                'шт.': [10, 5],
            }),
        }, "bom_new.xlsx")
        output = str(temp_dir / "compare_added.xlsx")
        result = compare_processed_files(str(path1), str(path2), output)
        assert result is True
        assert os.path.exists(output)

    def test_removed_component(self, make_temp_excel, temp_dir):
        """Обнаружение удалённого компонента"""
        path1 = make_temp_excel({
            'Резисторы': pd.DataFrame({
                'Наименование ИВП': ['Резистор 100 Ом', 'Резистор 200 Ом'],
                'шт.': [10, 5],
            }),
        }, "bom_base2.xlsx")
        path2 = make_temp_excel({
            'Резисторы': pd.DataFrame({
                'Наименование ИВП': ['Резистор 100 Ом'],
                'шт.': [10],
            }),
        }, "bom_new2.xlsx")
        output = str(temp_dir / "compare_removed.xlsx")
        result = compare_processed_files(str(path1), str(path2), output)
        assert result is True
        assert os.path.exists(output)

    def test_quantity_change(self, make_temp_excel, temp_dir):
        """Обнаружение изменения количества"""
        path1 = make_temp_excel({
            'Резисторы': pd.DataFrame({
                'Наименование ИВП': ['Резистор 100 Ом'],
                'шт.': [10],
            }),
        }, "bom_qty1.xlsx")
        path2 = make_temp_excel({
            'Резисторы': pd.DataFrame({
                'Наименование ИВП': ['Резистор 100 Ом'],
                'шт.': [20],
            }),
        }, "bom_qty2.xlsx")
        output = str(temp_dir / "compare_qty.xlsx")
        result = compare_processed_files(str(path1), str(path2), output)
        assert result is True
        assert os.path.exists(output)


# ──────────────────────────────────────────────────────────────────────
# compare_flat_files
# ──────────────────────────────────────────────────────────────────────
class TestCompareFlatFiles:
    """Тесты сравнения плоских файлов"""

    def test_common_items_found(self, make_temp_excel, temp_dir):
        """Общие элементы обнаруживаются"""
        path1 = make_temp_excel({
            'Sheet1': pd.DataFrame({
                'Наименование': ['Резистор 100 Ом', 'Конденсатор 10 нФ'],
                'Количество': [10, 5],
            }),
        }, "flat1.xlsx")
        path2 = make_temp_excel({
            'Sheet1': pd.DataFrame({
                'Наименование': ['Резистор 100 Ом', 'Диод 1N4148'],
                'Количество': [10, 3],
            }),
        }, "flat2.xlsx")
        output = str(temp_dir / "flat_compare.xlsx")
        result = compare_flat_files(str(path1), str(path2), output)
        assert result is True
        assert os.path.exists(output)

    def test_unique_items_separated(self, make_temp_excel, temp_dir):
        """Уникальные элементы разделяются"""
        path1 = make_temp_excel({
            'Sheet1': pd.DataFrame({
                'Наименование': ['Только в файле 1'],
                'Количество': [10],
            }),
        }, "flat_unique1.xlsx")
        path2 = make_temp_excel({
            'Sheet1': pd.DataFrame({
                'Наименование': ['Только в файле 2'],
                'Количество': [5],
            }),
        }, "flat_unique2.xlsx")
        output = str(temp_dir / "flat_unique_compare.xlsx")
        result = compare_flat_files(str(path1), str(path2), output)
        assert result is True
        assert os.path.exists(output)

    def test_output_file_created(self, make_temp_excel, temp_dir):
        """Выходной файл создаётся"""
        path1 = make_temp_excel({
            'Sheet1': pd.DataFrame({
                'Наименование': ['A', 'B'],
                'Количество': [1, 2],
            }),
        }, "flat_a.xlsx")
        path2 = make_temp_excel({
            'Sheet1': pd.DataFrame({
                'Наименование': ['B', 'C'],
                'Количество': [2, 3],
            }),
        }, "flat_b.xlsx")
        output = str(temp_dir / "flat_output.xlsx")
        result = compare_flat_files(str(path1), str(path2), output)
        assert result is True
        assert os.path.exists(output)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
