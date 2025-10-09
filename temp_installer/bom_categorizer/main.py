# -*- coding: utf-8 -*-
"""
Главная функция CLI для категоризации BOM файлов

Поддерживаемые входные форматы:
- .txt (текстовые файлы с разделителями)
- .docx (документы Word с таблицами)
- .xlsx, .xls (Excel файлы)
"""

import os
import re
import sys
import json
import argparse
from typing import List, Dict, Any, Optional
import pandas as pd

from .parsers import parse_txt_like, parse_docx
from .classifiers import classify_row
from .excel_writer import write_categorized_excel, enrich_with_mr_and_total
from .txt_writer import write_txt_reports
from .utils import normalize_column_names, find_column


def add_excel_row_numbers(df: pd.DataFrame, header_offset: int = 2) -> pd.DataFrame:
    """
    Добавляет колонку с номерами строк Excel, если она отсутствует,
    или заполняет пустые значения номерами строк
    
    Args:
        df: DataFrame после чтения Excel
        header_offset: Смещение строки заголовка (обычно 2: строка 1 = заголовок, данные с 2)
    
    Returns:
        DataFrame с добавленной/заполненной колонкой "№ п\\п"
    """
    # Проверяем, есть ли уже колонка с номерами позиций
    pp_columns = [col for col in df.columns if str(col).startswith('№ п')]
    
    if not pp_columns:
        # Колонки нет - создаём с номерами строк Excel
        df['№ п\\п'] = range(header_offset, header_offset + len(df))
        print(f"  [+] Добавлена колонка '№ п\\п' с номерами строк Excel ({header_offset}-{header_offset + len(df) - 1})")
    else:
        # Колонка есть - проверяем пустые значения и заполняем их
        pp_col = pp_columns[0]
        empty_count = df[pp_col].isna().sum()
        
        if empty_count > 0:
            # Заполняем пустые значения номерами строк Excel
            for idx in df[df[pp_col].isna()].index:
                df.loc[idx, pp_col] = header_offset + idx
            print(f"  [+] Заполнено {empty_count} пустых значений в колонке '{pp_col}' номерами строк Excel")
    
    return df


