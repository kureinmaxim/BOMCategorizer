# -*- coding: utf-8 -*-
"""
Генерация TXT отчетов для категоризованных BOM данных

Основная функция:
- write_txt_reports: создает TXT файлы для каждой категории
"""

import os
from typing import Dict
import pandas as pd

from .excel_writer import RUS_SHEET_NAMES
from .formatters import extract_tu_code, clean_component_name


def write_txt_reports(outputs: Dict[str, pd.DataFrame], txt_dir: str, desc_col: str):
    """
    Создает TXT отчеты для каждой категории
    
    Args:
        outputs: Словарь {category_key: DataFrame}
        txt_dir: Директория для сохранения TXT файлов
        desc_col: Название колонки с описанием
    """
    if not os.path.exists(txt_dir):
        os.makedirs(txt_dir, exist_ok=True)
    
    for key, part_df in outputs.items():
        if len(part_df) == 0:
            continue
        
        category_name = RUS_SHEET_NAMES.get(key, key)
        txt_path = os.path.join(txt_dir, f"{category_name}.txt")
        
        # Подготовить данные для TXT
        output_df = part_df.copy()
        
        # Найти колонку с описанием
        desc_col_candidates = [desc_col, '_merged_description_', 'description', 'Наименование ИВП']
        desc_col_found = None
        for candidate in desc_col_candidates:
            if candidate in output_df.columns:
                desc_col_found = candidate
                break
        
        if not desc_col_found:
            # Если нет колонки с описанием, пропускаем
            continue
        
        # Данные уже очищены и отформатированы в main.py через format_excel_output
        # Колонка ТУ уже должна присутствовать, не нужно извлекать её заново
        
        # Фильтровать строки с пустым описанием
        output_df = output_df[output_df[desc_col_found].notna() & (output_df[desc_col_found].astype(str).str.strip() != '')]
        
        if output_df.empty:
            continue
        
        # Применить ту же сортировку что и в Excel
        category_name = RUS_SHEET_NAMES.get(key, key)
        
        if category_name in ['Конденсаторы', 'Дроссели', 'Резисторы', 'Индуктивности']:
            # Сортировка по номиналу
            from .formatters import extract_nominal_value
            category_map = {
                'Резисторы': 'resistors',
                'Конденсаторы': 'capacitors',
                'Дроссели': 'inductors',
                'Индуктивности': 'inductors',
            }
            category_key = category_map.get(category_name, 'resistors')
            
            def get_nominal_value(text):
                result = extract_nominal_value(str(text), category_key)
                # result может быть tuple (value, unit) или просто значение
                if isinstance(result, tuple):
                    return result[0] if result[0] is not None else float('inf')
                else:
                    return result if result is not None else float('inf')
            
            output_df['_nominal_value'] = output_df[desc_col_found].apply(get_nominal_value)
            output_df = output_df.sort_values(by=['_nominal_value', desc_col_found], ascending=[True, True])
            output_df = output_df.drop(columns=['_nominal_value'])
        
        elif category_name in ['Отладочные платы и модули', 'Модули питания', 'Оптические компоненты',
                               'Полупроводники', 'Разъемы', 'Кабели', 'Другие']:
            # Алфавитная сортировка
            output_df = output_df.sort_values(by=desc_col_found, ascending=True)
        
        # Для остальных категорий - без сортировки
        output_df = output_df.reset_index(drop=True)
        
        # Записать TXT файл
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"=== {category_name.upper()} ===\n")
            f.write(f"Всего элементов: {len(output_df)}\n")
            f.write("=" * 80 + "\n\n")
            
            for idx, (_, row) in enumerate(output_df.iterrows(), start=1):
                name = row[desc_col_found]
                tu = row.get('ТУ', '')
                
                line = f"{idx}. {name}"
                if tu and str(tu).strip() and str(tu).strip() != '-':
                    line += f" | ТУ: {tu}"
                
                f.write(line + "\n")
            
            f.write("\n" + "=" * 80 + "\n")
    
    print(f"TXT files written to: {txt_dir}")
    
    # Создаем отдельный файл для импортных компонентов
    write_imported_components_report(outputs, txt_dir, desc_col)


