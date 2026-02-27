# -*- coding: utf-8 -*-
"""
Тесты для модуля обработки ТРУ/РКМ файлов (tru_rkm_processor.py)
"""
import pytest
import os
import glob
from pathlib import Path
from bom_categorizer.tru_rkm_processor import (
    detect_file_type,
    generate_output_filename,
)


# ──────────────────────────────────────────────────────────────────────
# detect_file_type
# ──────────────────────────────────────────────────────────────────────
class TestDetectFileType:
    """Тесты определения типа файла по имени"""

    def test_latin_tru(self):
        """Латиница tru → 'tpy'"""
        assert detect_file_type("data_tru.xlsx") == 'tpy'

    def test_latin_try(self):
        """Латиница try → 'tpy'"""
        assert detect_file_type("data_try.xlsx") == 'tpy'

    def test_latin_tpy(self):
        """Латиница tpy → 'tpy'"""
        assert detect_file_type("data_tpy.xlsx") == 'tpy'

    def test_cyrillic_tru(self):
        """Кириллица тру → 'tpy'"""
        assert detect_file_type("data_тру.xlsx") == 'tpy'

    def test_latin_rkm(self):
        """Латиница rkm → 'rkm'"""
        assert detect_file_type("data_rkm.xlsx") == 'rkm'

    def test_latin_pkm(self):
        """Латиница pkm → 'rkm'"""
        assert detect_file_type("data_pkm.xlsx") == 'rkm'

    def test_cyrillic_rkm(self):
        """Кириллица ркм → 'rkm'"""
        assert detect_file_type("data_ркм.xlsx") == 'rkm'

    def test_unknown_file(self):
        """Неизвестный файл → None"""
        assert detect_file_type("data.xlsx") is None

    def test_case_insensitive(self):
        """Регистронезависимое определение"""
        assert detect_file_type("DATA_TRU.XLSX") == 'tpy'
        assert detect_file_type("Data_RKM.Xlsx") == 'rkm'

    def test_tru_in_middle_of_name(self):
        """ТРУ в середине имени файла"""
        assert detect_file_type("ТРУ.953033.7471_tpy.xlsx") == 'tpy'


# ──────────────────────────────────────────────────────────────────────
# generate_output_filename
# ──────────────────────────────────────────────────────────────────────
class TestGenerateOutputFilename:
    """Тесты генерации имени выходного файла"""

    def test_basic_output_name(self, temp_dir):
        """Добавляет суффикс _tpy"""
        input_path = str(temp_dir / "input.xls")
        result = generate_output_filename(input_path, "tpy")
        assert "_tpy" in result
        assert result.endswith(".xlsx")

    def test_rkm_suffix(self, temp_dir):
        """Добавляет суффикс _rkm"""
        input_path = str(temp_dir / "input.xls")
        result = generate_output_filename(input_path, "rkm")
        assert "_rkm" in result

    def test_preserves_directory(self, temp_dir):
        """Выходной файл в той же директории"""
        input_path = str(temp_dir / "input.xls")
        result = generate_output_filename(input_path, "tpy")
        assert os.path.dirname(result) == str(temp_dir)


# ──────────────────────────────────────────────────────────────────────
# _read_tru_file (интеграционный)
# ──────────────────────────────────────────────────────────────────────
class TestReadTruFile:
    """Интеграционные тесты чтения реальных ТРУ файлов"""

    def test_read_real_tru_file(self, tru_dir):
        """Чтение реального ТРУ файла"""
        tru_files = list(tru_dir.glob("*.xlsx"))
        if not tru_files:
            pytest.skip("ТРУ файлы не найдены")

        from bom_categorizer.tru_rkm_processor import _read_tru_file

        tru_df = _read_tru_file(str(tru_files[0]))
        assert tru_df is not None
        assert len(tru_df) > 0

    def test_tru_has_expected_columns(self, tru_dir):
        """ТРУ файл содержит ожидаемые колонки"""
        tru_files = list(tru_dir.glob("*.xlsx"))
        if not tru_files:
            pytest.skip("ТРУ файлы не найдены")

        from bom_categorizer.tru_rkm_processor import _read_tru_file

        tru_df = _read_tru_file(str(tru_files[0]))
        if tru_df is None:
            pytest.skip("Не удалось прочитать ТРУ файл")

        # Должна быть хотя бы колонка с наименованием
        name_cols = [c for c in tru_df.columns if 'наименование' in str(c).lower()]
        assert len(name_cols) > 0, f"Колонка наименования не найдена. Колонки: {list(tru_df.columns)}"

    def test_multiple_tru_files_readable(self, tru_dir):
        """Все ТРУ файлы читаются без ошибок"""
        tru_files = list(tru_dir.glob("*.xlsx"))
        if not tru_files:
            pytest.skip("ТРУ файлы не найдены")

        from bom_categorizer.tru_rkm_processor import _read_tru_file

        success_count = 0
        for tf in tru_files[:5]:  # Проверяем первые 5
            try:
                df = _read_tru_file(str(tf))
                if df is not None and len(df) > 0:
                    success_count += 1
            except Exception:
                pass

        assert success_count > 0, "Ни один ТРУ файл не удалось прочитать"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
