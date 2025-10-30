"""
Тесты для модуля базы данных компонентов
"""
import pytest
import json
from pathlib import Path
from bom_categorizer.component_database import (
    load_component_database,
    save_component_database,
    add_component_to_database,
    get_component_category,
    get_database_stats
)


class TestComponentDatabase:
    """Тесты базы данных компонентов"""
    
    def test_load_empty_database(self, mock_component_database):
        """Тест загрузки несуществующей базы - должна создаться начальная"""
        db = load_component_database()
        assert isinstance(db, dict)
        assert len(db) > 0  # Должны быть начальные компоненты
        assert "1594ТЛ2Т" in db  # Проверяем один из начальных
    
    def test_save_and_load_database(self, mock_component_database):
        """Тест сохранения и загрузки базы"""
        test_db = {
            "Component1": "resistors",
            "Component2": "capacitors",
            "Component3": "ics"
        }
        
        save_component_database(test_db)
        loaded_db = load_component_database()
        
        assert loaded_db == test_db
    
    def test_add_component(self, mock_component_database):
        """Тест добавления компонента"""
        # Очистить базу
        save_component_database({})
        
        # Добавить компонент
        add_component_to_database("Тестовый резистор", "resistors")
        
        # Проверить что добавился
        db = load_component_database()
        assert "Тестовый резистор" in db
        assert db["Тестовый резистор"] == "resistors"
    
    def test_add_duplicate_component(self, mock_component_database):
        """Тест добавления дубликата - должен обновить категорию"""
        save_component_database({})
        
        # Добавляем первый раз
        add_component_to_database("Component1", "resistors")
        
        # Добавляем второй раз с другой категорией
        add_component_to_database("Component1", "capacitors")
        
        db = load_component_database()
        assert db["Component1"] == "capacitors"  # Должна обновиться
    
    def test_get_component_category(self, mock_component_database):
        """Тест получения категории компонента"""
        test_db = {
            "Component1": "resistors",
            "Component2": "capacitors"
        }
        save_component_database(test_db)
        
        # Существующий компонент
        category = get_component_category("Component1")
        assert category == "resistors"
        
        # Несуществующий компонент
        category = get_component_category("NonExistent")
        assert category is None
    
    def test_get_component_category_case_insensitive(self, mock_component_database):
        """Тест поиска компонента без учета регистра"""
        test_db = {"Component1": "resistors"}
        save_component_database(test_db)
        
        # Разный регистр
        assert get_component_category("COMPONENT1") == "resistors"
        assert get_component_category("component1") == "resistors"
        assert get_component_category("CoMpOnEnT1") == "resistors"
    
    def test_get_database_stats(self, mock_component_database):
        """Тест получения статистики базы"""
        test_db = {
            "R1": "resistors",
            "R2": "resistors",
            "C1": "capacitors",
            "IC1": "ics",
            "IC2": "ics",
            "IC3": "ics"
        }
        save_component_database(test_db)
        
        stats = get_database_stats()
        
        assert stats['total'] == 6
        assert stats['by_category']['resistors'] == 2
        assert stats['by_category']['capacitors'] == 1
        assert stats['by_category']['ics'] == 3
    
    def test_component_name_normalization(self, mock_component_database):
        """Тест нормализации названий компонентов"""
        save_component_database({})
        
        # Добавляем с пробелами
        add_component_to_database("  Component with spaces  ", "resistors")
        
        db = load_component_database()
        # Должно сохраниться без лишних пробелов
        assert "Component with spaces" in db
        assert "  Component with spaces  " not in db
    
    def test_empty_component_name(self, mock_component_database):
        """Тест добавления пустого названия - не должно добавиться"""
        save_component_database({})
        
        add_component_to_database("", "resistors")
        add_component_to_database(None, "resistors")
        
        db = load_component_database()
        assert len(db) == 0
    
    def test_database_persistence(self, mock_component_database):
        """Тест что база данных сохраняется на диск"""
        test_db = {"Component1": "resistors"}
        save_component_database(test_db)
        
        # Проверяем что файл существует
        db_path = mock_component_database
        assert db_path.exists()
        
        # Проверяем содержимое файла
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data == test_db
    
    def test_database_json_format(self, mock_component_database):
        """Тест что база сохраняется в правильном JSON формате"""
        test_db = {
            "Резистор": "resistors",
            "Конденсатор": "capacitors"
        }
        save_component_database(test_db)
        
        # Читаем как текст
        db_path = mock_component_database
        with open(db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем что это валидный JSON с кириллицей
        assert "Резистор" in content
        assert "Конденсатор" in content
        assert "\\u" not in content  # Не должно быть escape последовательностей


class TestDatabaseIntegration:
    """Интеграционные тесты базы данных"""
    
    def test_database_grows_with_classifications(self, mock_component_database):
        """Тест что база растет при классификациях"""
        save_component_database({})
        
        # Имитируем несколько классификаций
        components = [
            ("Резистор 100 Ом", "resistors"),
            ("Конденсатор 100 нФ", "capacitors"),
            ("Микросхема IC1", "ics")
        ]
        
        for name, category in components:
            add_component_to_database(name, category)
        
        db = load_component_database()
        assert len(db) == 3
    
    def test_database_survives_reload(self, mock_component_database):
        """Тест что база сохраняется между перезагрузками"""
        # Первая сессия
        save_component_database({})
        add_component_to_database("Component1", "resistors")
        
        # "Перезагрузка" - загружаем заново
        db = load_component_database()
        
        assert "Component1" in db
        assert db["Component1"] == "resistors"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
