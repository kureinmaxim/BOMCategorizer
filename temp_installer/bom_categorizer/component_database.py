"""
Модуль для работы с базой данных компонентов
База данных содержит точные соответствия наименований компонентов и их категорий
"""

import json
import os
from typing import Optional, Dict


# Путь к файлу базы данных (в папке с данными пользователя)
def get_database_path() -> str:
    """Получить путь к файлу базы данных компонентов"""
    # Сохраняем в текущей директории (рядом с rules.json)
    # Используем абсолютный путь для надежности
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)  # Выходим из bom_categorizer
    return os.path.join(parent_dir, "component_database.json")


def load_component_database() -> Dict[str, str]:
    """
    Загружает базу данных компонентов
    
    Returns:
        Словарь {наименование_компонента: категория}
    """
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        # Создать начальную базу с известными компонентами
        initial_db = {
            # Микросхемы
            "1594ТЛ2Т": "ics",
            "HMC435AMS8GE": "ics",
            "HMC742ALP5E": "ics",
            "РАТ-0+": "ics",
            "РАТ-1+": "ics",
            "РАТ-2+": "ics",
            "РАТ-3+": "ics",
            "РАТ-20+": "ics",
            "PE43713A-Z": "ics",
        }
        save_component_database(initial_db)
        print(f"✅ Создана база данных компонентов: {db_path}")
        print(f"   Начальных записей: {len(initial_db)}")
        return initial_db
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
            return db
    except Exception as e:
        print(f"⚠️ Ошибка чтения базы данных компонентов: {e}")
        return {}


def save_component_database(database: Dict[str, str]) -> None:
    """
    Сохраняет базу данных компонентов
    
    Args:
        database: Словарь {наименование_компонента: категория}
    """
    db_path = get_database_path()
    
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения базы данных компонентов: {e}")


def add_component_to_database(component_name: str, category: str) -> None:
    """
    Добавляет компонент в базу данных
    
    Args:
        component_name: Наименование компонента
        category: Категория компонента
    """
    if not component_name or not category:
        return
    
    db = load_component_database()
    
    # Нормализуем наименование (убираем лишние пробелы)
    component_name = component_name.strip()
    
    # Добавляем только если категория изменилась или компонента нет в базе
    if component_name not in db or db[component_name] != category:
        db[component_name] = category
        save_component_database(db)
        print(f"✅ Добавлено в базу: {component_name} → {category}")


def get_component_category(component_name: str) -> Optional[str]:
    """
    Получает категорию компонента из базы данных
    
    Args:
        component_name: Наименование компонента
        
    Returns:
        Категория компонента или None если не найдено
    """
    if not component_name:
        return None
    
    db = load_component_database()
    
    # Нормализуем наименование
    component_name = component_name.strip()
    
    # Точное совпадение
    if component_name in db:
        return db[component_name]
    
    # Поиск без учета регистра
    component_lower = component_name.lower()
    for name, category in db.items():
        if name.lower() == component_lower:
            return category
    
    return None


def get_database_stats() -> dict:
    """
    Получает статистику по базе данных
    
    Returns:
        Словарь со статистикой
    """
    db = load_component_database()
    
    stats = {
        'total': len(db),
        'by_category': {}
    }
    
    for category in db.values():
        if category not in stats['by_category']:
            stats['by_category'][category] = 0
        stats['by_category'][category] += 1
    
    return stats
