"""
Модуль для работы с базой данных компонентов
База данных содержит точные соответствия наименований компонентов и их категорий

Структура базы данных (JSON) с блокчейн-подобным версионированием:
{
    "metadata": {
        "version": "1.5",  # Двузначная версия
        "created": "2025-11-01",
        "last_updated": "2025-11-08 15:30:45",
        "total_components": 100,
        "description": "База данных компонентов для BOM классификатора",
        "previous_hash": "abc123...",  # SHA256 хэш предыдущей версии
        "current_hash": "def456..."    # SHA256 хэш текущей версии
    },
    "history": [
        {
            "version": "1.5",
            "timestamp": "2025-11-08 15:30:45",
            "action": "import_from_file",  # или "manual_add", "import_from_excel"
            "source": "input_file.xlsx",
            "components_added": 5,
            "component_names": ["Резистор...", "Конденсатор..."],
            "previous_hash": "abc123...",
            "current_hash": "def456..."
        }
    ],
    "categories": {
        "resistors": "Резисторы",
        "capacitors": "Конденсаторы",
        ...
    },
    "components": {
        "Резистор С2-29В-0.125 100 Ом": "resistors",
        "1594ТЛ2Т": "ics",
        ...
    }
}
"""

import json
import os
import shutil
import hashlib
import sys
from typing import Optional, Dict, List
from datetime import datetime

from openpyxl.utils import get_column_letter


def safe_print(message: str):
    """
    Безопасный вывод сообщений с эмодзи в консоль.
    Обрабатывает ошибки кодировки на Windows.
    """
    try:
        print(message)
    except UnicodeEncodeError:
        # Заменяем эмодзи на ASCII символы для консолей, не поддерживающих UTF-8
        safe_message = message.replace("✅", "[OK]").replace("❌", "[ERROR]").replace("⚠️", "[WARNING]")
        try:
            print(safe_message)
        except:
            # В крайнем случае выводим в stderr
            sys.stderr.write(safe_message + "\n")


# Путь к файлу базы данных (в папке с данными пользователя)
def get_database_path() -> str:
    r"""
    Получить путь к файлу базы данных компонентов
    
    База данных хранится в отдельной пользовательской папке,
    которая НЕ удаляется при деинсталляции программы.
    
    Расположение:
    - Windows: C:\Users\USERNAME\AppData\Roaming\BOMCategorizer\Data\component_database.json
    - Режим разработки: рядом с проектом (component_database.json)
    """
    import os
    import sys
    
    # Определяем, запущена ли программа из установленной версии или из проекта
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)  # Выходим из bom_categorizer
    
    # Проверяем наличие маркера установленной версии
    installed_marker = os.path.join(parent_dir, ".installed")
    
    if os.path.exists(installed_marker):
        # Установленная версия - используем папку пользовательских данных
        if sys.platform == "win32":
            # Windows: %APPDATA%\BOMCategorizer\Data
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            data_dir = os.path.join(appdata, 'BOMCategorizer', 'Data')
        else:
            # Linux/Mac: ~/.local/share/BOMCategorizer/Data
            data_dir = os.path.expanduser('~/.local/share/BOMCategorizer/Data')
        
        # Создаем папку если её нет
        os.makedirs(data_dir, exist_ok=True)
        
        return os.path.join(data_dir, "component_database.json")
    else:
        # Режим разработки - сохраняем в папке data/
        return os.path.join(parent_dir, "data", "component_database.json")


# Названия категорий (должны совпадать с RUS_SHEET_NAMES в excel_writer.py!)
CATEGORY_NAMES = {
    "resistors": "Резисторы",
    "capacitors": "Конденсаторы",
    "inductors": "Индуктивности",
    "ics": "Микросхемы",
    "semiconductors": "Полупроводники",
    "connectors": "Разъемы",
    "dev_boards": "Отладочные платы",
    "optics": "Оптические компоненты",
    "rf_modules": "СВЧ модули",
    "cables": "Кабели",
    "power_modules": "Модули питания",
    "our_developments": "Наши разработки",
    "others": "Другие",
    "unclassified": "Не распределено",
    "non_bom": "Не ИВП"
}


