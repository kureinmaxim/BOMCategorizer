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
                read_kwargs = {}
                
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
                            
                            if has_mostly_unnamed and not dfi.empty and dfi.iloc[0].notna().any():
                                first_row_text = ' '.join(str(val).lower() for val in dfi.iloc[0] if pd.notna(val))
                                looks_like_header = any(keyword in first_row_text for keyword in 
                                    ['наименование', 'количество', 'кол.', 'код', 'description', 'qty'])
                                
                                if looks_like_header:
                                    new_headers = dfi.iloc[0].fillna('').astype(str)
                                    dfi = dfi[1:].reset_index(drop=True)
                                    dfi.columns = new_headers
                            
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
                    if all(str(col).lower().startswith('unnamed') for col in df.columns):
                        if not df.empty and df.iloc[0].notna().any():
                            new_headers = df.iloc[0].fillna('').astype(str)
                            df = df[1:].reset_index(drop=True)
                            df.columns = new_headers
                    
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
                        
                        if has_mostly_unnamed and not df_local.empty and df_local.iloc[0].notna().any():
                            first_row_text = ' '.join(str(val).lower() for val in df_local.iloc[0] if pd.notna(val))
                            looks_like_header = any(keyword in first_row_text for keyword in 
                                ['наименование', 'количество', 'кол.', 'код', 'description', 'qty'])
                            
                            if looks_like_header:
                                new_headers = df_local.iloc[0].fillna('').astype(str)
                                df_local = df_local[1:].reset_index(drop=True)
                                df_local.columns = new_headers
                        
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
    desc_col = find_column(["description", "desc", "наименование", "имя", "item", "part", "part name", "наим."], list(df.columns))
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
            
            mask = df["category"] == "unclassified"
            
            if contains:
                blob = (
                    df.get("description", pd.Series([""] * len(df))).astype(str).str.lower().fillna("") + " " +
                    df.get("value", pd.Series([""] * len(df))).astype(str).str.lower().fillna("") + " " +
                    df.get("part", pd.Series([""] * len(df))).astype(str).str.lower().fillna("") + " " +
                    df.get("reference", pd.Series([""] * len(df))).astype(str).str.lower().fillna("")
                )
                mask = mask & blob.str.contains(re.escape(contains), na=False)
            
            if regex:
                try:
                    r = re.compile(regex, re.IGNORECASE)
                    text_series = (
                        df.get("description", "").astype(str).fillna("") + " " +
                        df.get("value", "").astype(str).fillna("") + " " +
                        df.get("part", "").astype(str).fillna("") + " " +
                        df.get("reference", "").astype(str).fillna("")
                    )
                    mask = mask & text_series.apply(lambda t: bool(r.search(t)))
                except Exception:
                    pass
            
            matched_count = mask.sum()
            if matched_count > 0:
                df.loc[mask, "category"] = cat
                rules_applied_count += matched_count
        
        if rules_applied_count > 0:
            print(f"✅ {rules_applied_count} элементов автоматически классифицированы по сохраненным правилам")
    
    except Exception as exc:
        print(f"⚠️ Не удалось применить правила из {rules_json}: {exc}")
    
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


def main():
    """
    Главная функция CLI
    """
    parser = argparse.ArgumentParser(description="BOM Categorizer CLI")
    parser.add_argument("--inputs", nargs="+", required=True, help="Входные файлы (TXT, DOCX, XLSX)")
    parser.add_argument("--sheets", help="Листы Excel (через запятую)")
    parser.add_argument("--sheet", help="Конкретный лист Excel")
    parser.add_argument("--xlsx", required=True, help="Выходной Excel файл")
    parser.add_argument("--txt-dir", help="Директория для TXT отчетов")
    parser.add_argument("--combine", action="store_true", help="Создать SUMMARY лист")
    parser.add_argument("--loose", action="store_true", help="Нестрогая классификация")
    parser.add_argument("--interactive", action="store_true", help="Интерактивная классификация")
    parser.add_argument("--no-interactive", action="store_true", help="Отключить автоматический интерактивный режим")
    parser.add_argument("--assign-json", default="rules.json", help="JSON файл с правилами")
    
    args = parser.parse_args()
    
    # Load and combine inputs
    print(f"Запуск: split_bom --inputs {' '.join(args.inputs)} --xlsx {args.xlsx} {' --combine' if args.combine else ''} {' --txt-dir ' + args.txt_dir if args.txt_dir else ''}")
    
    df = load_and_combine_inputs(args.inputs, args.sheets, args.sheet)
    
    # Normalize and merge columns
    df, ref_col, desc_col, value_col, part_col, qty_col, mr_col = normalize_and_merge_columns(df)
    
    # Фильтровать строки с пустым описанием ДО классификации
    # Это предотвращает попадание пустых строк в "unclassified"
    if desc_col in df.columns:
        initial_count = len(df)
        df = df[df[desc_col].notna() & (df[desc_col].astype(str).str.strip() != '')]
        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            print(f"Отфильтровано {filtered_count} строк с пустым описанием")
    
    # Run classification
    df = run_classification(df, ref_col, desc_col, value_col, part_col, args.loose)
    
    # Apply existing rules from JSON
    df = apply_rules_from_json(df, args.assign_json, desc_col, value_col, part_col, ref_col)
    
    # Interactive classification if needed
    unclassified_count = len(df[df["category"] == "unclassified"])
    auto_interactive = unclassified_count > 0 and not args.interactive and not args.no_interactive
    
    if args.interactive or auto_interactive:
        df = interactive_classification(df, desc_col, value_col, part_col, args.assign_json, auto_prompted=auto_interactive)
    
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