def write_imported_components_report(outputs: Dict[str, pd.DataFrame], txt_dir: str, desc_col: str):
    """
    Создает отдельный TXT файл со всеми импортными компонентами, сгруппированными по категориям
    
    Args:
        outputs: Словарь {category_key: DataFrame}
        txt_dir: Директория для сохранения TXT файлов
        desc_col: Название колонки с описанием
    """
    import re
    
    # Паттерн российских ТУ-кодов: любое количество букв/цифр . цифры . цифры ТУ (с возможными суффиксами)
    # Примеры: ИУЯР.436610.015ТУ, ОЖ0.348.021ТУ, НЩ0.364.061ТУ/02
    russian_tu_pattern = re.compile(r'^[А-ЯЁ\d]+\.\d+\.\d+ТУ', re.IGNORECASE)
    
    # Собираем все импортные компоненты по категориям
    imported_by_category = {}
    
    for key, part_df in outputs.items():
        if len(part_df) == 0:
            continue
        
        category_name = RUS_SHEET_NAMES.get(key, key)
        
        # Найти колонку с описанием
        desc_col_candidates = [desc_col, '_merged_description_', 'description', 'Наименование ИВП']
        desc_col_found = None
        for candidate in desc_col_candidates:
            if candidate in part_df.columns:
                desc_col_found = candidate
                break
        
        if not desc_col_found:
            continue
        
        # Ищем импортные компоненты (у которых НЕТ российского ТУ-кода)
        imported_items = []
        
        for idx, row in part_df.iterrows():
            tu = str(row.get('ТУ', '')) if pd.notna(row.get('ТУ')) else ""
            name = str(row[desc_col_found]) if pd.notna(row[desc_col_found]) else ""
            
            if not name or not name.strip():
                continue
            
            # Паттерны российских/советских компонентов по ГОСТ
            # Резисторы: Р1-, С2-, НР1-, МЛТ-, СП5- и т.д.
            # Конденсаторы: К10-, К50-, К53-, КМ-, КД- и т.д.
            # Полупроводники: 2Д, 2С, 2Т, КД, КТ и т.д.
            # Микросхемы: 1272, 1564, 140, 249, 286, 5115, 5559 и т.д.
            russian_component_patterns = [
                r'^Р\d+[-\s]',  # Резисторы Р1-, Р2- и т.д.
                r'^С\d+[-\s]',  # Резисторы С2-, С5- и т.д.
                r'^НР\d+[-\s]', # Резисторы НР1- и т.д.
                r'^МЛТ',        # Резисторы МЛТ
                r'^СП\d+',      # Подстроечные СП5
                r'^К\d+[-\s]',  # Конденсаторы К10-, К50-, К53- и т.д.
                r'^КМ[-\s]',    # Конденсаторы КМ
                r'^КД[-\s]',    # Конденсаторы КД
                r'^\d[ДСТ]\d+', # Полупроводники 2Д, 2С, 2Т, КД, КТ
                r'^КД\d+',      # Диоды КД
                r'^КТ\d+',      # Транзисторы КТ
                r'^\d{3,4}[А-ЯЁ]{2}\d', # Микросхемы типа 1272ПН3Т, 140УД17А
            ]
            
            def is_russian_component_by_name(component_name: str) -> bool:
                """Проверяет, является ли компонент российским/советским по названию"""
                if not component_name:
                    return False
                name_upper = component_name.upper()
                for pattern in russian_component_patterns:
                    if re.match(pattern, name_upper, re.IGNORECASE):
                        return True
                return False
            
            # Считаем импортным если:
            # 1. ТУ есть и НЕ соответствует российскому формату (это производитель типа TI, Maxim)
            # 2. ТУ отсутствует И название НЕ соответствует российским/советским стандартам
            is_imported = False
            manufacturer = ""
            
            if not tu or tu.strip() == '' or tu.strip() == '-':
                # ТУ отсутствует - проверяем название компонента
                if is_russian_component_by_name(name):
                    # Название похоже на российский ГОСТ - НЕ импортный
                    is_imported = False
                else:
                    # Название не похоже на российский - импортный
                    is_imported = True
                    manufacturer = "-"
            elif not russian_tu_pattern.match(tu.strip()):
                # ТУ не российского формата - это производитель (импортный)
                is_imported = True
                manufacturer = tu.strip()
            else:
                # ТУ российского формата - отечественный
                is_imported = False
            
            if is_imported:
                # Очищаем название от ТУ если он там есть
                name_clean = clean_component_name(name, "")
                name_clean, _ = extract_tu_code(name_clean)
                
                imported_items.append({
                    'name': name_clean,
                    'manufacturer': manufacturer
                })
        
        if imported_items:
            imported_by_category[category_name] = imported_items
    
    # Записываем файл если есть импортные компоненты
    if imported_by_category:
        txt_path = os.path.join(txt_dir, "Импортные_компоненты.txt")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("=== ИМПОРТНЫЕ КОМПОНЕНТЫ (ИВП) ===\n")
            f.write("=" * 80 + "\n\n")
            
            total_count = sum(len(items) for items in imported_by_category.values())
            f.write(f"Всего импортных компонентов: {total_count}\n")
            f.write(f"Категорий: {len(imported_by_category)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Записываем по категориям
            for category_name, items in sorted(imported_by_category.items()):
                f.write(f"\n>>> {category_name.upper()}\n")
                f.write("-" * 80 + "\n")
                
                for idx, item in enumerate(items, start=1):
                    # Если производитель неизвестен, не пишем его
                    if item['manufacturer'] and item['manufacturer'] != '-':
                        f.write(f"{idx}. {item['name']} | Производитель: {item['manufacturer']}\n")
                    else:
                        f.write(f"{idx}. {item['name']}\n")
                
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write(f"Итого импортных компонентов: {total_count}\n")
        
        print(f"Imported components report written to: {txt_path}")