def _calculate_database_hash(components: Dict[str, str]) -> str:
    """
    Вычисляет SHA256 хэш базы данных компонентов
    
    Args:
        components: Словарь компонентов
        
    Returns:
        Hexadecimal строка хэша
    """
    # Сортируем компоненты для стабильного хэша
    sorted_items = sorted(components.items())
    data_str = json.dumps(sorted_items, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()[:16]  # Первые 16 символов


def _increment_version(current_version: str, manual_add: bool = False) -> str:
    """
    Инкрементирует версию БД (формат X.Y)
    
    Args:
        current_version: Текущая версия (например "1.5")
        manual_add: True если ручное добавление (увеличивает Y), False если из файла (увеличивает X)
        
    Returns:
        Новая версия (например "2.5" если из файла, или "1.6" если ручное)
    """
    try:
        # Обработка формата Build N (старый формат)
        if 'Build' in current_version:
            build_str = current_version.replace('Build', '').strip()
            build_num = int(build_str)
            # Конвертируем в новый формат X.Y
            if manual_add:
                return "1.1"  # Первое ручное добавление после конвертации
            else:
                return "2.0"  # Первый импорт из файла после конвертации
        
        # Обработка формата X.Y
        if '.' in current_version:
            parts = current_version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            
            # Специальная обработка версии 0.0 (пустая база после очистки)
            if major == 0 and minor == 0:
                if manual_add:
                    # Первое ручное добавление: 0.0 → 0.1
                    return "0.1"
                else:
                    # Первый импорт из файла: 0.0 → 1.0
                    return "1.0"
            
            if manual_add:
                # Ручное добавление - увеличиваем Y
                minor += 1
            else:
                # Импорт из файла - увеличиваем X, сбрасываем Y
                major += 1
                minor = 0
            
            return f"{major}.{minor}"
        
        # Пытаемся распарсить как число
        num = int(current_version)
        if manual_add:
            return f"1.{num + 1}"
        else:
            return f"{num + 1}.0"
    except:
        return "1.0"


def set_database_version(new_version: str) -> bool:
    """
    Устанавливает версию БД вручную
    
    Args:
        new_version: Новая версия в формате "X.Y"
        
    Returns:
        True если успешно, False в случае ошибки
    """
    db_path = get_database_path()
    
    # Проверяем формат версии
    if not new_version or '.' not in new_version:
        safe_print(f"❌ Неверный формат версии: {new_version}. Ожидается формат X.Y")
        return False
    
    try:
        parts = new_version.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        
        if major < 0 or minor < 0:
            safe_print(f"❌ Версия должна быть >= 0.0")
            return False
        
        # Загружаем базу данных
        if not os.path.exists(db_path):
            safe_print(f"❌ База данных не найдена")
            return False
        
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        old_version = data.get("metadata", {}).get("version", "1.0")
        
        # Обновляем версию
        data["metadata"]["version"] = new_version
        data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Добавляем запись в историю
        history_entry = {
            "version": new_version,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "manual_version_change",
            "components_added": 0,
            "source": f"Ручная смена версии: {old_version} → {new_version}",
            "previous_hash": data["metadata"].get("current_hash", ""),
            "current_hash": data["metadata"].get("current_hash", ""),
            "component_names": []
        }
        
        if "history" not in data:
            data["history"] = []
        data["history"].insert(0, history_entry)
        
        # Сохраняем
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        safe_print(f"✅ Версия БД изменена: {old_version} → {new_version}")
        return True
        
    except Exception as e:
        safe_print(f"❌ Ошибка при изменении версии: {e}")
        return False


def _add_history_entry(structured_db: dict, action: str, source: Optional[str] = None, 
                       components_added: int = 0, component_names: List[str] = None) -> None:
    """
    Добавляет запись в историю изменений БД
    
    Args:
        structured_db: Структурированная БД
        action: Тип действия (manual_add, import_from_file, import_from_excel)
        source: Источник данных (имя файла)
        components_added: Количество добавленных компонентов
        component_names: Список названий добавленных компонентов
    """
    if "history" not in structured_db:
        structured_db["history"] = []
    
    # Ограничиваем количество имен компонентов в истории
    if component_names and len(component_names) > 10:
        component_names = component_names[:10] + [f"... и еще {len(component_names) - 10}"]
    
    history_entry = {
        "version": structured_db["metadata"]["version"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "components_added": components_added,
        "previous_hash": structured_db["metadata"].get("previous_hash", ""),
        "current_hash": structured_db["metadata"]["current_hash"]
    }
    
    if source:
        history_entry["source"] = source
    
    if component_names:
        history_entry["component_names"] = component_names
    
    structured_db["history"].insert(0, history_entry)  # Добавляем в начало (новые первые)
    
    # Ограничиваем историю последними 50 записями
    if len(structured_db["history"]) > 50:
        structured_db["history"] = structured_db["history"][:50]


def load_component_database() -> Dict[str, str]:
    """
    Загружает базу данных компонентов
    
    Returns:
        Словарь {наименование_компонента: категория}
    """
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        # Создать начальную базу с известными компонентами
        initial_components = {
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
        
        # Создаем структурированную базу с хэшами
        initial_hash = _calculate_database_hash(initial_components)
        structured_db = {
            "metadata": {
                "version": "1.0",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_components": len(initial_components),
                "description": "База данных компонентов для BOM классификатора",
                "previous_hash": "",  # Первая версия, нет предыдущего хэша
                "current_hash": initial_hash
            },
            "history": [{
                "version": "1.0",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": "initial_creation",
                "components_added": len(initial_components),
                "previous_hash": "",
                "current_hash": initial_hash
            }],
            "categories": CATEGORY_NAMES,
            "components": initial_components
        }
        
        _save_structured_database(structured_db)
        safe_print(f"✅ Создана база данных компонентов: {db_path}")
        print(f"   Начальных записей: {len(initial_components)}")
        return initial_components
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Проверяем формат базы данных
            if isinstance(data, dict):
                # Новый формат с метаданными
                if "components" in data:
                    # Проверяем и конвертируем трехзначную версию в двухзначную
                    if "metadata" in data:
                        old_version = data["metadata"].get("version", "1.0")
                        if old_version.count('.') == 2:  # Формат X.Y.Z
                            parts = old_version.split('.')
                            new_version = f"{parts[0]}.{parts[1]}"  # X.Y
                            data["metadata"]["version"] = new_version
                            _save_structured_database(data)
                            print(f"🔄 Версия БД конвертирована: {old_version} → {new_version}")
                    return data["components"]
                # Старый формат (простой словарь)
                elif "metadata" not in data and "categories" not in data:
                    # Конвертируем старый формат в новый с хэшами
                    print("🔄 Обнаружен старый формат базы данных, конвертирую в новый формат с версионированием...")
                    current_hash = _calculate_database_hash(data)
                    structured_db = {
                        "metadata": {
                            "version": "1.0",
                            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "total_components": len(data),
                            "description": "База данных компонентов для BOM классификатора (конвертирована из старого формата)",
                            "previous_hash": "",
                            "current_hash": current_hash
                        },
                        "history": [{
                            "version": "1.0",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "action": "conversion_from_old_format",
                            "components_added": len(data),
                            "previous_hash": "",
                            "current_hash": current_hash
                        }],
                        "categories": CATEGORY_NAMES,
                        "components": data
                    }
                    _save_structured_database(structured_db)
                    safe_print(f"✅ База данных обновлена до нового формата с версионированием")
                    return data
            
            return {}
    except Exception as e:
        safe_print(f"⚠️ Ошибка чтения базы данных компонентов: {e}")
        return {}


def _save_structured_database(structured_db: dict) -> None:
    """
    Внутренняя функция для сохранения структурированной базы данных
    
    Args:
        structured_db: Полная структура базы данных с метаданными
    """
    db_path = get_database_path()
    
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(structured_db, f, ensure_ascii=False, indent=2, sort_keys=False)
    except Exception as e:
        safe_print(f"⚠️ Ошибка сохранения базы данных компонентов: {e}")


def save_component_database(database: Dict[str, str], action: str = "update", 
                            source: Optional[str] = None, component_names: List[str] = None) -> None:
    """
    Сохраняет базу данных компонентов (с автоматическим обновлением метаданных, версии и хэшей)
    
    Args:
        database: Словарь {наименование_компонента: категория}
        action: Тип действия (update, import_from_file, import_from_excel, manual_add)
        source: Источник данных (имя файла)
        component_names: Список названий добавленных компонентов
    """
    db_path = get_database_path()
    
    # Загружаем текущую структуру или создаем новую
    try:
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "metadata" in data:
                    structured_db = data
                else:
                    # Старый формат - создаем новую структуру с хэшами
                    old_hash = _calculate_database_hash(data) if data else ""
                    structured_db = {
                        "metadata": {
                            "version": "1.0",
                            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "total_components": 0,
                            "description": "База данных компонентов для BOM классификатора",
                            "previous_hash": "",
                            "current_hash": old_hash
                        },
                        "history": [],
                        "categories": CATEGORY_NAMES,
                        "components": data if data else {}
                    }
        else:
            structured_db = {
                "metadata": {
                    "version": "1.0",
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_components": 0,
                    "description": "База данных компонентов для BOM классификатора",
                    "previous_hash": "",
                    "current_hash": ""
                },
                "history": [],
                "categories": CATEGORY_NAMES,
                "components": {}
            }
    except Exception as e:
        safe_print(f"⚠️ Ошибка загрузки базы данных: {e}")
        return
    
    # Вычисляем количество добавленных компонентов
    old_components = structured_db.get("components", {})
    components_added = len(database) - len(old_components)
    
    # Вычисляем хэши для проверки изменений
    previous_hash = structured_db["metadata"].get("current_hash", "")
    new_hash = _calculate_database_hash(database)
    
    # Если хэш изменился (реальные изменения в данных), обновляем версию
    if previous_hash != new_hash and new_hash:
        # Инкрементируем версию
        old_version = structured_db["metadata"].get("version", "1.0")
        # Определяем тип инкремента: manual_add если ручное добавление, иначе импорт из файла
        is_manual_add = (action == "manual_add")
        new_version = _increment_version(old_version, manual_add=is_manual_add)
        
        # Обновляем метаданные
        structured_db["metadata"]["version"] = new_version
        structured_db["metadata"]["previous_hash"] = previous_hash
        structured_db["metadata"]["current_hash"] = new_hash
    
    # Обновляем компоненты и метаданные (всегда)
    structured_db["components"] = database
    structured_db["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    structured_db["metadata"]["total_components"] = len(database)
    
    # Добавляем запись в историю если были добавлены новые компоненты
    if components_added > 0:
        _add_history_entry(structured_db, action, source, components_added, component_names)
    
    # Сохраняем
    _save_structured_database(structured_db)


def add_component_to_database(component_name: str, category: str, source: Optional[str] = None) -> None:
    """
    Добавляет компонент в базу данных с обновлением версии и истории
    
    Args:
        component_name: Наименование компонента
        category: Категория компонента
        source: Источник данных (имя файла)
    """
    if not component_name or not category:
        return
    
    db = load_component_database()
    
    # Нормализуем наименование (убираем лишние пробелы)
    component_name = component_name.strip()
    
    # Добавляем только если категория изменилась или компонента нет в базе
    if component_name not in db or db[component_name] != category:
        db[component_name] = category
        # Передаем информацию о добавляемом компоненте
        action = "import_from_file" if source else "manual_add"
        save_component_database(db, action=action, source=source, component_names=[component_name])
        safe_print(f"✅ Добавлено в базу: {component_name} → {category}")


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
    
    # 1. Точное совпадение
    if component_name in db:
        return db[component_name]
    
    # 2. Поиск без учета регистра
    component_lower = component_name.lower()
    for name, category in db.items():
        if name.lower() == component_lower:
            return category
    
    # 3. Поиск без учета пробелов (для компонентов типа "Р1-12" vs "Р 1-12")
    component_no_spaces = component_name.replace(" ", "").lower()
    for name, category in db.items():
        if name.replace(" ", "").lower() == component_no_spaces:
            return category
    
    # 4. Поиск без учета дефисов и пробелов (для "Р1-12" vs "Р112" vs "Р 1 12")
    component_normalized = component_name.replace(" ", "").replace("-", "").lower()
    for name, category in db.items():
        if name.replace(" ", "").replace("-", "").lower() == component_normalized:
            return category
    
    return None


def get_database_history() -> List[dict]:
    """
    Получает историю изменений базы данных
    
    Returns:
        Список записей истории (последние N записей)
    """
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        return []
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("history", [])
    except Exception as e:
        safe_print(f"⚠️ Ошибка чтения истории БД: {e}")
        return []


def format_history_tooltip() -> str:
    """
    Форматирует историю БД для показа в tooltip
    
    Returns:
        Отформатированная строка с историей изменений
    """
    history = get_database_history()
    
    if not history:
        return "История изменений пуста"
    
    # Ограничиваем количество записей в tooltip
    recent_history = history[:10]
    
    lines = ["📜 ИСТОРИЯ ИЗМЕНЕНИЙ БД:\n"]
    
    action_names = {
        "initial_creation": "Создание БД",
        "conversion_from_old_format": "Конвертация из старого формата",
        "manual_add": "Ручное добавление",
        "import_from_file": "Импорт из файла",
        "import_from_excel": "Импорт из Excel",
        "update": "Обновление"
    }
    
    for i, entry in enumerate(recent_history, 1):
        version = entry.get("version", "?")
        timestamp = entry.get("timestamp", "")
        action = action_names.get(entry.get("action", ""), entry.get("action", ""))
        added = entry.get("components_added", 0)
        source = entry.get("source", "")
        prev_hash = entry.get("previous_hash", "")[:8]
        curr_hash = entry.get("current_hash", "")[:8]
        
        lines.append(f"\n{i}. v{version} ({timestamp})")
        lines.append(f"   Действие: {action}")
        lines.append(f"   Добавлено: {added} компонент(ов)")
        
        if source:
            lines.append(f"   Источник: {source}")
        
        if prev_hash and curr_hash:
            lines.append(f"   Хэш: {prev_hash} → {curr_hash}")
        
        # Показываем первые несколько компонентов
        component_names = entry.get("component_names", [])
        if component_names:
            lines.append(f"   Компоненты: {', '.join(component_names[:3])}")
            if len(component_names) > 3:
                lines.append(f"   ... и еще {len(component_names) - 3}")
    
    if len(history) > 10:
        lines.append(f"\n... и еще {len(history) - 10} записей")
    
    return '\n'.join(lines)


def clear_database() -> bool:
    """
    Очищает базу данных компонентов (создает новую пустую базу)
    
    Returns:
        True если очистка успешна, False в случае ошибки
    """
    db_path = get_database_path()
    
    try:
        # Создаем резервную копию перед очисткой
        if os.path.exists(db_path):
            backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"component_database_before_clear_{timestamp}.json")
            shutil.copy2(db_path, backup_path)
            safe_print(f"✅ Резервная копия создана: {backup_path}")
        
        # Создаем новую пустую базу
        empty_db = {
            "metadata": {
                "version": "0.0",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_components": 0,
                "description": "База данных компонентов для BOM классификатора",
                "previous_hash": "",
                "current_hash": ""
            },
            "components": {},
            "history": [
                {
                    "version": "0.0",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "database_cleared",
                    "components_added": 0,
                    "source": "manual_clear",
                    "previous_hash": "",
                    "current_hash": "",
                    "component_names": []
                }
            ]
        }
        
        # Сохраняем пустую базу
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(empty_db, f, ensure_ascii=False, indent=2)
        
        safe_print(f"✅ База данных очищена: {db_path}")
        return True
        
    except Exception as e:
        safe_print(f"❌ Ошибка при очистке базы данных: {e}")
        return False


def get_database_stats() -> dict:
    """
    Получает расширенную статистику по базе данных
    
    Returns:
        Словарь со статистикой и метаданными
    """
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        return {
            'metadata': {},
            'total': 0,
            'by_category': {}
        }
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Новый формат с метаданными
            if "components" in data:
                components = data["components"]
                metadata = data.get("metadata", {})
            else:
                # Старый формат
                components = data
                metadata = {}
            
            stats = {
                'metadata': metadata,
                'total': len(components),
                'by_category': {},
                'category_names': CATEGORY_NAMES
            }
            
            for category in components.values():
                if category not in stats['by_category']:
                    stats['by_category'][category] = 0
                stats['by_category'][category] += 1
            
            return stats
    except Exception as e:
        safe_print(f"⚠️ Ошибка получения статистики: {e}")
        return {
            'metadata': {},
            'total': 0,
            'by_category': {}
        }


def export_database_to_excel(output_path: str = "component_database_export.xlsx") -> bool:
    """
    Экспортирует базу данных в Excel для редактирования
    
    Args:
        output_path: Путь к выходному файлу
        
    Returns:
        True если успешно, False при ошибке
    """
    try:
        import pandas as pd
        
        db = load_component_database()
        
        if not db:
            print("⚠️ База данных пуста")
            return False
        
        # Создаем DataFrame
        data = []
        for component, category in sorted(db.items()):
            category_name = CATEGORY_NAMES.get(category, category)
            data.append({
                'Наименование компонента': component,
                'Категория (ключ)': category,
                'Категория (название)': category_name
            })
        
        df = pd.DataFrame(data)
        
        # Получаем метаданные
        stats = get_database_stats()
        metadata = stats.get('metadata', {})
        
        # Создаем лист с метаданными
        meta_data = []
        meta_data.append(['Версия базы данных', metadata.get('version', 'Неизвестно')])
        meta_data.append(['Дата создания', metadata.get('created', 'Неизвестно')])
        meta_data.append(['Последнее обновление', metadata.get('last_updated', 'Неизвестно')])
        meta_data.append(['Всего компонентов', len(db)])
        meta_data.append(['Описание', metadata.get('description', '')])
        meta_data.append(['', ''])
        meta_data.append(['Категория (ключ)', 'Категория (название)', 'Количество'])
        
        for cat_key, cat_name in sorted(CATEGORY_NAMES.items()):
            count = stats['by_category'].get(cat_key, 0)
            if count > 0:
                meta_data.append([cat_key, cat_name, count])
        
        meta_df = pd.DataFrame(meta_data)
        
        # Сохраняем в Excel с двумя листами
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            meta_df.to_excel(writer, sheet_name='Информация', index=False, header=False)
            df.to_excel(writer, sheet_name='Компоненты', index=False)

            workbook = writer.book
            info_sheet = writer.sheets['Информация']
            components_sheet = writer.sheets['Компоненты']

            def adjust_sheet_columns(ws, dataframe, include_header=True, min_width=12, max_width=80, extra_padding=4):
                """
                Автоматическая подстройка ширины столбцов под содержимое DataFrame.
                """
                if dataframe is None or dataframe.shape[1] == 0:
                    return

                # Перебираем все столбцы DataFrame
                for col_idx in range(dataframe.shape[1]):
                    column_letter = get_column_letter(col_idx + 1)
                    max_length = 0

                    # Учитываем заголовок
                    if include_header:
                        header_value = str(dataframe.columns[col_idx])
                        if header_value and header_value != 'None':
                            max_length = len(header_value)

                    # Учитываем содержимое ячеек
                    for cell_value in dataframe.iloc[:, col_idx]:
                        if pd.isna(cell_value):
                            cell_text = ""
                        else:
                            cell_text = str(cell_value)

                        if len(cell_text) > max_length:
                            max_length = len(cell_text)

                    # Применяем ограничения и отступ
                    desired_width = max_length + extra_padding
                    desired_width = max(min_width, min(desired_width, max_width))

                    ws.column_dimensions[column_letter].width = desired_width

            # Настраиваем ширины столбцов для обоих листов
            adjust_sheet_columns(info_sheet, meta_df, include_header=False, min_width=16, max_width=80, extra_padding=6)
            adjust_sheet_columns(components_sheet, df, include_header=True, min_width=20, max_width=80, extra_padding=6)

            # Немного увеличим высоту первой строки листа "Компоненты" для header
            components_sheet.row_dimensions[1].height = 24
        
        safe_print(f"✅ База данных экспортирована: {output_path}")
        print(f"   Компонентов: {len(db)}")
        return True
        
    except Exception as e:
        safe_print(f"❌ Ошибка экспорта базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False


def backup_database() -> str:
    """
    Создает резервную копию базы данных
    
    Returns:
        str: Путь к созданному файлу резервной копии
        
    Raises:
        Exception: При ошибке создания резервной копии
    """
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"База данных не найдена: {db_path}")
    
    # Определяем папку для резервных копий
    backup_dir = os.path.join(os.path.dirname(db_path), "database_backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Генерируем имя файла с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"component_database_backup_{timestamp}.json"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Копируем файл
    import shutil
    shutil.copy2(db_path, backup_path)
    
    return backup_path


def import_database_from_excel(input_path: str, replace: bool = False) -> int:
    """
    Импортирует базу данных из Excel
    
    Args:
        input_path: Путь к файлу Excel
        replace: Если True - заменяет всю базу, False - объединяет с существующей
        
    Returns:
        int: Количество импортированных компонентов
        
    Raises:
        Exception: При ошибке импорта
    """
    import pandas as pd
    
    # Читаем лист с компонентами
    df = pd.read_excel(input_path, sheet_name='Компоненты', engine='openpyxl')
    
    if 'Наименование компонента' not in df.columns or 'Категория (ключ)' not in df.columns:
        raise ValueError("Неверный формат файла. Требуются колонки: 'Наименование компонента' и 'Категория (ключ)'")
    
    # Загружаем текущую базу если нужно объединить
    if not replace:
        current_db = load_component_database()
    else:
        current_db = {}
    
    # Импортируем компоненты
    imported_count = 0
    component_names = []
    for _, row in df.iterrows():
        component = str(row['Наименование компонента']).strip()
        category = str(row['Категория (ключ)']).strip()
        
        if component and category and category != 'nan':
            current_db[component] = category
            component_names.append(component)
            imported_count += 1
    
    # Сохраняем с полным путем к файлу-источнику
    save_component_database(
        current_db, 
        action="import_from_excel",
        source=os.path.abspath(input_path),
        component_names=component_names[:50]  # Первые 50 для истории
    )
    
    return imported_count


def is_first_run() -> bool:
    """
    Проверяет, является ли это первым запуском (пустая или почти пустая БД)
    
    Returns:
        True если это первый запуск (БД пустая или содержит <= 10 компонентов)
    """
    db_path = get_database_path()
    
    # Если файла БД нет - это первый запуск
    if not os.path.exists(db_path):
        return True
    
    # Загружаем БД и проверяем количество компонентов
    try:
        components = load_component_database()
        # Считаем первым запуском если компонентов 10 или меньше
        return len(components) <= 10
    except Exception:
        return True


def initialize_database_from_template():
    """
    Инициализирует БД из шаблона при первом запуске
    Копирует component_database_template.json в рабочую БД
    """
    db_path = get_database_path()
    
    # Если БД уже есть - ничего не делаем
    if os.path.exists(db_path):
        return
    
    # Ищем шаблон БД
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    template_path = os.path.join(parent_dir, "component_database_template.json")
    
    if os.path.exists(template_path):
        # Копируем шаблон
        import shutil
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        shutil.copy2(template_path, db_path)
        safe_print(f"✅ Инициализирована БД из шаблона: {db_path}")
    else:
        # Если шаблона нет - создаем пустую БД
        structured_db = {
            "metadata": {
                "version": "1.0.0",
                "created": datetime.now().strftime("%Y-%m-%d"),
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "total_components": 0,
                "description": "База данных компонентов для BOM классификатора"
            },
            "categories": CATEGORY_NAMES,
            "components": {}
        }
        _save_structured_database(structured_db)
        safe_print(f"✅ Создана пустая БД: {db_path}")