def load_and_combine_inputs(input_paths: List[str], sheets_str: Optional[str] = None, sheet: Optional[str] = None) -> pd.DataFrame:
    """
    Загружает и объединяет данные из всех входных файлов
    
    Args:
        input_paths: Список путей к входным файлам
        sheets_str: Строка с номерами листов Excel (через запятую)
        sheet: Конкретный лист для чтения
        
    Returns:
        Объединенный DataFrame со всеми данными
    """
    all_rows: List[pd.DataFrame] = []
    
    for input_path in input_paths:
        ext = os.path.splitext(input_path)[1].lower()
        
        # TXT parsing
        if ext in [".txt"]:
            try:
                df_txt = parse_txt_like(input_path)
                df_txt["source_file"] = os.path.basename(input_path)
                df_txt["source_sheet"] = ""
                all_rows.append(df_txt)
            except Exception as exc:
                print(f"⚠️ Не удалось прочитать TXT '{input_path}': {exc}", file=sys.stderr)
        
        # DOCX parsing
        elif ext in [".doc", ".docx"]:
            try:
                df_docx = parse_docx(input_path)
                df_docx["source_file"] = os.path.basename(input_path)
                df_docx["source_sheet"] = ""
                all_rows.append(df_docx)
            except Exception as exc:
                print(f"⚠️ Не удалось прочитать DOCX '{input_path}': {exc}", file=sys.stderr)
        
        # Excel parsing
        elif ext in [".xlsx", ".xls"]:
            try:
                # Читать "Код МР" как строку, чтобы сохранить точность больших чисел
                read_kwargs = {
                    'dtype': {
                        'Код МР': str,
                        'код мр': str,
                        'КОД МР': str,
                        'Код мр': str,
                        'код_мр': str,
                        'kodmr': str
                    }
                }
                
                # Parse sheets parameter if provided
                if sheets_str:
                    sheets_requested = []
                    for s_token in sheets_str.split(","):
                        s_token = s_token.strip()
                        try:
                            sheets_requested.append(int(s_token))
                        except ValueError:
                            sheets_requested.append(s_token)
                    
                    # Read multiple sheets
                    for sh in sheets_requested:
                        read_kwargs_copy = read_kwargs.copy()
                        read_kwargs_copy["sheet_name"] = sh
                        try:
                            dfi = pd.read_excel(input_path, **read_kwargs_copy)
                            
                            if isinstance(dfi, dict):
                                first_key = next(iter(dfi))
                                dfi = dfi[first_key]
                                sh = first_key
                            
                            # Проверка на пустую первую строку
                            unnamed_count = sum(1 for col in dfi.columns if str(col).lower().startswith('unnamed'))
                            has_mostly_unnamed = unnamed_count >= len(dfi.columns) * 0.5
                            
                            header_was_removed = False
                            if has_mostly_unnamed and not dfi.empty and dfi.iloc[0].notna().any():
                                first_row_text = ' '.join(str(val).lower() for val in dfi.iloc[0] if pd.notna(val))
                                looks_like_header = any(keyword in first_row_text for keyword in 
                                    ['наименование', 'количество', 'кол.', 'код', 'description', 'qty'])
                                
                                if looks_like_header:
                                    new_headers = dfi.iloc[0].fillna('').astype(str)
                                    dfi = dfi[1:].reset_index(drop=True)
                                    dfi.columns = new_headers
                                    header_was_removed = True
                            
                            # Добавить номера строк Excel, если колонка "№ п\п" отсутствует
                            header_offset = 3 if header_was_removed else 2
                            dfi = add_excel_row_numbers(dfi, header_offset)
                            
                            dfi["source_file"] = os.path.basename(input_path)
                            dfi["source_sheet"] = str(sh)
                            all_rows.append(dfi)
                        except Exception as exc:
                            print(f"⚠️ Не удалось прочитать лист '{sh}' из '{input_path}': {exc}", file=sys.stderr)
                
                elif sheet is not None:
                    # Пользователь указал конкретный лист через --sheet
                    try:
                        sheet = int(sheet)
                    except ValueError:
                        pass
                    read_kwargs["sheet_name"] = sheet
                    
                    df = pd.read_excel(input_path, **read_kwargs)
                    if isinstance(df, dict):
                        first_key = next(iter(df))
                        df = df[first_key]
                        src_sheet = first_key
                    else:
                        src_sheet = sheet
                    
                    # Проверка на пустую первую строку
                    header_was_removed = False
                    if all(str(col).lower().startswith('unnamed') for col in df.columns):
                        if not df.empty and df.iloc[0].notna().any():
                            new_headers = df.iloc[0].fillna('').astype(str)
                            df = df[1:].reset_index(drop=True)
                            df.columns = new_headers
                            header_was_removed = True
                    
                    # Добавить номера строк Excel, если колонка "№ п\п" отсутствует
                    header_offset = 3 if header_was_removed else 2
                    df = add_excel_row_numbers(df, header_offset)
                    
                    df["source_file"] = os.path.basename(input_path)
                    df["source_sheet"] = str(src_sheet)
                    all_rows.append(df)
                
                else:
                    # Листы не указаны - читаем ВСЕ листы
                    all_sheets_data = pd.read_excel(input_path, sheet_name=None, **{k: v for k, v in read_kwargs.items() if k != 'sheet_name'})
                    for sheet_name, df_local in all_sheets_data.items():
                        # Проверка на пустую первую строку
                        unnamed_count = sum(1 for col in df_local.columns if str(col).lower().startswith('unnamed'))
                        has_mostly_unnamed = unnamed_count >= len(df_local.columns) * 0.5
                        
                        header_was_removed = False
                        if has_mostly_unnamed and not df_local.empty and df_local.iloc[0].notna().any():
                            first_row_text = ' '.join(str(val).lower() for val in df_local.iloc[0] if pd.notna(val))
                            looks_like_header = any(keyword in first_row_text for keyword in 
                                ['наименование', 'количество', 'кол.', 'код', 'description', 'qty'])
                            
                            if looks_like_header:
                                new_headers = df_local.iloc[0].fillna('').astype(str)
                                df_local = df_local[1:].reset_index(drop=True)
                                df_local.columns = new_headers
                                header_was_removed = True
                        
                        # Добавить номера строк Excel, если колонка "№ п\п" отсутствует
                        header_offset = 3 if header_was_removed else 2
                        df_local = add_excel_row_numbers(df_local, header_offset)
                        
                        df_local["source_file"] = os.path.basename(input_path)
                        df_local["source_sheet"] = str(sheet_name)
                        all_rows.append(df_local)
            
            except Exception as exc:
                print(f"⚠️ Не удалось прочитать Excel '{input_path}': {exc}", file=sys.stderr)
                raise SystemExit(f"Failed to read Excel '{input_path}': {exc}")
    
    if not all_rows:
        raise SystemExit("No data loaded from inputs")
    
    df = pd.concat(all_rows, ignore_index=True)
    
    # Объединяем source_file и source_sheet для многолистовых файлов
    if 'source_sheet' in df.columns and 'source_file' in df.columns:
        file_sheet_counts = df.groupby('source_file')['source_sheet'].nunique()
        multi_sheet_files = file_sheet_counts[file_sheet_counts > 1].index.tolist()
        
        if multi_sheet_files:
            for file in multi_sheet_files:
                file_mask = df['source_file'] == file
                unique_sheets = df.loc[file_mask, 'source_sheet'].unique()
                sheet_to_num = {sheet: i+1 for i, sheet in enumerate(unique_sheets)}
                
                df.loc[file_mask, 'source_file'] = df.loc[file_mask].apply(
                    lambda row: f"{row['source_file']} Лист_{sheet_to_num[row['source_sheet']]}", 
                    axis=1
                )
            
            df = df.drop(columns=['source_sheet'])
    
    return df


