#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Инструмент управления базой данных компонентов

Функции:
- Просмотр статистики базы данных
- Экспорт базы данных в Excel
- Импорт базы данных из Excel
- Очистка базы данных
- Резервное копирование и восстановление

Использование:
    python manage_database.py --stats
    python manage_database.py --export database.xlsx
    python manage_database.py --import database.xlsx
    python manage_database.py --backup
"""

import os
import sys
import argparse
import shutil
from datetime import datetime

# Исправление кодировки для корректного вывода русских символов и эмодзи
if sys.stdout.encoding != 'utf-8':
    try:
        # Python 3.7+ - используем reconfigure если доступен
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        else:
            # Fallback для старых версий Python
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, OSError):
        # Если не удалось изменить кодировку - продолжаем с текущей
        pass

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bom_categorizer.component_database import (
    load_component_database,
    save_component_database,
    get_database_path,
    get_database_stats,
    export_database_to_excel,
    import_database_from_excel,
    add_component_to_database,
    CATEGORY_NAMES
)


def show_stats():
    """Показать статистику базы данных"""
    print("\n" + "="*80)
    print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ КОМПОНЕНТОВ")
    print("="*80)
    
    stats = get_database_stats()
    metadata = stats.get('metadata', {})
    
    print("\n📋 МЕТАДАННЫЕ:")
    print(f"   Версия:              {metadata.get('version', 'Неизвестно')}")
    print(f"   Дата создания:       {metadata.get('created', 'Неизвестно')}")
    print(f"   Последнее обновление: {metadata.get('last_updated', 'Неизвестно')}")
    print(f"   Описание:            {metadata.get('description', 'Нет описания')}")
    
    print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего компонентов:   {stats['total']}")
    print(f"   Всего категорий:     {len(CATEGORY_NAMES)}")
    
    if stats['by_category']:
        print(f"\n📦 РАСПРЕДЕЛЕНИЕ ПО КАТЕГОРИЯМ:")
        # Сортируем по количеству (по убыванию)
        sorted_categories = sorted(
            stats['by_category'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for cat_key, count in sorted_categories:
            cat_name = CATEGORY_NAMES.get(cat_key, cat_key)
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            bar = "█" * int(percentage / 2)
            print(f"   {cat_name:40s} {count:5d} ({percentage:5.1f}%) {bar}")
    else:
        print("\n   База данных пуста")
    
    print("\n" + "="*80)


def export_database(output_path: str):
    """Экспортировать базу данных в Excel"""
    print("\n" + "="*80)
    print("📤 ЭКСПОРТ БАЗЫ ДАННЫХ")
    print("="*80)
    print(f"Выходной файл: {output_path}")
    
    if export_database_to_excel(output_path):
        print("\n✅ Экспорт завершен успешно!")
        print(f"\nТеперь вы можете:")
        print(f"  1. Открыть файл в Excel: {output_path}")
        print(f"  2. Редактировать компоненты на листе 'Компоненты'")
        print(f"  3. Импортировать обратно: python manage_database.py --import \"{output_path}\"")
    else:
        print("\n❌ Ошибка экспорта")
    
    print("="*80 + "\n")


def import_database(input_path: str, merge: bool = True):
    """Импортировать базу данных из Excel"""
    print("\n" + "="*80)
    print("📥 ИМПОРТ БАЗЫ ДАННЫХ")
    print("="*80)
    print(f"Входной файл: {input_path}")
    print(f"Режим: {'Объединение' if merge else 'Замена'}")
    
    if not os.path.exists(input_path):
        print(f"\n❌ Файл не найден: {input_path}")
        print("="*80 + "\n")
        return
    
    # Показываем текущую статистику
    print("\n📊 До импорта:")
    current_stats = get_database_stats()
    print(f"   Компонентов в базе: {current_stats['total']}")
    
    # Импортируем
    if import_database_from_excel(input_path, merge):
        print("\n✅ Импорт завершен успешно!")
        
        # Показываем новую статистику
        print("\n📊 После импорта:")
        new_stats = get_database_stats()
        print(f"   Компонентов в базе: {new_stats['total']}")
        
        if merge:
            added = new_stats['total'] - current_stats['total']
            print(f"   Добавлено: {added}")
    else:
        print("\n❌ Ошибка импорта")
    
    print("="*80 + "\n")


def backup_database():
    """Создать резервную копию базы данных"""
    print("\n" + "="*80)
    print("💾 РЕЗЕРВНОЕ КОПИРОВАНИЕ")
    print("="*80)
    
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        print("❌ База данных не существует")
        print("="*80 + "\n")
        return
    
    # Создаем папку для бэкапов если её нет
    # Резервные копии всегда в той же папке, где и база данных
    backup_dir = os.path.join(os.path.dirname(db_path), "database_backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Формируем имя файла с датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"component_database_backup_{timestamp}.json"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Резервная копия создана:")
        print(f"   {backup_path}")
        
        # Показываем статистику
        stats = get_database_stats()
        print(f"\n📊 Скопировано компонентов: {stats['total']}")
        
        # Показываем список всех бэкапов
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.json')])
        if len(backups) > 1:
            print(f"\n📁 Всего резервных копий: {len(backups)}")
            print("   Последние 5:")
            for backup in backups[-5:]:
                backup_full_path = os.path.join(backup_dir, backup)
                size = os.path.getsize(backup_full_path) / 1024
                print(f"     - {backup} ({size:.1f} KB)")
        
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
    
    print("="*80 + "\n")


def restore_database(backup_path: str):
    """Восстановить базу данных из резервной копии"""
    print("\n" + "="*80)
    print("♻️  ВОССТАНОВЛЕНИЕ ИЗ РЕЗЕРВНОЙ КОПИИ")
    print("="*80)
    
    if not os.path.exists(backup_path):
        print(f"❌ Файл резервной копии не найден: {backup_path}")
        print("="*80 + "\n")
        return
    
    db_path = get_database_path()
    
    # Спрашиваем подтверждение
    print(f"⚠️  ВНИМАНИЕ! Текущая база данных будет заменена!")
    print(f"   Источник: {backup_path}")
    print(f"   Назначение: {db_path}")
    
    response = input("\nПродолжить? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено пользователем")
        print("="*80 + "\n")
        return
    
    try:
        # Создаем автоматический бэкап текущей базы перед восстановлением
        if os.path.exists(db_path):
            print("\n💾 Создаю резервную копию текущей базы перед восстановлением...")
            backup_database()
        
        # Восстанавливаем
        shutil.copy2(backup_path, db_path)
        print(f"\n✅ База данных восстановлена из резервной копии")
        
        # Показываем статистику
        stats = get_database_stats()
        print(f"\n📊 Восстановлено компонентов: {stats['total']}")
        
    except Exception as e:
        print(f"❌ Ошибка восстановления: {e}")
    
    print("="*80 + "\n")


def clear_database(keep_backup: bool = True):
    """Очистить базу данных"""
    print("\n" + "="*80)
    print("🗑️  ОЧИСТКА БАЗЫ ДАННЫХ")
    print("="*80)
    
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        print("❌ База данных не существует")
        print("="*80 + "\n")
        return
    
    # Показываем текущую статистику
    stats = get_database_stats()
    print(f"\n⚠️  ВНИМАНИЕ! Будут удалены все компоненты из базы данных!")
    print(f"   Текущее количество: {stats['total']} компонентов")
    
    response = input("\nПродолжить? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'да', 'д']:
        print("❌ Отменено пользователем")
        print("="*80 + "\n")
        return
    
    try:
        # Создаем резервную копию перед очисткой
        if keep_backup:
            print("\n💾 Создаю резервную копию перед очисткой...")
            backup_database()
        
        # Очищаем базу данных (сохраняем пустой словарь)
        save_component_database({})
        print(f"\n✅ База данных очищена")
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
    
    print("="*80 + "\n")


def import_from_output(output_file: str):
    """
    Импортировать компоненты из выходного Excel файла в базу данных
    Читает все листы категорий и добавляет компоненты с их категориями
    """
    print("\n" + "="*80)
    print("📥 ИМПОРТ ИЗ ВЫХОДНОГО ФАЙЛА")
    print("="*80)
    print(f"Файл: {output_file}")
    
    if not os.path.exists(output_file):
        print(f"\n❌ Файл не найден: {output_file}")
        print("="*80 + "\n")
        return
    
    try:
        import pandas as pd
        
        # Маппинг русских названий листов на ключи категорий
        SHEET_TO_CATEGORY = {
            'Резисторы': 'resistors',
            'Конденсаторы': 'capacitors',
            'Индуктивности': 'inductors',
            'Полупроводники': 'semiconductors',
            'Микросхемы': 'ics',
            'Разъемы': 'connectors',
            'Оптика': 'optics',
            'СВЧ модули': 'rf_modules',
            'Кабели': 'cables',
            'Модули питания': 'power_modules',
            'Отладочные платы': 'dev_boards',
            'Наши разработки': 'our_developments',
            'Другие': 'others',
        }
        
        # Читаем файл Excel
        xl_file = pd.ExcelFile(output_file, engine='openpyxl')
        
        added_count = 0
        skipped_count = 0
        total_sheets = 0
        
        print("\n📊 Обработка листов:")
        
        # Обрабатываем каждый лист
        for sheet_name in xl_file.sheet_names:
            # Пропускаем служебные листы
            if sheet_name in ['SOURCES', 'SUMMARY', 'Не распределено', 'INFO']:
                continue
            
            # Проверяем что это лист категории
            if sheet_name not in SHEET_TO_CATEGORY:
                continue
            
            category_key = SHEET_TO_CATEGORY[sheet_name]
            total_sheets += 1
            
            # Читаем данные
            df = pd.read_excel(output_file, sheet_name=sheet_name, engine='openpyxl')
            
            if df.empty:
                continue
            
            # Ищем колонку с наименованием
            name_col = None
            for col in ['Наименование ИВП', 'Наименование', 'наименование ивп', 'наименование']:
                if col in df.columns:
                    name_col = col
                    break
            
            if not name_col:
                print(f"   ⚠️  {sheet_name}: не найдена колонка с наименованием")
                continue
            
            sheet_added = 0
            
            # Добавляем каждый компонент в базу данных
            for idx, row in df.iterrows():
                name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
                
                # Пропускаем пустые названия
                if not name or name == 'nan':
                    skipped_count += 1
                    continue
                
                # Добавляем в базу данных
                add_component_to_database(name, category_key)
                added_count += 1
                sheet_added += 1
            
            print(f"   ✅ {sheet_name}: добавлено {sheet_added} компонентов")
        
        print(f"\n✅ Импорт завершен!")
        print(f"\n📈 Статистика:")
        print(f"   Обработано листов: {total_sheets}")
        print(f"   Добавлено компонентов: {added_count}")
        print(f"   Пропущено (пустые): {skipped_count}")
        
        # Показываем обновленную статистику базы данных
        print(f"\n📊 База данных после импорта:")
        stats = get_database_stats()
        print(f"   Всего компонентов: {stats['total']}")
        
    except Exception as e:
        print(f"\n❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*80 + "\n")


def list_backups():
    """Показать список резервных копий"""
    print("\n" + "="*80)
    print("📁 РЕЗЕРВНЫЕ КОПИИ")
    print("="*80)
    
    db_path = get_database_path()
    # Резервные копии всегда в той же папке, где и база данных
    backup_dir = os.path.join(os.path.dirname(db_path), "database_backups")
    
    if not os.path.exists(backup_dir):
        print("\n❌ Папка с резервными копиями не найдена")
        print(f"   {backup_dir}")
        print("="*80 + "\n")
        return
    
    backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.json')])
    
    if not backups:
        print("\n📭 Резервных копий нет")
    else:
        print(f"\n📦 Найдено резервных копий: {len(backups)}")
        print(f"📂 Папка: {backup_dir}\n")
        
        for i, backup in enumerate(backups, 1):
            backup_full_path = os.path.join(backup_dir, backup)
            size = os.path.getsize(backup_full_path) / 1024
            mtime = datetime.fromtimestamp(os.path.getmtime(backup_full_path))
            print(f"   {i:2d}. {backup}")
            print(f"       Размер: {size:.1f} KB")
            print(f"       Дата:   {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
    
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Инструмент управления базой данных компонентов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  Показать статистику:
    python manage_database.py --stats
    
  Экспортировать в Excel:
    python manage_database.py --export database.xlsx
    
  Импортировать из Excel (объединение):
    python manage_database.py --import database.xlsx
    
  Импортировать из Excel (замена):
    python manage_database.py --import database.xlsx --replace
    
  Импортировать из выходного файла:
    python manage_database.py --import-output plata_MKVH_out.xlsx
    
  Создать резервную копию:
    python manage_database.py --backup
    
  Показать резервные копии:
    python manage_database.py --list-backups
    
  Восстановить из резервной копии:
    python manage_database.py --restore database_backups/component_database_backup_20251101_120000.json
    
  Очистить базу данных:
    python manage_database.py --clear
        """
    )
    
    parser.add_argument("--stats", action="store_true", help="Показать статистику базы данных")
    parser.add_argument("--export", metavar="FILE", help="Экспортировать базу данных в Excel")
    parser.add_argument("--import", metavar="FILE", dest="import_file", help="Импортировать базу данных из Excel")
    parser.add_argument("--import-output", metavar="FILE", dest="import_output", help="Импортировать компоненты из выходного файла программы")
    parser.add_argument("--replace", action="store_true", help="Заменить базу данных при импорте (по умолчанию: объединение)")
    parser.add_argument("--backup", action="store_true", help="Создать резервную копию базы данных")
    parser.add_argument("--list-backups", action="store_true", help="Показать список резервных копий")
    parser.add_argument("--restore", metavar="FILE", help="Восстановить базу данных из резервной копии")
    parser.add_argument("--clear", action="store_true", help="Очистить базу данных")
    
    args = parser.parse_args()
    
    # Если нет аргументов - показываем справку
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:
        if args.stats:
            show_stats()
        
        if args.export:
            export_database(args.export)
        
        if args.import_file:
            import_database(args.import_file, merge=not args.replace)
        
        if args.import_output:
            import_from_output(args.import_output)
        
        if args.backup:
            backup_database()
        
        if args.list_backups:
            list_backups()
        
        if args.restore:
            restore_database(args.restore)
        
        if args.clear:
            clear_database()
            
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

