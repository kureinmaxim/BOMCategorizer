"""
Конфигурация pytest и общие фикстуры
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def example_dir():
    """Путь к папке с примерами"""
    return project_root / "example"


@pytest.fixture
def test_data_dir():
    """Путь к папке с тестовыми данными"""
    return project_root / "tests" / "test_data"


@pytest.fixture
def temp_dir():
    """Временная директория для тестов"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_component_data():
    """Пример данных компонента"""
    return {
        'reference': 'R1',
        'description': 'Резистор 100 Ом ± 5% - М',
        'value': '100 Ом',
        'quantity': 10,
        'note': '',
        'source_file': 'test.xlsx'
    }


@pytest.fixture
def mock_component_database(monkeypatch, temp_dir):
    """Мокируем базу данных компонентов для тестов"""
    db_path = temp_dir / "component_database.json"

    def mock_get_database_path():
        return str(db_path)

    from bom_categorizer import component_database
    monkeypatch.setattr(component_database, 'get_database_path', mock_get_database_path)

    return db_path


@pytest.fixture
def tru_dir():
    """Путь к папке с ТРУ файлами"""
    return project_root / "TRU"


@pytest.fixture
def real_bom_file():
    """Реальный BOM файл для интеграционных тестов"""
    path = project_root / "БФ+БУ_ШСК-М.xlsx"
    if not path.exists():
        pytest.skip("Реальный BOM файл не найден")
    return path


@pytest.fixture
def sample_bom_df():
    """Синтетический BOM DataFrame для юнит-тестов"""
    return pd.DataFrame({
        'Наименование ИВП': [
            'Микросхема 1564АП3У2',
            'Резистор P1 - 12 - 0,125 - 100 Ом ± 5% - Т',
            'Конденсатор К10-17Б 0,1 мкФ',
            'Чип катушки индуктивности 0603HP-47NXJ_LW',
            'Модуль электропитания МДМ100-1В3ЦФУ',
        ],
        'шт.': [10, 20, 5, 3, 8],
        'ТУ/Производитель': ['АЕЯР.431320.420ТУ', '', '', 'Coilcraft', ''],
    })


@pytest.fixture
def sample_tru_df():
    """Синтетический ТРУ DataFrame для юнит-тестов"""
    return pd.DataFrame({
        'Наименование': [
            'Микросхема 1564АП3У2 ЭП',
            'Чип катушки индуктивности 0603HP-47NXJ_LW Coilcraft',
            'Конденсатор К10-17Б-Н90-0,1 мкФ ± 10%',
            'Модуль электропитания МДМ100-1В3ЦФУ',
            'Разъем Вилка МДМ30-1В15ТУП',
        ],
        'Артикул': ['12345', '67890', '11111', '22222', '33333'],
        'Количество': [10, 20, 5, 3, 8],
        'Цена': [100.0, 50.0, 20.0, 500.0, 150.0],
        'Стоимость': [1000.0, 1000.0, 100.0, 1500.0, 1200.0],
    })


@pytest.fixture
def make_temp_excel(temp_dir):
    """Фабрика для создания временных Excel файлов"""
    def _make(data_by_sheet, filename="test.xlsx"):
        path = temp_dir / filename
        with pd.ExcelWriter(str(path), engine='openpyxl') as writer:
            for sheet_name, df in data_by_sheet.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        return path
    return _make