def normalize_and_merge_columns(df: pd.DataFrame) -> tuple:
    """
    Нормализует названия колонок и объединяет дублирующиеся колонки
    
    Returns:
        (df, ref_col, desc_col, value_col, part_col, qty_col, mr_col)
    """
    # Normalize columns
    original_cols = list(df.columns)
    lower_cols = normalize_column_names(original_cols)
    rename_map = {orig: norm for orig, norm in zip(original_cols, lower_cols)}
    df = df.rename(columns=rename_map)
    
    # Common column guesses
    ref_col = find_column(["ref", "reference", "designator", "refdes", "reference designator", "обозначение", "позиционное обозначение"], list(df.columns))
    desc_col = find_column(["description", "desc", "наименование ивп", "наименование", "имя", "item", "part", "part name", "наим."], list(df.columns))
    value_col = find_column(["value", "значение", "номинал"], list(df.columns))
    part_col = find_column(["partnumber", "mfr part", "mpn", "pn", "art", "артикул", "part", "part name"], list(df.columns))
    qty_col = find_column([
        "qty", "quantity", "количество", "кол.", "кол-во", "кол. в ктд", "кол в ктд", "кол. в спецификации", "кол. в кдт",
        "кол. в ктд", "кол. в ктд, шт", "кол. в ктд (шт)", "кол. в ктд, шт."
    ], list(df.columns))
    mr_col = find_column([
        "код мр", "код ивп", "код мр/ивп", "код позиции", "код изделия", "код мр позиции", "код мр ивп"
    ], list(df.columns))
    
    # Merge multiple description columns
    possible_desc_cols = [col for col in df.columns if any(
        col.startswith(prefix) for prefix in ["description", "наименование", "desc", "имя"]
    )]
    
    if len(possible_desc_cols) > 1:
        def merge_desc(row):
            for col in possible_desc_cols:
                val = row.get(col)
                if pd.notna(val) and str(val).strip():
                    return val
            return None
        
        df["_merged_description_"] = df.apply(merge_desc, axis=1)
        for col in possible_desc_cols:
            if col in df.columns:
                df = df.drop(columns=[col])
        desc_col = "_merged_description_"
    
    # Merge multiple qty columns
    possible_qty_cols = [col for col in df.columns if any(
        col.startswith(prefix) for prefix in ["qty", "quantity", "количество", "кол"]
    )]
    
    if len(possible_qty_cols) > 1:
        def merge_qty(row):
            for col in possible_qty_cols:
                val = row.get(col)
                if pd.notna(val):
                    try:
                        return float(val) if val != 0 or str(val).strip() == '0' else None
                    except:
                        pass
            return None
        
        df["_merged_qty_"] = df.apply(merge_qty, axis=1)
        for col in possible_qty_cols:
            if col in df.columns:
                df = df.drop(columns=[col])
        qty_col = "_merged_qty_"
    
    # Ensure we have at least some text to classify
    if not any([ref_col, desc_col, value_col, part_col]):
        df["_row_text_"] = df.apply(lambda r: " ".join(str(x) for x in r.values if pd.notna(x)), axis=1)
        desc_col = "_row_text_"
    
    return df, ref_col, desc_col, value_col, part_col, qty_col, mr_col


def run_classification(df: pd.DataFrame, ref_col: str, desc_col: str, value_col: str, part_col: str, loose: bool) -> pd.DataFrame:
    """
    Классифицирует все строки DataFrame
    
    Returns:
        DataFrame с добавленной колонкой 'category'
    """
    categories: List[str] = []
    for _, row in df.iterrows():
        ref = row.get(ref_col) if ref_col else None
        desc = row.get(desc_col) if desc_col else None
        val = row.get(value_col) if value_col else None
        part = row.get(part_col) if part_col else None
        src_file = row.get('source_file') if 'source_file' in df.columns else None
        note_val = row.get('note') if 'note' in df.columns else None
        categories.append(classify_row(ref, desc, val, part, strict=not loose, source_file=src_file, note=note_val))
    
    df = df.copy()
    df["category"] = categories
    return df


