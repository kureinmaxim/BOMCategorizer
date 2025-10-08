# -*- coding: utf-8 -*-
"""
Запись категоризованных BOM данных в Excel

Основные функции:
- write_categorized_excel: главная функция записи
- enrich_with_mr_and_total: добавление кодов МР и общих количеств
- format_excel_output: форматирование и сортировка
- apply_excel_styles: применение стилей к ячейкам
"""

import os
import re
from typing import Dict
import pandas as pd
from openpyxl.styles import Alignment

from .formatters import clean_component_name, extract_nominal_value, extract_tu_code
from .utils import find_column


# Русские названия категорий для листов Excel
RUS_SHEET_NAMES = {
    "debug_modules": "Отладочные платы и модули",
    "ics": "Микросхемы",
    "resistors": "Резисторы",
    "capacitors": "Конденсаторы",
    "inductors": "Индуктивности",  # Переименовано с "Дроссели"
    "semiconductors": "Полупроводники",
    "connectors": "Разъемы",
    "optics": "Оптические компоненты",  # Переименовано с "Оптические компоненты модули"
    "power_modules": "Модули питания",
    "cables": "Кабели",
    "others": "Другие",
    "unclassified": "Не распределено",
    "our_developments": "Наши разработки",
    "dev_boards": "Отладочные платы",
    "rf_modules": "СВЧ модули",
}


