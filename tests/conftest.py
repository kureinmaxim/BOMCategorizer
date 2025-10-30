"""
Конфигурация pytest и общие фикстуры
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

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