def apply_rules_from_json(df: pd.DataFrame, rules_json: str, desc_col: str, value_col: str, part_col: str, ref_col: str) -> pd.DataFrame:
    """
    Применяет правила классификации из JSON файла
    
    Returns:
        DataFrame с обновленными категориями
    """
    if not os.path.exists(rules_json):
        return df
    
    try:
        with open(rules_json, "r", encoding="utf-8") as f:
            rules = json.load(f)
        
        if not isinstance(rules, list) or len(rules) == 0:
            return df
        
        print(f"Применяю {len(rules)} сохраненных правил из {rules_json}...")
        rules_applied_count = 0
        
        for i, rule in enumerate(rules, start=1):
            cat = str(rule.get("category", "")).strip()
            contains = str(rule.get("contains", "")).strip().lower()
            regex = rule.get("regex")
            
            if not cat or (not contains and not regex):
                continue
            
            # ИСПРАВЛЕНО: Применяем правила ко ВСЕМ элементам с категорией unclassified
            mask = df["category"] == "unclassified"
            
            if contains:
                # ИСПРАВЛЕНО: Используем правильные колонки из normalize_and_merge_columns
                def get_col_values(col_name):
                    if col_name and col_name in df.columns:
                        return df[col_name].astype(str).str.lower().fillna("")
                    return pd.Series([""] * len(df))
                
                blob = (
                    get_col_values(desc_col) + " " +
                    get_col_values(value_col) + " " +
                    get_col_values(part_col) + " " +
                    get_col_values(ref_col)
                )
                mask = mask & blob.str.contains(re.escape(contains), na=False)
            
            if regex:
                try:
                    r = re.compile(regex, re.IGNORECASE)
                    
                    def get_col_values_str(col_name):
                        if col_name and col_name in df.columns:
                            return df[col_name].astype(str).fillna("")
                        return pd.Series([""] * len(df))
                    
                    text_series = (
                        get_col_values_str(desc_col) + " " +
                        get_col_values_str(value_col) + " " +
                        get_col_values_str(part_col) + " " +
                        get_col_values_str(ref_col)
                    )
                    mask = mask & text_series.apply(lambda t: bool(r.search(t)))
                except Exception:
                    pass
            
            matched_count = mask.sum()
            if matched_count > 0:
                df.loc[mask, "category"] = cat
                rules_applied_count += matched_count
        
        if rules_applied_count > 0:
            print(f"[OK] {rules_applied_count} элементов автоматически классифицированы по сохраненным правилам")
    
    except Exception as exc:
        print(f"[!] Не удалось применить правила из {rules_json}: {exc}")
    
    return df