def enrich_with_mr_and_total(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет колонку 'Общее количество' с суммой по группам
    
    Группировка: по коду МР, если доступен, иначе по описанию и типу
    
    Args:
        df: DataFrame с данными компонентов
        
    Returns:
        DataFrame с добавленной колонкой 'Общее количество'
    """
    if df.empty:
        df["Общее количество"] = 0
        return df

    mr_col = find_column(["код мр", "part number", "pn", "mpn"], df.columns)
    qty_col = find_column(["количество", "qty", "quantity", "_merged_qty_"], df.columns)
    
    enriched = df.copy()
    tmp = enriched.copy()

    # Обработка колонки количества: безопасное преобразование в float
    if qty_col and qty_col in tmp.columns:
        # Используем pd.to_numeric с errors='coerce' для безопасного преобразования
        qty_series = pd.to_numeric(tmp[qty_col], errors='coerce')
        # Заменяем все NaN на 1
        qty_series = qty_series.fillna(1).astype(float)
    else:
        qty_series = pd.Series([1] * len(tmp), dtype=float)

    # Определяем ключи для группировки
    # ВАЖНО: если mr_col пустой или отсутствует, используем _merged_description_
    if mr_col and mr_col in tmp.columns and tmp[mr_col].notna().any():
        group_keys = [mr_col]
    else:
        # Если нет mr_col, группируем по _merged_description_
        if '_merged_description_' in tmp.columns:
            group_keys = ['_merged_description_']
        elif 'description' in tmp.columns:
            group_keys = ['description']
        else:
            # Fallback: группируем по всем возможным колонкам
            group_keys = [c for c in tmp.columns if c in ['description', 'value', 'part']]
            if not group_keys:
                # Если ничего не нашли, не группируем
                enriched["Общее количество"] = qty_series
                return enriched

    # Конвертируем все группировочные колонки в строки для избежания проблем с mixed types
    for key in group_keys:
        if key in tmp.columns:
            tmp[key] = tmp[key].fillna('').astype(str)

    tmp["__qty__"] = qty_series
    totals = tmp.groupby(group_keys, dropna=False)["__qty__"].sum().reset_index().rename(columns={"__qty__": "Общее количество"})

    # Конвертируем те же колонки в enriched для корректного merge
    for key in group_keys:
        if key in enriched.columns:
            enriched[key] = enriched[key].fillna('').astype(str)

    enriched = enriched.merge(totals, on=group_keys, how="left")
    enriched["Общее количество"] = enriched["Общее количество"].fillna(1).astype(int)

    return enriched


def format_excel_output(df: pd.DataFrame, sheet_name: str, desc_col: str) -> pd.DataFrame:
    """
    Форматирует DataFrame для записи в Excel:
    - Очистка названий компонентов
    - Извлечение ТУ
    - Добавление примечаний
    - Сортировка
    - Нумерация
    
    Args:
        df: DataFrame с данными
        sheet_name: Название листа (категория)
        desc_col: Название колонки с описанием
        
    Returns:
        Отформатированный DataFrame
    """
    if df.empty:
        return df
    
    result_df = df.copy()
    
    # Переименовать столбцы
    if 'Общее количество' in result_df.columns:
        result_df = result_df.rename(columns={'Общее количество': 'Кол-во'})
    if 'наименование ивп' in result_df.columns:
        result_df = result_df.rename(columns={'наименование ивп': 'Наименование ИВП'})
    # Переименовать нормализованные английские колонки в русские
    if '_merged_description_' in result_df.columns and 'Наименование ИВП' not in result_df.columns:
        result_df = result_df.rename(columns={'_merged_description_': 'Наименование ИВП'})
    elif 'description' in result_df.columns and 'Наименование ИВП' not in result_df.columns:
        result_df = result_df.rename(columns={'description': 'Наименование ИВП'})
    if 'qty' in result_df.columns and 'Кол-во' not in result_df.columns:
        result_df = result_df.rename(columns={'qty': 'Кол-во'})
    
    # Обработать наименование - очистить и извлечь ТУ
    # Найти столбец с наименованием (ВАЖНО: сначала ищем переименованный столбец!)
    desc_col_name = None
    for possible_name in ['Наименование ИВП', 'наименование ивп', 'описание', 'наименование', desc_col]:
        if possible_name and possible_name in result_df.columns:
            desc_col_name = possible_name
            break
    
    if not desc_col_name:
        # Если не нашли колонку с описанием, возвращаем как есть
        result_df.insert(0, '№ п/п', range(1, len(result_df) + 1))
        return result_df
    
    # Применить функцию очистки к каждой строке
    cleaned_data = []
    for idx, row in result_df.iterrows():
        text = str(row[desc_col_name]) if pd.notna(row[desc_col_name]) else ""
        note = str(row['note']) if 'note' in result_df.columns and pd.notna(row['note']) else ""
        
        # Извлечь ТУ из note (если есть)
        note_tu = ""
        note_type = ""
        if note and '|' in note:
            parts = note.split('|')
            if len(parts) >= 2:
                note_type = parts[0].strip()
                note_tu = parts[1].strip()
        
        # Очистить название
        cleaned_text = clean_component_name(text, note)
        
        # Извлечь ТУ из текста
        cleaned_text, tu_code = extract_tu_code(cleaned_text)
        
        # Если ТУ был в note, используем его
        if note_tu:
            tu_code = note_tu
        
        # Определить тип компонента
        comp_type = note_type if note_type else ""
        
        cleaned_data.append((cleaned_text, tu_code, comp_type))
    
    result_df[desc_col_name] = [item[0] for item in cleaned_data]
    
    # Для "Наших разработок" - если название пустое, взять из source_file
    if sheet_name == 'Наши разработки' and 'source_file' in result_df.columns:
        for idx in result_df.index:
            if not result_df.loc[idx, desc_col_name] or pd.isna(result_df.loc[idx, desc_col_name]) or str(result_df.loc[idx, desc_col_name]).strip() == '':
                source_file = result_df.loc[idx, 'source_file']
                if source_file and pd.notna(source_file):
                    # Извлечь название файла без расширения
                    file_name = os.path.splitext(os.path.basename(str(source_file)))[0]
                    result_df.loc[idx, desc_col_name] = file_name
    
    # Вставить ТУ сразу после наименования
    tu_data = [item[1] for item in cleaned_data]
    desc_idx = list(result_df.columns).index(desc_col_name)
    result_df.insert(desc_idx + 1, 'ТУ', tu_data)
    
    # Вставить Примечание после ТУ
    component_types = [item[2] for item in cleaned_data]
    
    # Определить стандартный тип для категории
    category_standard_types = {
        'Резисторы': 'Резистор',
        'Конденсаторы': 'Конденсатор',
        'Индуктивности': 'Дроссель',
        'Микросхемы': 'Микросхема',
        'Разъемы': 'Разъем',
        'Полупроводники': '',  # Нет стандартного типа
    }
    
    standard_type = category_standard_types.get(sheet_name, '')
    
    # Если тип компонента совпадает со стандартным - ставим "-"
    primechanie = []
    for comp_type in component_types:
        if not comp_type or comp_type == standard_type:
            primechanie.append('-')
        else:
            primechanie.append(comp_type)
    
    result_df.insert(desc_idx + 2, 'Примечание', primechanie)
    
    # Сортировка зависит от категории
    if sheet_name in ['Конденсаторы', 'Дроссели', 'Резисторы', 'Индуктивности']:
        # Определяем категорию для extract_nominal_value
        category_map = {
            'Резисторы': 'resistors',
            'Конденсаторы': 'capacitors',
            'Дроссели': 'inductors',
            'Индуктивности': 'inductors',
        }
        category_key = category_map.get(sheet_name, 'resistors')
        
        # Сортировка по номиналу
        result_df['_nominal'] = result_df[desc_col_name].apply(
            lambda x: extract_nominal_value(str(x), category_key)
        )
        result_df = result_df.sort_values(
            by=['_nominal', desc_col_name],
            ascending=[True, True]
        )
        result_df = result_df.drop(columns=['_nominal'])
    else:
        # Сортировка: сначала импортные, потом отечественные
        result_df['_is_domestic'] = result_df['ТУ'].apply(
            lambda x: 1 if (x and x != '-' and str(x).strip() != '') else 0
        )
        
        # Для отечественных: извлечь первые цифры из названия
        def get_domestic_number(row):
            if row['_is_domestic'] == 1:
                name = str(row[desc_col_name])
                match = re.match(r'(\d+)', name)
                if match:
                    return int(match.group(1))
                else:
                    return 999999
            else:
                return 0
        
        result_df['_domestic_num'] = result_df.apply(get_domestic_number, axis=1)
        
        # Для импортных: сортировка по номиналу (если применимо)
        category_map = {
            'Микросхемы': 'ics',
            'Полупроводники': 'semiconductors',
        }
        category_key = category_map.get(sheet_name, 'ics')
        
        result_df['_nominal'] = result_df[desc_col_name].apply(
            lambda x: extract_nominal_value(str(x), category_key) or 0
        )
        
        # Сортируем: сначала по типу (импортные/отечественные), потом по номиналу/номеру, потом по имени
        result_df = result_df.sort_values(
            by=['_is_domestic', '_domestic_num', '_nominal', desc_col_name],
            ascending=[True, True, True, True]
        )
        
        result_df = result_df.drop(columns=['_is_domestic', '_domestic_num', '_nominal'])
    
    result_df = result_df.reset_index(drop=True)
    
    # Добавить № п/п в начало (ПОСЛЕ сортировки!)
    result_df.insert(0, '№ п/п', range(1, len(result_df) + 1))
    
    # Переименовать source_file в Источник
    if 'source_file' in result_df.columns:
        result_df = result_df.rename(columns={'source_file': 'Источник'})
    
    # Удалить ненужные колонки
    cols_to_remove = ['ед. изм. ктд', 'код мр', '_merged_qty_', 
                    'ед. изм. КТД', 'Код МР', 'Код мр', 'ед. изм. КТД', 'Код МР']
    for col in cols_to_remove:
        if col in result_df.columns:
            result_df = result_df.drop(columns=[col])
    
    # Упорядочить колонки в правильном порядке
    desired_order = ['№ п/п', 'Наименование ИВП', 'ТУ', 'Примечание', 'Источник', 'Кол-во']
    
    ordered_cols = [col for col in desired_order if col in result_df.columns]
    remaining_cols = [col for col in result_df.columns 
                    if col not in ordered_cols and col not in cols_to_remove]
    
    final_cols = ordered_cols + remaining_cols
    result_df = result_df[final_cols]
    
    # Удалить 'note' перед записью (если остался)
    if 'note' in result_df.columns:
        result_df = result_df.drop(columns=['note'])
    
    return result_df


def apply_excel_styles(writer: pd.ExcelWriter):
    """
    Применяет стили к Excel файлу:
    - Выравнивание (center для большинства, left для описания и ТУ)
    - Автоматическая ширина столбцов
    
    Args:
        writer: ExcelWriter с уже записанными данными
    """
    for sheet_name in writer.book.sheetnames:
        ws = writer.book[sheet_name]
        
        # Найти индексы столбцов "Наименование ИВП" и "ТУ"
        desc_col_idx = None
        tu_col_idx = None
        for idx, cell in enumerate(ws[1], start=1):
            cell_val = str(cell.value).lower() if cell.value else ''
            if 'наименование ивп' in cell_val or 'наименование' in cell_val:
                desc_col_idx = idx
            elif cell_val == 'ту':
                tu_col_idx = idx
        
        # Центрировать все ячейки, кроме "наименование ивп" и "ТУ"
        for row_idx, row in enumerate(ws.iter_rows(), start=1):
            for col_idx, cell in enumerate(row, start=1):
                if col_idx == desc_col_idx or col_idx == tu_col_idx:
                    # Наименование ИВП и ТУ - выравнивание по левому краю
                    cell.alignment = Alignment(horizontal='left', vertical='center')
                else:
                    # Все остальные - по центру
                    cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Автоматически установить ширину столбцов по содержимому
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception:
                    pass
            adjusted_width = min(max_length + 2, 100)
            ws.column_dimensions[column_letter].width = adjusted_width


def write_categorized_excel(
    outputs: Dict[str, pd.DataFrame],
    df: pd.DataFrame,
    output_xlsx: str,
    combine: bool,
    desc_col: str
):
    """
    Записывает категоризованные данные в Excel файл
    
    Args:
        outputs: Словарь {category_key: DataFrame}
        df: Полный DataFrame со всеми данными
        output_xlsx: Путь к выходному Excel файлу
        combine: Если True, добавляет SUMMARY лист
        desc_col: Название колонки с описанием
    """
    sheets_written = 0
    
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        for key, part_df in outputs.items():
            if len(part_df) == 0:
                continue
            
            sheet_name = RUS_SHEET_NAMES.get(key, key)
            
            # Обогатить данными МР и общим количеством
            result_df = enrich_with_mr_and_total(part_df)
            
            # Фильтровать строки с пустым Наименованием ИВП
            desc_check_cols = [desc_col, '_merged_description_', 'description', 'Наименование ИВП']
            for check_col in desc_check_cols:
                if check_col in result_df.columns:
                    result_df = result_df[result_df[check_col].notna() & (result_df[check_col].astype(str).str.strip() != '')]
                    break
            
            if result_df.empty:
                continue
            
            # Форматировать для вывода
            result_df = format_excel_output(result_df, sheet_name, desc_col)
            
            # Проверка что есть данные после форматирования
            if result_df.empty or len(result_df) == 0:
                continue
            
            # Записать в Excel
            result_df.to_excel(writer, sheet_name=sheet_name, index=False)
            sheets_written += 1
        
        # SUMMARY sheet
        if combine:
            summary_rows = []
            for key, part_df in outputs.items():
                if len(part_df) == 0:
                    continue
                category_name = RUS_SHEET_NAMES.get(key, key)
                total_qty = part_df['Общее количество'].sum() if 'Общее количество' in part_df.columns else len(part_df)
                summary_rows.append({
                    '№ п/п': len(summary_rows) + 1,
                    'Категория': category_name,
                    'Кол-во позиций': len(part_df),
                    'Общее количество': int(total_qty)
                })
            
            if summary_rows:
                summary = pd.DataFrame(summary_rows)
                summary.to_excel(writer, sheet_name="SUMMARY", index=False)
                sheets_written += 1
        
        # SOURCES sheet
        sources = pd.DataFrame(
            sorted({(r.get("source_file", ""), r.get("source_sheet", "")) for _, r in df.iterrows()}), 
            columns=["source_file", "source_sheet"]
        )
        if not sources.empty:
            sources.to_excel(writer, sheet_name="SOURCES", index=False)
            sheets_written += 1
        
        # Проверить что хотя бы один лист записан
        if sheets_written == 0:
            # Записать пустой лист с сообщением
            empty_df = pd.DataFrame({'Сообщение': ['Нет данных для записи']})
            empty_df.to_excel(writer, sheet_name="INFO", index=False)
            sheets_written = 1
        
        # Применить стили только если есть листы
        if sheets_written > 0:
            apply_excel_styles(writer)
    
    print(f"XLSX written: {output_xlsx} ({sheets_written} sheets)")