def interactive_classification(df: pd.DataFrame, desc_col: str, value_col: str, part_col: str, rules_json: str, auto_prompted: bool = False) -> pd.DataFrame:
    """
    Интерактивная классификация нераспределенных элементов
    
    Returns:
        DataFrame с обновленными категориями
    """
    cat_names = [
        ("resistors", "Резисторы"),
        ("capacitors", "Конденсаторы"),
        ("inductors", "Дроссели"),
        ("ics", "Микросхемы"),
        ("connectors", "Разъемы"),
        ("dev_boards", "Отладочные платы"),
        ("semiconductors", "Полупроводники"),
        ("our_developments", "Наши разработки"),
        ("others", "Другие"),
        ("unclassified", "Не распределено"),
    ]
    
    uncls = df[df["category"] == "unclassified"].copy()
    max_preview = min(len(uncls), 50)
    
    skip_interactive = False
    if auto_prompted:
        print(f"\n⚠️  ВНИМАНИЕ: Обнаружено {len(uncls)} нераспределённых элементов!")
        print(f"Для повышения точности рекомендуется интерактивная классификация.")
        response = input(f"\nЗапустить интерактивный режим для классификации? (y/n, Enter=y): ").strip().lower()
        if response and response not in ['y', 'yes', 'д', 'да', '']:
            print("Интерактивный режим пропущен. Нераспределенные элементы останутся в категории 'Не распределено'.")
            skip_interactive = True
        else:
            print(f"\nНераспределено: {len(uncls)}. Покажу первые {max_preview} для разметки.")
    else:
        print(f"Нераспределено: {len(uncls)}. Покажу первые {max_preview} для разметки.")
    
    if skip_interactive:
        return df
    
    # Load existing rules
    existing_rules: List[Dict[str, Any]] = []
    if os.path.exists(rules_json):
        try:
            with open(rules_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_rules = data
        except Exception:
            pass
    
    for idx, (_, row) in enumerate(uncls.head(max_preview).iterrows(), start=1):
        text_blob = " ".join(str(x) for x in [row.get(desc_col), row.get(value_col), row.get(part_col)] if pd.notna(x))
        print(f"[{idx}] {text_blob}")
        for i, (_, ru) in enumerate(cat_names, start=1):
            print(f"  {i}. {ru}")
        choice = input("Выберите номер категории (Enter чтобы пропустить): ").strip()
        if choice.isdigit():
            ci = int(choice)
            if 1 <= ci <= len(cat_names):
                selected_key = cat_names[ci - 1][0]
                df.loc[uncls.index[idx - 1], "category"] = selected_key
                rule = {"contains": text_blob[:160], "category": selected_key}
                existing_rules.append(rule)
    
    # Save updated rules
    try:
        with open(rules_json, "w", encoding="utf-8") as f:
            json.dump(existing_rules, f, ensure_ascii=False, indent=2)
        print(f"Сохранил правила: {rules_json}")
    except Exception as exc:
        print(f"Не удалось сохранить правила: {exc}")
    
    return df


def combine_debug_modules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Объединяет категории для "Отладочные платы и модули"
    
    Returns:
        DataFrame с объединенными категориями
    """
    debug_modules_parts = []
    
    # 1. Наши разработки
    our_dev = df[df["category"] == "our_developments"]
    if not our_dev.empty:
        debug_modules_parts.append(our_dev)
    
    # 2. Пустая строка
    if debug_modules_parts:
        empty_row = pd.DataFrame([{col: '' for col in df.columns}])
        debug_modules_parts.append(empty_row)
    
    # 3. Отладочные платы
    dev_boards = df[df["category"] == "dev_boards"]
    if not dev_boards.empty:
        debug_modules_parts.append(dev_boards)
    
    # 4. Пустая строка
    if len(debug_modules_parts) > 0 and not dev_boards.empty:
        empty_row2 = pd.DataFrame([{col: '' for col in df.columns}])
        debug_modules_parts.append(empty_row2)
    
    # 5. СВЧ модули
    rf_mods = df[df["category"] == "rf_modules"]
    if not rf_mods.empty:
        debug_modules_parts.append(rf_mods)
    
    # Объединяем все части
    debug_modules_combined = pd.concat(debug_modules_parts, ignore_index=True) if debug_modules_parts else pd.DataFrame()
    
    return debug_modules_combined


def create_outputs_dict(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Создает словарь выходных DataFrame по категориям
    
    Returns:
        Словарь {category_key: DataFrame}
    """
    debug_modules_combined = combine_debug_modules(df)
    
    outputs = {
        "debug_modules": debug_modules_combined,
        "ics": df[df["category"] == "ics"],
        "resistors": df[df["category"] == "resistors"],
        "capacitors": df[df["category"] == "capacitors"],
        "inductors": df[df["category"] == "inductors"],
        "semiconductors": df[df["category"] == "semiconductors"],
        "connectors": df[df["category"] == "connectors"],
        "optics": df[df["category"] == "optics"],
        "power_modules": df[df["category"] == "power_modules"],
        "cables": df[df["category"] == "cables"],
        "others": df[df["category"] == "others"],
        "unclassified": df[df["category"] == "unclassified"],
    }
    
    return outputs


def print_summary(outputs: Dict[str, pd.DataFrame]):
    """
    Выводит сводку по количеству элементов в каждой категории
    """
    print("Split complete:")
    for key, part_df in outputs.items():
        print(f"  {key}: {len(part_df)}")


def parse_exclude_items(exclude_file_path: str) -> list:
    """
    Парсит файл с элементами для исключения
    
    Формат файла: каждая строка содержит "Название ИВП, количество"
    Например:
        AD9221AR, 2
        GRM1885C1H681J, 1
        
    Args:
        exclude_file_path: Путь к файлу с исключениями
        
    Returns:
        Список кортежей (название, количество)
    """
    exclude_items = []
    
    if not os.path.exists(exclude_file_path):
        print(f"⚠️ Файл исключений не найден: {exclude_file_path}")
        return exclude_items
    
    try:
        with open(exclude_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Парсинг формата "Название, количество"
                if ',' in line:
                    parts = line.rsplit(',', 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        try:
                            qty = int(parts[1].strip())
                            exclude_items.append((name, qty))
                        except ValueError:
                            print(f"⚠️ Ошибка в строке {line_num}: неверное количество '{parts[1].strip()}'")
                    else:
                        print(f"⚠️ Ошибка в строке {line_num}: неверный формат")
                else:
                    print(f"⚠️ Ошибка в строке {line_num}: отсутствует запятая")
    except Exception as e:
        print(f"⚠️ Ошибка при чтении файла исключений: {e}")
    
    return exclude_items


def apply_exclusions(df: pd.DataFrame, exclude_items: list, desc_col: str) -> pd.DataFrame:
    """
    Применяет исключения элементов к DataFrame
    
    Args:
        df: DataFrame с данными BOM
        exclude_items: Список кортежей (название, количество) для исключения
        desc_col: Имя колонки с описанием
        
    Returns:
        DataFrame с примененными исключениями
    """
    if not exclude_items:
        return df
    
    if desc_col not in df.columns:
        print(f"⚠️ Колонка '{desc_col}' не найдена, исключения не применены")
        return df
    
    # Найти колонку количества
    qty_col = find_column(df, ['qty', '_merged_qty_', 'Количество', 'количество', 'Кол-во', 'кол-во'])
    if not qty_col or qty_col not in df.columns:
        print("⚠️ Колонка количества не найдена, исключения не могут быть применены")
        return df
    
    excluded_count = 0
    reduced_count = 0
    
    for exclude_name, exclude_qty in exclude_items:
        # Найти строки с совпадающим названием (частичное совпадение)
        mask = df[desc_col].astype(str).str.contains(exclude_name, case=False, na=False, regex=False)
        matching_indices = df[mask].index.tolist()
        
        if not matching_indices:
            print(f"⚠️ Элемент '{exclude_name}' не найден в BOM")
            continue
        
        remaining_exclude_qty = exclude_qty
        
        for idx in matching_indices:
            if remaining_exclude_qty <= 0:
                break
            
            current_qty = df.loc[idx, qty_col]
            if pd.isna(current_qty):
                continue
            
            try:
                current_qty = int(current_qty)
            except (ValueError, TypeError):
                continue
            
            if current_qty <= remaining_exclude_qty:
                # Сохранить название перед удалением
                item_name = df.loc[idx, desc_col]
                # Удалить всю строку
                df = df.drop(idx)
                remaining_exclude_qty -= current_qty
                excluded_count += 1
                print(f"✓ Исключен элемент '{item_name}' (qty: {current_qty})")
            else:
                # Уменьшить количество
                new_qty = current_qty - remaining_exclude_qty
                df.loc[idx, qty_col] = new_qty
                print(f"✓ Уменьшено количество '{df.loc[idx, desc_col]}': {current_qty} → {new_qty}")
                remaining_exclude_qty = 0
                reduced_count += 1
        
        if remaining_exclude_qty > 0:
            print(f"⚠️ Не удалось исключить полное количество '{exclude_name}': осталось {remaining_exclude_qty}")
    
    if excluded_count > 0 or reduced_count > 0:
        print(f"\n📊 Итого исключено: {excluded_count} строк, уменьшено: {reduced_count} строк")
    
    return df


def process_file_for_comparison(file_path: str, no_interactive: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Обрабатывает BOM файл для сравнения (классификация с автоматическим переносом unclassified в 'others')
    
    Args:
        file_path: Путь к файлу
        no_interactive: Отключить интерактивный режим
        
    Returns:
        Словарь категорий с DataFrame
    """
    print(f"\n📂 Обработка файла: {file_path}")
    
    # Загрузить файл
    df = load_and_combine_inputs([file_path], None, None)
    
    # Нормализовать колонки
    df, ref_col, desc_col, value_col, part_col, qty_col, mr_col = normalize_and_merge_columns(df)
    
    # Фильтровать пустые строки
    if desc_col in df.columns:
        df = df[df[desc_col].notna() & (df[desc_col].astype(str).str.strip() != '')]
    
    # Проверить существующую категорию
    has_existing_category = 'category' in df.columns
    
    if not has_existing_category:
        # Классифицировать
        df = run_classification(df, ref_col, desc_col, value_col, part_col, loose=False)
        
        # Применить правила из JSON
        df = apply_rules_from_json(df, "rules.json", desc_col, value_col, part_col, ref_col)
        
        # Автоматически перенести unclassified в 'others'
        unclassified_mask = df["category"] == "unclassified"
        unclassified_count = unclassified_mask.sum()
        if unclassified_count > 0:
            print(f"ℹ️  Перенос {unclassified_count} нераспределенных элементов в категорию 'Другие'")
            df.loc[unclassified_mask, "category"] = "others"
    
    # Очистить названия
    if not has_existing_category:
        from .formatters import clean_component_name
        if desc_col in df.columns:
            cleaned_values = []
            for val in df[desc_col]:
                if pd.notna(val):
                    cleaned_values.append(clean_component_name(str(val)))
                else:
                    cleaned_values.append(val)
            df[desc_col] = cleaned_values
    
    # Создать outputs словарь
    outputs = create_outputs_dict(df)
    
    # ВАЖНО: Применить format_excel_output для каждой категории
    # Это приводит данные к стандартному виду (извлекает ТУ, добавляет колонки, нормализует)
    from .excel_writer import format_excel_output, RUS_SHEET_NAMES
    processed_outputs = {}
    
    for category, cat_df in outputs.items():
        if not cat_df.empty:
            # Получить русское название категории для правильной обработки
            sheet_name = RUS_SHEET_NAMES.get(category, category)
            
            # Применить полную обработку (извлечение ТУ, очистка, сортировка)
            # force_reprocess=True: всегда обрабатывать заново, даже если файл уже обработан
            processed_df = format_excel_output(
                cat_df, 
                sheet_name, 
                desc_col,
                force_reprocess=True
            )
            processed_outputs[category] = processed_df
        else:
            processed_outputs[category] = cat_df
    
    print(f"✓ Файл обработан: {len(df)} элементов в {len(outputs)} категориях")
    
    return processed_outputs


def compare_bom_files(file1_path: str, file2_path: str, output_path: str, no_interactive: bool = True):
    """
    Сравнивает два BOM файла и создает отчет о различиях
    
    Args:
        file1_path: Путь к первому файлу (базовый)
        file2_path: Путь ко второму файлу (новый)
        output_path: Путь к выходному файлу с результатами
        no_interactive: Отключить интерактивный режим
    """
    print("=" * 80)
    print("🔄 СРАВНЕНИЕ BOM ФАЙЛОВ")
    print("=" * 80)
    
    # Обработать оба файла
    outputs1 = process_file_for_comparison(file1_path, no_interactive)
    outputs2 = process_file_for_comparison(file2_path, no_interactive)
    
    # Получить все категории
    all_categories = sorted(set(list(outputs1.keys()) + list(outputs2.keys())))
    
    print(f"\n📊 Сравнение по категориям...")
    
    # Создать список для результатов
    comparison_results = []
    
    for category in all_categories:
        df1 = outputs1.get(category, pd.DataFrame())
        df2 = outputs2.get(category, pd.DataFrame())
        
        if df1.empty and df2.empty:
            continue
        
        # Найти колонку описания
        desc_col1 = find_column(df1, ['Наименование ИВП', 'наименование ивп', 'description', '_merged_description_']) if not df1.empty else None
        desc_col2 = find_column(df2, ['Наименование ИВП', 'наименование ивп', 'description', '_merged_description_']) if not df2.empty else None
        
        # Найти колонку количества
        qty_col1 = find_column(df1, ['Кол-во', 'qty', '_merged_qty_', 'Количество']) if not df1.empty else None
        qty_col2 = find_column(df2, ['Кол-во', 'qty', '_merged_qty_', 'Количество']) if not df2.empty else None
        
        # Создать словари для сравнения: название -> количество
        items1 = {}
        if not df1.empty and desc_col1 and qty_col1:
            for _, row in df1.iterrows():
                name = str(row[desc_col1]) if pd.notna(row[desc_col1]) else ""
                qty_val = row[qty_col1]
                # Обработка пустых значений, NaN и строк
                if pd.notna(qty_val) and str(qty_val).strip():
                    try:
                        qty = int(float(qty_val))
                    except (ValueError, TypeError):
                        qty = 0
                else:
                    qty = 0
                items1[name] = items1.get(name, 0) + qty
        
        items2 = {}
        if not df2.empty and desc_col2 and qty_col2:
            for _, row in df2.iterrows():
                name = str(row[desc_col2]) if pd.notna(row[desc_col2]) else ""
                qty_val = row[qty_col2]
                # Обработка пустых значений, NaN и строк
                if pd.notna(qty_val) and str(qty_val).strip():
                    try:
                        qty = int(float(qty_val))
                    except (ValueError, TypeError):
                        qty = 0
                else:
                    qty = 0
                items2[name] = items2.get(name, 0) + qty
        
        # Найти различия
        all_items = set(list(items1.keys()) + list(items2.keys()))
        
        for item_name in sorted(all_items):
            if not item_name:
                continue
            
            qty1 = items1.get(item_name, 0)
            qty2 = items2.get(item_name, 0)
            
            if qty1 != qty2:
                if qty1 == 0:
                    # Добавлен
                    comparison_results.append({
                        'Категория': category,
                        'Изменение': 'Добавлено',
                        'Наименование ИВП': item_name,
                        'Кол-во в файле 1': qty1,
                        'Кол-во в файле 2': qty2,
                        'Разница': qty2 - qty1
                    })
                elif qty2 == 0:
                    # Удален
                    comparison_results.append({
                        'Категория': category,
                        'Изменение': 'Удалено',
                        'Наименование ИВП': item_name,
                        'Кол-во в файле 1': qty1,
                        'Кол-во в файле 2': qty2,
                        'Разница': qty2 - qty1
                    })
                else:
                    # Изменено количество
                    comparison_results.append({
                        'Категория': category,
                        'Изменение': 'Изменено',
                        'Наименование ИВП': item_name,
                        'Кол-во в файле 1': qty1,
                        'Кол-во в файле 2': qty2,
                        'Разница': qty2 - qty1
                    })
    
    # Создать DataFrame с результатами
    if comparison_results:
        result_df = pd.DataFrame(comparison_results)
        
        # Записать в Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='Сравнение', index=False)
            
            # Применить стили
            from .excel_writer import apply_excel_styles
            apply_excel_styles(writer)
        
        print(f"\n✅ Результаты сравнения записаны: {output_path}")
        print(f"   Найдено различий: {len(comparison_results)}")
        
        # Статистика
        added = len([r for r in comparison_results if r['Изменение'] == 'Добавлено'])
        removed = len([r for r in comparison_results if r['Изменение'] == 'Удалено'])
        changed = len([r for r in comparison_results if r['Изменение'] == 'Изменено'])
        
        print(f"   Добавлено: {added}")
        print(f"   Удалено: {removed}")
        print(f"   Изменено: {changed}")
    else:
        print("\n✅ Файлы идентичны, различий не найдено")
        
        # Все равно создать файл с сообщением
        result_df = pd.DataFrame([{'Результат': 'Файлы идентичны, различий не найдено'}])
        result_df.to_excel(output_path, sheet_name='Сравнение', index=False)


def main():
    """
    Главная функция CLI
    """
    parser = argparse.ArgumentParser(description="BOM Categorizer CLI")
    parser.add_argument("--inputs", nargs="+", help="Входные файлы (TXT, DOCX, XLSX)")
    parser.add_argument("--sheets", help="Листы Excel (через запятую)")
    parser.add_argument("--sheet", help="Конкретный лист Excel")
    parser.add_argument("--xlsx", help="Выходной Excel файл")
    parser.add_argument("--compare", nargs=2, metavar=('FILE1', 'FILE2'), help="Сравнить два BOM файла")
    parser.add_argument("--compare-output", help="Выходной файл для результатов сравнения")
    parser.add_argument("--txt-dir", help="Директория для TXT отчетов")
    parser.add_argument("--combine", action="store_true", help="Создать SUMMARY лист")
    parser.add_argument("--loose", action="store_true", help="Нестрогая классификация")
    parser.add_argument("--interactive", action="store_true", help="Интерактивная классификация")
    parser.add_argument("--no-interactive", action="store_true", help="Отключить автоматический интерактивный режим")
    parser.add_argument("--assign-json", default="rules.json", help="JSON файл с правилами")
    parser.add_argument("--exclude-items", help="Файл с элементами для исключения (формат: Название ИВП, количество)")
    
    args = parser.parse_args()
    
    # Режим сравнения файлов
    if args.compare:
        if not args.compare_output:
            print("❌ Ошибка: укажите --compare-output для сохранения результатов сравнения")
            return
        compare_bom_files(args.compare[0], args.compare[1], args.compare_output, args.no_interactive)
        return
    
    # Обычный режим обработки
    if not args.inputs or not args.xlsx:
        print("❌ Ошибка: укажите --inputs и --xlsx для обработки файлов")
        return
    
    # Load and combine inputs
    print(f"Запуск: split_bom --inputs {' '.join(args.inputs)} --xlsx {args.xlsx} {' --combine' if args.combine else ''} {' --txt-dir ' + args.txt_dir if args.txt_dir else ''}")
    
    df = load_and_combine_inputs(args.inputs, args.sheets, args.sheet)
    
    # Normalize and merge columns
    df, ref_col, desc_col, value_col, part_col, qty_col, mr_col = normalize_and_merge_columns(df)
    
    # Применить исключения элементов (если указано)
    if args.exclude_items:
        print(f"\n🔧 Применение исключений из файла: {args.exclude_items}")
        exclude_items = parse_exclude_items(args.exclude_items)
        if exclude_items:
            print(f"Найдено {len(exclude_items)} элементов для исключения")
            df = apply_exclusions(df, exclude_items, desc_col)
            df = df.reset_index(drop=True)
    
    # Фильтровать строки с пустым описанием ДО классификации
    # Это предотвращает попадание пустых строк в "unclassified"
    if desc_col in df.columns:
        initial_count = len(df)
        df = df[df[desc_col].notna() & (df[desc_col].astype(str).str.strip() != '')]
        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            print(f"Отфильтровано {filtered_count} строк с пустым описанием")
    
    # Проверяем, есть ли уже колонка category (файл был обработан ранее)
    has_existing_category = 'category' in df.columns
    
    if has_existing_category:
        print("✓ Обнаружена существующая колонка 'category' (файл уже был обработан ранее).")
        print("  Используем существующую классификацию без изменений.")
        # НЕ удаляем и НЕ перезапускаем классификацию!
        # Данные уже очищены и классифицированы, повторная классификация только ухудшит результат
    else:
        # Run classification только для новых файлов
        df = run_classification(df, ref_col, desc_col, value_col, part_col, args.loose)
    
    # Apply existing rules from JSON (только для новых файлов)
    if not has_existing_category:
        df = apply_rules_from_json(df, args.assign_json, desc_col, value_col, part_col, ref_col)
    
    # Interactive classification if needed
    unclassified_count = len(df[df["category"] == "unclassified"])
    auto_interactive = unclassified_count > 0 and not args.interactive and not args.no_interactive
    
    if args.interactive or auto_interactive:
        df = interactive_classification(df, desc_col, value_col, part_col, args.assign_json, auto_prompted=auto_interactive)
    
    # Очистить названия компонентов ТОЛЬКО для новых файлов
    # Для уже обработанных файлов данные уже очищены
    if not has_existing_category:
        from .formatters import clean_component_name
        if desc_col in df.columns:
            # Применяем clean_component_name ко всем значениям
            cleaned_values = []
            for val in df[desc_col]:
                if pd.notna(val):
                    cleaned_values.append(clean_component_name(str(val)))
                else:
                    cleaned_values.append(val)
            df[desc_col] = cleaned_values
    
    # Create outputs dictionary
    outputs = create_outputs_dict(df)
    
    # Re-apply rules after interactive classification (outputs need to be updated)
    if args.interactive or auto_interactive:
        # Re-create outputs to reflect new classifications
        outputs = create_outputs_dict(df)
    
    # Print summary
    print_summary(outputs)
    
    # Write Excel
    write_categorized_excel(outputs, df, args.xlsx, args.combine, desc_col)
    
    # Write TXT reports
    if args.txt_dir:
        write_txt_reports(outputs, args.txt_dir, desc_col)
    
    print("Готово.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
