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
from .podborka_extractor import extract_podbor_elements


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


def multiply_quantities(df: pd.DataFrame, multiplier: int) -> pd.DataFrame:
    """
    Умножает количество всех элементов на заданный множитель
    
    Args:
        df: DataFrame с данными
        multiplier: Множитель для количества
        
    Returns:
        DataFrame с умноженными количествами
    """
    if multiplier == 1:
        return df
    
    # Найти колонку с количеством (без учета регистра)
    qty_col = None
    qty_keywords = ["qty", "quantity", "количество", "кол.", "кол-во", "кол-в", "_merged_qty_"]
    
    # Сначала попробуем find_column (для обратной совместимости)
    qty_col = find_column(qty_keywords, list(df.columns))
    
    # Если не нашли, ищем без учета регистра
    if not qty_col:
        columns_lower = {col.lower(): col for col in df.columns}
        for keyword in qty_keywords:
            if keyword.lower() in columns_lower:
                qty_col = columns_lower[keyword.lower()]
                break
        
        # Если все еще не нашли, ищем частичное совпадение без учета регистра
        if not qty_col:
            for keyword in qty_keywords:
                for col in df.columns:
                    if keyword.lower() in col.lower():
                        qty_col = col
                        break
                if qty_col:
                    break
    
    if qty_col and qty_col in df.columns:
        # Умножаем количество
        for idx in df.index:
            current_qty = df.loc[idx, qty_col]
            if pd.notna(current_qty):
                try:
                    df.loc[idx, qty_col] = int(float(current_qty)) * multiplier
                except (ValueError, TypeError):
                    pass  # Оставляем как есть, если не можем преобразовать
    
    return df


def load_and_combine_inputs(input_paths: List[str], sheets_str: Optional[str] = None, sheet: Optional[str] = None) -> pd.DataFrame:
    """
    Загружает и объединяет данные из всех входных файлов
    
    Args:
        input_paths: Список путей к входным файлам (формат: "файл" или "файл:количество")
        sheets_str: Строка с номерами листов Excel (через запятую)
        sheet: Конкретный лист для чтения
        
    Returns:
        Объединенный DataFrame со всеми данными
    """
    all_rows: List[pd.DataFrame] = []
    
    for input_spec in input_paths:
        # Парсим формат "файл:количество"
        # Проверяем, есть ли двоеточие и является ли последняя часть числом
        multiplier = 1
        input_path = input_spec
        
        if ':' in input_spec:
            # Разделяем по последнему двоеточию
            parts = input_spec.rsplit(':', 1)
            if len(parts) == 2:
                # Проверяем, является ли последняя часть числом
                try:
                    potential_multiplier = int(parts[1])
                    # Если это число, то это множитель, а не часть пути
                    if potential_multiplier > 0:
                        input_path = parts[0]
                        multiplier = potential_multiplier
                    elif potential_multiplier <= 0:
                        print(f" Множитель должен быть положительным числом: {input_spec}", file=sys.stderr)
                        # Оставляем multiplier = 1 и input_path = input_spec
                except ValueError:
                    # Последняя часть не число - это просто часть пути (например, C:\path)
                    pass
        ext = os.path.splitext(input_path)[1].lower()
        
        # TXT parsing
        if ext in [".txt"]:
            try:
                df_txt = parse_txt_like(input_path)
                
                # Добавляем source_file ПЕРЕД извлечением подборов (нужно для пометки)
                df_txt["source_file"] = os.path.basename(input_path)
                df_txt["source_sheet"] = ""
                
                # Извлечь подборные элементы из примечаний (с пометкой source_file)
                df_txt = extract_podbor_elements(df_txt)
                
                df_txt = multiply_quantities(df_txt, multiplier)
                all_rows.append(df_txt)
                if multiplier > 1:
                    print(f"  [x{multiplier}] Умножено количество элементов из '{os.path.basename(input_path)}'")
            except Exception as exc:
                print(f" Не удалось прочитать TXT '{input_path}': {exc}", file=sys.stderr)
        
        # DOCX parsing
        elif ext in [".doc", ".docx"]:
            try:
                df_docx = parse_docx(input_path)
                
                # Добавляем source_file ПЕРЕД извлечением подборов (нужно для пометки)
                df_docx["source_file"] = os.path.basename(input_path)
                df_docx["source_sheet"] = ""
                
                # Извлечь подборные элементы из примечаний (с пометкой source_file)
                df_docx = extract_podbor_elements(df_docx)
                
                df_docx = multiply_quantities(df_docx, multiplier)
                all_rows.append(df_docx)
                if multiplier > 1:
                    print(f"  [x{multiplier}] Умножено количество элементов из '{os.path.basename(input_path)}'")
            except Exception as exc:
                print(f" Не удалось прочитать DOCX '{input_path}': {exc}", file=sys.stderr)
        
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
                            dfi = multiply_quantities(dfi, multiplier)
                            all_rows.append(dfi)
                        except Exception as exc:
                            print(f" Не удалось прочитать лист '{sh}' из '{input_path}': {exc}", file=sys.stderr)
                
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
                    df = multiply_quantities(df, multiplier)
                    all_rows.append(df)
                
                else:
                    # Листы не указаны - читаем ВСЕ листы
                    all_sheets_data = pd.read_excel(input_path, sheet_name=None, **{k: v for k, v in read_kwargs.items() if k != 'sheet_name'})
                    
                    # Создаем обратный маппинг: русское имя листа → английская категория
                    from .excel_writer import RUS_SHEET_NAMES
                    sheet_to_category = {v: k for k, v in RUS_SHEET_NAMES.items()}
                    
                    for sheet_name, df_local in all_sheets_data.items():
                        # Пропускаем служебные листы
                        if str(sheet_name).upper() in ['SUMMARY', 'SOURCES', 'INFO']:
                            continue
                        
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
                        
                        # ВАЖНО: Если лист имеет имя категории, сохраняем категорию из имени листа
                        # Это предотвращает переклассификацию уже обработанных файлов
                        if str(sheet_name) in sheet_to_category:
                            category_eng = sheet_to_category[str(sheet_name)]
                            df_local["category"] = category_eng
                            print(f"  [КАТЕГОРИЯ] Лист '{sheet_name}' → category='{category_eng}' (сохранено из xlsx)")
                        
                        df_local = multiply_quantities(df_local, multiplier)
                        all_rows.append(df_local)
                
                if multiplier > 1:
                    print(f"  [x{multiplier}] Умножено количество элементов из '{os.path.basename(input_path)}'")
            
            except Exception as exc:
                print(f" Не удалось прочитать Excel '{input_path}': {exc}", file=sys.stderr)
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


def smart_aggregate_source_file(source_files) -> str:
    """
    Умная агрегация source_file для компактного отображения подборов/замен
    
    Входные данные: ['Plata_preobrz.docx', 'Plata_preobrz.docx (п/б R48*)', 'Plata_preobrz.docx (п/б R49*)']
    Результат: 'Plata_preobrz.docx (п/б R48*), (п/б R49*)'
    
    Args:
        source_files: Серия значений source_file для агрегации
        
    Returns:
        Компактная строка с общим файлом и всеми пометками
    """
    import re
    
    sources = [str(v) for v in source_files if pd.notna(v) and str(v).strip()]
    if not sources:
        return ''
    
    # Извлекаем базовые файлы и пометки
    base_files = set()
    tags = []
    
    for source in sources:
        # Паттерн для извлечения базового файла и пометок
        # Формат: "filename.ext (п/б R48*)" или "filename.ext"
        # Ищем все пометки типа (п/б ...) или (зам ...)
        tag_matches = re.findall(r'\((?:п/б|зам)\s+[^)]+\)', source)
        
        # Базовый файл - это всё до первой пометки
        if tag_matches:
            base_file = source[:source.index(tag_matches[0])].strip()
            base_files.add(base_file)
            tags.extend(tag_matches)
        else:
            # Нет пометок - просто базовый файл
            base_files.add(source.strip())
    
    # Если только один базовый файл и есть пометки - компактный формат
    if len(base_files) == 1 and tags:
        base_file = list(base_files)[0]
        unique_tags = []
        seen = set()
        for tag in tags:
            if tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)
        return f"{base_file} {', '.join(unique_tags)}"
    
    # Иначе просто объединяем через запятую (стандартная логика)
    return ', '.join(sorted(set(sources)))


def aggregate_duplicate_items(df: pd.DataFrame, desc_col: str, combine_across_files: bool = False) -> pd.DataFrame:
    """
    Объединяет одинаковые элементы из одного источника (документа)
    Суммирует количество и объединяет позиционные обозначения через запятую
    
    Args:
        df: DataFrame с данными
        desc_col: Название колонки с описанием
        combine_across_files: Если True, объединяет одинаковые элементы из разных файлов
        
    Returns:
        DataFrame с объединенными элементами
    """
    if desc_col not in df.columns:
        return df
    
    # Нормализуем описания для группировки (убираем лишние пробелы, нормализуем символы)
    def normalize_description(desc):
        """Нормализует описание для сравнения"""
        if pd.isna(desc):
            return desc
        desc_str = str(desc)
        # Убираем символ ± (может быть в разных вариантах, или вообще отсутствовать)
        desc_str = desc_str.replace('±', '')
        # Нормализуем пробел между единицами измерения и процентами (всегда добавляем пробел)
        # Это решает проблему: "100 Ом 5%-Т" vs "100 Ом5%-Т" -> "100 Ом 5%-Т"
        desc_str = re.sub(r'(Ом|пФ|нФ|мкФ|мФ|кОм|МОм|Гн|мГн|мкГн|нГн)\s*(\d+%)', r'\1 \2', desc_str, flags=re.IGNORECASE)
        
        # ВАЖНО: НЕ нормализуем дефисы в артикулах модулей питания!
        # Артикулы типа МДМ30-1В05ТУП, МАА20-1С05СБП не должны превращаться в МДМ30 - 1В05ТУП
        # Проверяем, есть ли артикул модуля в строке
        module_article_pattern = re.compile(r'М[ДАФПАСЕ][МАДСИОЕ]?\d+[-\w]+[ТУП|СБП|СУФ|ТУФ|СБН|ФБП]', re.IGNORECASE)
        has_module_article = module_article_pattern.search(desc_str)
        
        # Также НЕ нормализуем дефисы для артикулов разъемов:
        # СНП347-14ВП31-1, ШП1-56-12К, 2РМ18БПН4Г1В1В и т.д.
        # Паттерн: буквы+цифры-буквы+цифры-... (например СНП347-14ВП31-1)
        connector_article_pattern = re.compile(r'[А-ЯЁ]{2,}\d+[-\d]+[А-ЯЁ]+[-\d]+(?:[А-ЯЁ]+)?', re.IGNORECASE)
        has_connector_article = connector_article_pattern.search(desc_str)
        
        if not has_module_article and not has_connector_article:
            # Нет артикула модуля/разъема - нормализуем пробелы вокруг дефисов (всегда " - ")
            # Это решает проблему: "P1 - 12 - 0,125 - 1" vs "P1 - 12 - 0,125-1" -> "P1 - 12 - 0,125 - 1"
            desc_str = re.sub(r'\s*-\s*', ' - ', desc_str)
        
        # Убираем множественные пробелы (в том числе там, где был ±)
        desc_str = re.sub(r'\s+', ' ', desc_str)
        # ОСТОРОЖНО! Удаляем производителя ТОЛЬКО если он в конце строки после "ф."
        # Это решает проблему: "PAT-0+ ф. Mini-Circuits" vs "PAT-0+" -> "PAT-0+"
        # НО НЕ ТРОГАЕМ другие части описания типа "К10-17в-М1500-100 пФ"
        desc_str = re.sub(r'\s+ф\.\s*[A-Za-zА-ЯЁа-яё0-9\s\-]+$', '', desc_str)
        # Убираем пробелы в начале и конце
        return desc_str.strip()
    
    # Создаем временную колонку для нормализованного описания
    df['_normalized_desc_'] = df[desc_col].apply(normalize_description)
    
    # Найти колонку quantity
    qty_col = find_column([
        "qty", "quantity", "количество", "кол.", "кол-во", "_merged_qty_"
    ], list(df.columns))
    
    # Найти колонку reference
    ref_col = find_column([
        "ref", "reference", "designator", "refdes", "обозначение", "позиционное обозначение"
    ], list(df.columns))
    
    if not qty_col and not ref_col:
        return df
    
    # Группируем по source_file, source_sheet и нормализованному description
    group_cols = []
    # Если combine_across_files=True, НЕ группируем по source_file
    # (чтобы одинаковые элементы из разных файлов объединялись)
    if not combine_across_files and 'source_file' in df.columns:
        group_cols.append('source_file')
    if 'source_sheet' in df.columns:
        group_cols.append('source_sheet')
    group_cols.append('_normalized_desc_')
    
    # Группируем по категории ТОЛЬКО если НЕ объединяем файлы
    # (иначе XLSX с category='dev_boards' и DOCX с category=NaN не объединятся!)
    if not combine_across_files and 'category' in df.columns:
        group_cols.append('category')
    
    # Создаем копию для агрегации
    agg_dict = {}
    
    # Суммируем количество
    if qty_col:
        agg_dict[qty_col] = 'sum'
    
    # Объединяем reference через запятую
    if ref_col:
        agg_dict[ref_col] = lambda x: ', '.join(str(v) for v in x if pd.notna(v) and str(v).strip())
    
    # Если combine_across_files=True, объединяем source_file через умную агрегацию
    if combine_across_files and 'source_file' in df.columns:
        agg_dict['source_file'] = smart_aggregate_source_file
    
    # Берем первое значение для остальных колонок
    for col in df.columns:
        if col not in group_cols and col not in agg_dict:
            agg_dict[col] = 'first'
    
    # Группируем и агрегируем
    try:
        df_agg = df.groupby(group_cols, as_index=False, dropna=False).agg(agg_dict)
        
        # Обновляем исходную колонку description нормализованным значением
        if '_normalized_desc_' in df_agg.columns and desc_col in df_agg.columns:
            df_agg[desc_col] = df_agg['_normalized_desc_']
            df_agg = df_agg.drop(columns=['_normalized_desc_'])
        
        return df_agg
    except Exception as e:
        print(f" Предупреждение: не удалось агрегировать дубликаты: {e}")
        # Удаляем временную колонку даже в случае ошибки
        if '_normalized_desc_' in df.columns:
            df = df.drop(columns=['_normalized_desc_'])
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
    
    ВАЖНО: Если у строки уже есть категория (из xlsx файла), она НЕ перезаписывается
    
    Returns:
        DataFrame с добавленной колонкой 'category'
    """
    df = df.copy()
    
    # Проверяем, есть ли уже колонка category
    has_existing_category = 'category' in df.columns
    
    categories: List[str] = []
    for idx, row in df.iterrows():
        # Если категория уже есть и не пустая - сохраняем её
        if has_existing_category:
            existing_cat = row.get('category')
            if pd.notna(existing_cat) and str(existing_cat).strip():
                categories.append(str(existing_cat).strip())
                continue
        
        # Иначе классифицируем
        ref = row.get(ref_col) if ref_col else None
        desc = row.get(desc_col) if desc_col else None
        val = row.get(value_col) if value_col else None
        part = row.get(part_col) if part_col else None
        src_file = row.get('source_file') if 'source_file' in df.columns else None
        note_val = row.get('note') if 'note' in df.columns else None
        group_type_val = row.get('group_type') if 'group_type' in df.columns else None
        categories.append(classify_row(ref, desc, val, part, strict=not loose, source_file=src_file, note=note_val, group_type=group_type_val))
    
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
        print(f"\nВНИМАНИЕ: Обнаружено {len(uncls)} нераспределённых элементов!")
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


def split_by_source_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    Разделяет DataFrame на группы по source_file с пустыми строками между ними
    
    Args:
        df: DataFrame с данными одной категории
        
    Returns:
        DataFrame с добавленными пустыми строками-разделителями между источниками
    """
    if df.empty or 'source_file' not in df.columns:
        return df
    
    # Получаем уникальные источники в порядке их появления
    unique_sources = df['source_file'].unique()
    
    if len(unique_sources) <= 1:
        # Если только один источник, разделение не нужно
        return df
    
    result_parts = []
    
    for i, source in enumerate(unique_sources):
        # Добавляем данные из этого источника
        source_data = df[df['source_file'] == source]
        result_parts.append(source_data)
        
        # Добавляем пустую строку-разделитель после каждого источника, кроме последнего
        if i < len(unique_sources) - 1:
            empty_row = pd.DataFrame([{col: '' for col in df.columns}])
            result_parts.append(empty_row)
    
    # Объединяем все части
    result = pd.concat(result_parts, ignore_index=True) if result_parts else pd.DataFrame()
    
    return result


def create_outputs_dict(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Создает словарь выходных DataFrame по категориям
    
    Returns:
        Словарь {category_key: DataFrame}
    """
    outputs = {
        "ics": split_by_source_file(df[df["category"] == "ics"]),
        "resistors": split_by_source_file(df[df["category"] == "resistors"]),
        "capacitors": split_by_source_file(df[df["category"] == "capacitors"]),
        "inductors": split_by_source_file(df[df["category"] == "inductors"]),
        "semiconductors": split_by_source_file(df[df["category"] == "semiconductors"]),
        "connectors": split_by_source_file(df[df["category"] == "connectors"]),
        "optics": split_by_source_file(df[df["category"] == "optics"]),
        "power_modules": split_by_source_file(df[df["category"] == "power_modules"]),
        "cables": split_by_source_file(df[df["category"] == "cables"]),
        "our_developments": split_by_source_file(df[df["category"] == "our_developments"]),
        "dev_boards": split_by_source_file(df[df["category"] == "dev_boards"]),
        "rf_modules": split_by_source_file(df[df["category"] == "rf_modules"]),
        "others": split_by_source_file(df[df["category"] == "others"]),
        "unclassified": split_by_source_file(df[df["category"] == "unclassified"]),
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
        print(f" Файл исключений не найден: {exclude_file_path}")
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
                            print(f" Ошибка в строке {line_num}: неверное количество '{parts[1].strip()}'")
                    else:
                        print(f" Ошибка в строке {line_num}: неверный формат")
                else:
                    print(f" Ошибка в строке {line_num}: отсутствует запятая")
    except Exception as e:
        print(f" Ошибка при чтении файла исключений: {e}")
    
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
        print(f" Колонка '{desc_col}' не найдена, исключения не применены")
        return df
    
    # Найти колонку количества
    qty_col = find_column(df, ['qty', '_merged_qty_', 'Количество', 'количество', 'Кол-во', 'кол-во'])
    if not qty_col or qty_col not in df.columns:
        print(" Колонка количества не найдена, исключения не могут быть применены")
        return df
    
    excluded_count = 0
    reduced_count = 0
    
    for exclude_name, exclude_qty in exclude_items:
        # Найти строки с совпадающим названием (частичное совпадение)
        mask = df[desc_col].astype(str).str.contains(exclude_name, case=False, na=False, regex=False)
        matching_indices = df[mask].index.tolist()
        
        if not matching_indices:
            print(f" Элемент '{exclude_name}' не найден в BOM")
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
                print(f"[OK] Исключен элемент '{item_name}' (qty: {current_qty})")
            else:
                # Уменьшить количество
                new_qty = current_qty - remaining_exclude_qty
                df.loc[idx, qty_col] = new_qty
                print(f"[OK] Уменьшено количество '{df.loc[idx, desc_col]}': {current_qty} -> {new_qty}")
                remaining_exclude_qty = 0
                reduced_count += 1
        
        if remaining_exclude_qty > 0:
            print(f"[ПРЕДУПРЕЖДЕНИЕ] Не удалось исключить полное количество '{exclude_name}': осталось {remaining_exclude_qty}")
    
    if excluded_count > 0 or reduced_count > 0:
        print(f"\n[ИТОГО] Исключено: {excluded_count} строк, уменьшено: {reduced_count} строк")
    
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
    print(f"\n[ОБРАБОТКА] Файл: {file_path}")
    
    # Загрузить файл
    df = load_and_combine_inputs([file_path], None, None)
    
    # Нормализовать колонки
    df, ref_col, desc_col, value_col, part_col, qty_col, mr_col = normalize_and_merge_columns(df)
    
    # Проверить существующую категорию
    has_existing_category = 'category' in df.columns
    
    # Сохранить оригинальные описания для сравнения (ДО применения clean_component_name)
    if desc_col in df.columns and '_comparison_original_' not in df.columns:
        df['_comparison_original_'] = df[desc_col].copy()
    
    # Очистить названия компонентов ДО агрегации для НОВЫХ файлов
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
    
    # Агрегировать одинаковые элементы из DOC/DOCX/TXT файлов
    has_docx_data = 'zone' in df.columns or (
        find_column(["reference", "ref"], list(df.columns)) and 
        'source_file' in df.columns
    )
    if has_docx_data:
        df = aggregate_duplicate_items(df, desc_col)
    
    # Фильтровать пустые строки
    if desc_col in df.columns:
        df = df[df[desc_col].notna() & (df[desc_col].astype(str).str.strip() != '')]
    
    if not has_existing_category:
        # Классифицировать
        df = run_classification(df, ref_col, desc_col, value_col, part_col, loose=False)
        
        # Применить правила из JSON
        df = apply_rules_from_json(df, "rules.json", desc_col, value_col, part_col, ref_col)
        
        # Автоматически перенести unclassified в 'others'
        unclassified_mask = df["category"] == "unclassified"
        unclassified_count = unclassified_mask.sum()
        if unclassified_count > 0:
            print(f"[INFO] Перенос {unclassified_count} нераспределенных элементов в категорию 'Другие'")
            df.loc[unclassified_mask, "category"] = "others"
    
    # Удалить все элементы с "АМФИ" из выходного файла
    if desc_col in df.columns:
        initial_count = len(df)
        df = df[~df[desc_col].astype(str).str.upper().str.contains('АМФИ', na=False)]
        df = df.reset_index(drop=True)
        removed_count = initial_count - len(df)
        if removed_count > 0:
            print(f"[ФИЛЬТР] Удалено {removed_count} элементов с 'АМФИ'")
    
    # Создать outputs словарь
    outputs = create_outputs_dict(df)
    
    # ВАЖНО: Применить format_excel_output для каждой категории
    # Это приводит данные к стандартному виду (извлекает ТУ, добавляет колонки, нормализует)
    # НО ТОЛЬКО если файл еще не обработан!
    from .excel_writer import format_excel_output, RUS_SHEET_NAMES
    processed_outputs = {}
    
    for category, cat_df in outputs.items():
        if not cat_df.empty:
            # Проверить, обработан ли уже этот файл (есть ли колонки "ТУ" и "Примечание")
            has_tu_column = 'ТУ' in cat_df.columns or 'ту' in cat_df.columns
            has_primechanie_column = 'Примечание' in cat_df.columns or 'примечание' in cat_df.columns
            
            if has_existing_category and has_tu_column and has_primechanie_column:
                # Файл уже обработан, НЕ применяем format_excel_output заново
                print(f"[INFO] Категория '{category}' уже обработана, пропускаем повторную обработку")
                processed_outputs[category] = cat_df
            else:
                # Получить русское название категории для правильной обработки
                sheet_name = RUS_SHEET_NAMES.get(category, category)
                
                # Применить полную обработку (извлечение ТУ, очистка, сортировка)
                processed_df = format_excel_output(
                    cat_df, 
                    sheet_name, 
                    desc_col,
                    force_reprocess=False  # НЕ пересоздавать колонки для уже обработанных файлов
                )
                processed_outputs[category] = processed_df
        else:
            processed_outputs[category] = cat_df
    
    print(f"[OK] Файл обработан: {len(df)} элементов в {len(outputs)} категориях")
    
    return processed_outputs


def normalize_name_for_comparison(name: str) -> str:
    """
    Нормализует название для сравнения - удаляет лишние пробелы
    
    Args:
        name: Исходное название
        
    Returns:
        Нормализованное название
    """
    import re
    if not name or pd.isna(name):
        return ""
    
    name = str(name).strip()
    
    # Удаляем множественные пробелы
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def compare_processed_files(file1_path: str, file2_path: str, output_path: str) -> bool:
    """
    Сравнивает два УЖЕ ОБРАБОТАННЫХ BOM файла (с категориями)
    
    Args:
        file1_path: Путь к первому файлу (базовый)
        file2_path: Путь ко второму файлу (новый)
        output_path: Путь к выходному файлу с результатами
        
    Returns:
        True если сравнение успешно, False если файлы не обработанные
    """
    import pandas as pd
    
    # Маппинг названий листов на категории
    CATEGORY_SHEETS = {
        'Резисторы': 'Резисторы',
        'Конденсаторы': 'Конденсаторы',
        'Индуктивности': 'Индуктивности',
        'Полупроводники': 'Полупроводники',
        'Микросхемы': 'Микросхемы',
        'Разъемы': 'Разъемы',
        'Оптика': 'Оптика',
        'СВЧ модули': 'СВЧ модули',
        'Кабели': 'Кабели',
        'Модули питания': 'Модули питания',
        'Отладочные платы': 'Отладочные платы',
        'Наши разработки': 'Наши разработки',
        'Другие': 'Другие'
    }
    
    IGNORED_SHEETS = ['SOURCES', 'SUMMARY', 'Не распределено', 'INFO']
    
    print("=" * 80)
    print("[СРАВНЕНИЕ] ОБРАБОТАННЫХ BOM ФАЙЛОВ")
    print("=" * 80)
    
    # Проверяем что оба файла - обработанные
    try:
        xl1 = pd.ExcelFile(file1_path, engine='openpyxl')
        xl2 = pd.ExcelFile(file2_path, engine='openpyxl')
    except Exception as e:
        print(f"❌ Ошибка чтения файлов: {e}")
        return False
    
    # Проверяем наличие листов категорий
    sheets1 = set(xl1.sheet_names)
    sheets2 = set(xl2.sheet_names)
    
    category_sheets1 = sheets1 & set(CATEGORY_SHEETS.keys())
    category_sheets2 = sheets2 & set(CATEGORY_SHEETS.keys())
    
    if not category_sheets1 and not category_sheets2:
        print("❌ Файлы не являются обработанными BOM файлами")
        print(f"   Файл 1 листы: {', '.join(xl1.sheet_names)}")
        print(f"   Файл 2 листы: {', '.join(xl2.sheet_names)}")
        return False
    
    print(f"\n[ФАЙЛ 1] {os.path.basename(file1_path)}")
    print(f"   Найдено категорий: {len(category_sheets1)}")
    
    print(f"\n[ФАЙЛ 2] {os.path.basename(file2_path)}")
    print(f"   Найдено категорий: {len(category_sheets2)}")
    
    # Объединяем все категории из обоих файлов
    all_categories = sorted(category_sheets1 | category_sheets2)
    
    comparison_results = []
    
    print(f"\n[АНАЛИЗ] Сравнение по категориям...")
    
    for category in all_categories:
        print(f"\n  📂 {category}")
        
        # Читаем данные из первого файла
        items1 = {}
        if category in category_sheets1:
            try:
                df1 = pd.read_excel(file1_path, sheet_name=category, engine='openpyxl')
                # Ищем колонки
                name_col = None
                qty_col = None
                for col in ['Наименование ИВП', 'Наименование', 'наименование ивп']:
                    if col in df1.columns:
                        name_col = col
                        break
                for col in ['Кол-во', 'Количество', 'qty']:
                    if col in df1.columns:
                        qty_col = col
                        break
                
                if name_col and qty_col:
                    for _, row in df1.iterrows():
                        name = str(row[name_col]) if pd.notna(row[name_col]) else ""
                        if name and name != 'nan':
                            # Нормализуем название
                            name_normalized = normalize_name_for_comparison(name)
                            qty = 0
                            if pd.notna(row[qty_col]):
                                try:
                                    qty = int(float(row[qty_col]))
                                except:
                                    pass
                            items1[name_normalized] = items1.get(name_normalized, 0) + qty
                print(f"     Файл 1: {len(items1)} уникальных компонентов")
            except Exception as e:
                print(f"     ⚠️ Ошибка чтения из файла 1: {e}")
        
        # Читаем данные из второго файла
        items2 = {}
        if category in category_sheets2:
            try:
                df2 = pd.read_excel(file2_path, sheet_name=category, engine='openpyxl')
                # Ищем колонки
                name_col = None
                qty_col = None
                for col in ['Наименование ИВП', 'Наименование', 'наименование ивп']:
                    if col in df2.columns:
                        name_col = col
                        break
                for col in ['Кол-во', 'Количество', 'qty']:
                    if col in df2.columns:
                        qty_col = col
                        break
                
                if name_col and qty_col:
                    for _, row in df2.iterrows():
                        name = str(row[name_col]) if pd.notna(row[name_col]) else ""
                        if name and name != 'nan':
                            # Нормализуем название
                            name_normalized = normalize_name_for_comparison(name)
                            qty = 0
                            if pd.notna(row[qty_col]):
                                try:
                                    qty = int(float(row[qty_col]))
                                except:
                                    pass
                            items2[name_normalized] = items2.get(name_normalized, 0) + qty
                print(f"     Файл 2: {len(items2)} уникальных компонентов")
            except Exception as e:
                print(f"     ⚠️ Ошибка чтения из файла 2: {e}")
        
        # Сравниваем
        all_items = set(list(items1.keys()) + list(items2.keys()))
        category_diffs = 0
        
        for item_name in sorted(all_items):
            if not item_name:
                continue
            
            qty1 = items1.get(item_name, 0)
            qty2 = items2.get(item_name, 0)
            
            if qty1 != qty2:
                category_diffs += 1
                if qty1 == 0:
                    change_type = 'Добавлено'
                elif qty2 == 0:
                    change_type = 'Удалено'
                else:
                    change_type = 'Изменено'
                
                comparison_results.append({
                    'Категория': category,
                    'Изменение': change_type,
                    'Наименование ИВП': item_name,
                    'Кол-во в файле 1': qty1,
                    'Кол-во в файле 2': qty2,
                    'Разница': qty2 - qty1
                })
        
        print(f"     Различий: {category_diffs}")
    
    # Создаем отчет
    if comparison_results:
        result_df = pd.DataFrame(comparison_results)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='Сравнение', index=False)
            
            # Применяем стили
            from .excel_writer import apply_excel_styles
            apply_excel_styles(writer)
        
        print(f"\n[УСПЕХ] Результаты сравнения записаны: {output_path}")
        print(f"        Найдено различий: {len(comparison_results)}")
        
        added = len([r for r in comparison_results if r['Изменение'] == 'Добавлено'])
        removed = len([r for r in comparison_results if r['Изменение'] == 'Удалено'])
        changed = len([r for r in comparison_results if r['Изменение'] == 'Изменено'])
        
        print(f"   Добавлено: {added}")
        print(f"   Удалено: {removed}")
        print(f"   Изменено: {changed}")
    else:
        print("\n[РЕЗУЛЬТАТ] Файлы идентичны, различий не найдено")
        
        result_df = pd.DataFrame([{'Результат': 'Файлы идентичны, различий не найдено'}])
        result_df.to_excel(output_path, sheet_name='Сравнение', index=False)
    
    return True


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
    print("[СРАВНЕНИЕ] BOM ФАЙЛОВ")
    print("=" * 80)
    
    # Обработать оба файла
    outputs1 = process_file_for_comparison(file1_path, no_interactive)
    outputs2 = process_file_for_comparison(file2_path, no_interactive)
    
    # Получить все категории
    all_categories = sorted(set(list(outputs1.keys()) + list(outputs2.keys())))
    
    print(f"\n[АНАЛИЗ] Сравнение по категориям...")
    
    # Создать список для результатов
    comparison_results = []
    
    for category in all_categories:
        df1 = outputs1.get(category, pd.DataFrame())
        df2 = outputs2.get(category, pd.DataFrame())
        
        if df1.empty and df2.empty:
            continue
        
        # Найти колонку описания (используем оригинальные описания для сравнения)
        desc_col1 = find_column(df1, ['_comparison_original_', 'Наименование ИВП', 'наименование ивп', 'description', '_merged_description_']) if not df1.empty else None
        desc_col2 = find_column(df2, ['_comparison_original_', 'Наименование ИВП', 'наименование ивп', 'description', '_merged_description_']) if not df2.empty else None
        
        # Найти колонку количества
        qty_col1 = find_column(df1, ['Кол-во', 'qty', '_merged_qty_', 'Количество']) if not df1.empty else None
        qty_col2 = find_column(df2, ['Кол-во', 'qty', '_merged_qty_', 'Количество']) if not df2.empty else None
        
        # Создать словари для сравнения: нормализованное_название -> количество
        items1 = {}
        if not df1.empty and desc_col1 and qty_col1:
            for _, row in df1.iterrows():
                name = str(row[desc_col1]) if pd.notna(row[desc_col1]) else ""
                # Нормализуем название для сравнения (удаляем ТУ-коды и т.д.)
                normalized_name = normalize_name_for_comparison(name)
                qty_val = row[qty_col1]
                # Обработка пустых значений, NaN и строк
                if pd.notna(qty_val) and str(qty_val).strip():
                    try:
                        qty = int(float(qty_val))
                    except (ValueError, TypeError):
                        qty = 0
                else:
                    qty = 0
                items1[normalized_name] = items1.get(normalized_name, 0) + qty
        
        items2 = {}
        if not df2.empty and desc_col2 and qty_col2:
            for _, row in df2.iterrows():
                name = str(row[desc_col2]) if pd.notna(row[desc_col2]) else ""
                # Нормализуем название для сравнения (удаляем ТУ-коды и т.д.)
                normalized_name = normalize_name_for_comparison(name)
                qty_val = row[qty_col2]
                # Обработка пустых значений, NaN и строк
                if pd.notna(qty_val) and str(qty_val).strip():
                    try:
                        qty = int(float(qty_val))
                    except (ValueError, TypeError):
                        qty = 0
                else:
                    qty = 0
                items2[normalized_name] = items2.get(normalized_name, 0) + qty
        
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
        
        print(f"\n[УСПЕХ] Результаты сравнения записаны: {output_path}")
        print(f"        Найдено различий: {len(comparison_results)}")
        
        # Статистика
        added = len([r for r in comparison_results if r['Изменение'] == 'Добавлено'])
        removed = len([r for r in comparison_results if r['Изменение'] == 'Удалено'])
        changed = len([r for r in comparison_results if r['Изменение'] == 'Изменено'])
        
        print(f"   Добавлено: {added}")
        print(f"   Удалено: {removed}")
        print(f"   Изменено: {changed}")
    else:
        print("\n[РЕЗУЛЬТАТ] Файлы идентичны, различий не найдено")
        
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
    parser.add_argument("--exclude-podbor", action="store_true", help="Исключить подборы и замены из выходного файла")
    
    args = parser.parse_args()
    
    # Режим сравнения файлов
    if args.compare:
        if not args.compare_output:
            print("[ОШИБКА] укажите --compare-output для сохранения результатов сравнения")
            return
        compare_bom_files(args.compare[0], args.compare[1], args.compare_output, args.no_interactive)
        return
    
    # Обычный режим обработки
    if not args.inputs or not args.xlsx:
        print("[ОШИБКА] укажите --inputs и --xlsx для обработки файлов")
        return
    
    # Load and combine inputs
    print(f"Запуск: split_bom --inputs {' '.join(args.inputs)} --xlsx {args.xlsx} {' --combine' if args.combine else ''} {' --txt-dir ' + args.txt_dir if args.txt_dir else ''}")
    
    df = load_and_combine_inputs(args.inputs, args.sheets, args.sheet)
    
    # Normalize and merge columns
    df, ref_col, desc_col, value_col, part_col, qty_col, mr_col = normalize_and_merge_columns(df)
    
    # Определяем, есть ли уже обработанные данные (с колонкой 'category')
    has_existing_category = 'category' in df.columns
    
    # Очистить названия компонентов ДО агрегации
    # Это критически важно для правильного объединения XLSX и DOCX файлов
    if desc_col in df.columns:
        from .formatters import clean_component_name, extract_tu_code
        from .parsers import normalize_dashes
        
        if has_existing_category:
            # Если есть колонка category, очищаем ТОЛЬКО строки без категории (новые данные)
            print("[ОЧИСТКА] Нормализация описаний для новых компонентов (без категории)...")
            cleaned_values = []
            for idx, val in enumerate(df[desc_col]):
                # Если у строки нет категории или категория пустая - очищаем
                has_cat = pd.notna(df.loc[idx, 'category']) and str(df.loc[idx, 'category']).strip()
                if not has_cat and pd.notna(val):
                    cleaned_values.append(clean_component_name(str(val)))
                else:
                    cleaned_values.append(val)
            df[desc_col] = cleaned_values
        else:
            # Если нет колонки category, очищаем все
            print("[ОЧИСТКА] Нормализация описаний компонентов...")
            cleaned_values = []
            for val in df[desc_col]:
                if pd.notna(val):
                    cleaned_values.append(clean_component_name(str(val)))
                else:
                    cleaned_values.append(val)
            df[desc_col] = cleaned_values
        
        # Нормализовать тире в других критичных колонках для правильного объединения
        # Конвертация .doc → .docx может заменять дефисы на типографские тире
        print("[НОРМАЛИЗАЦИЯ] Приведение всех видов тире к единому формату...")
        
        # Нормализация в позиционных обозначениях (reference)
        if ref_col and ref_col in df.columns:
            for idx in df.index:
                val = df.loc[idx, ref_col]
                if pd.notna(val):
                    df.loc[idx, ref_col] = normalize_dashes(str(val))
        
        # Нормализация в номиналах (value)
        if value_col and value_col in df.columns:
            for idx in df.index:
                val = df.loc[idx, value_col]
                if pd.notna(val):
                    df.loc[idx, value_col] = normalize_dashes(str(val))
        
        # Нормализация в колонке ТУ (если есть)
        for tu_col_name in ['ТУ', 'ту', 'TU', 'tu']:
            if tu_col_name in df.columns:
                for idx in df.index:
                    val = df.loc[idx, tu_col_name]
                    if pd.notna(val):
                        df.loc[idx, tu_col_name] = normalize_dashes(str(val))
        
        # КРИТИЧЕСКИ ВАЖНО: Извлечь ТУ-коды из DOCX файлов ДО агрегации
        # Это приводит DOCX к тому же формату что и XLSX (с отдельной колонкой ТУ)
        # Проверяем, есть ли DOCX данные (по наличию колонки 'note')
        if 'note' in df.columns:
            print("[ИЗВЛЕЧЕНИЕ ТУ] Извлечение ТУ-кодов из наименований (для унификации с XLSX)...")
            
            # Если колонки ТУ еще нет - создаем
            if 'ТУ' not in df.columns and 'ту' not in df.columns:
                df['_extracted_tu_'] = ''
            
            for idx in df.index:
                # Извлекаем ТУ только если:
                # 1. У строки нет категории (DOCX) ИЛИ
                # 2. У строки есть note но нет ТУ (DOCX с производителем)
                has_cat = 'category' in df.columns and pd.notna(df.loc[idx, 'category']) and str(df.loc[idx, 'category']).strip()
                has_tu = ('ТУ' in df.columns and pd.notna(df.loc[idx, 'ТУ']) and str(df.loc[idx, 'ТУ']).strip()) or \
                         ('ту' in df.columns and pd.notna(df.loc[idx, 'ту']) and str(df.loc[idx, 'ту']).strip())
                
                # Если это XLSX с категорией и ТУ - пропускаем
                if has_cat and has_tu:
                    continue
                
                # Извлекаем ТУ из описания
                desc_val = df.loc[idx, desc_col]
                if pd.notna(desc_val):
                    cleaned_desc, tu_code = extract_tu_code(str(desc_val))
                    
                    # Обновляем описание (без ТУ)
                    df.loc[idx, desc_col] = cleaned_desc
                    
                    # Сохраняем ТУ
                    if tu_code:
                        if '_extracted_tu_' in df.columns:
                            df.loc[idx, '_extracted_tu_'] = tu_code
                        
                        # Если есть note с производителем, объединяем: "ТУ | производитель"
                        note_val = df.loc[idx, 'note'] if 'note' in df.columns else ''
                        if note_val and pd.notna(note_val) and str(note_val).strip():
                            # Проверяем, не является ли note ТУ-кодом (чтобы не дублировать)
                            note_str = str(note_val).strip()
                            if 'ТУ' not in note_str.upper():
                                # note это производитель, объединяем
                                df.loc[idx, 'note'] = tu_code + ' | ' + note_str
                            else:
                                # note уже содержит ТУ
                                df.loc[idx, 'note'] = note_str
                        else:
                            # Нет note - просто ТУ
                            df.loc[idx, 'note'] = tu_code
    
    # Агрегировать одинаковые элементы (объединяем дубликаты)
    # Проверяем, есть ли данные из DOC/DOCX (по наличию колонки 'zone' или большого количества reference)
    has_docx_data = 'zone' in df.columns or (
        find_column(["reference", "ref"], list(df.columns)) and 
        'source_file' in df.columns
    )
    
    # ВСЕГДА агрегируем если используется --combine (даже для XLSX файлов)
    # ИЛИ если это DOC/DOCX/TXT данные
    if has_docx_data or args.combine:
        print("[АГРЕГАЦИЯ] Объединение одинаковых элементов из документов...")
        initial_count = len(df)
        # Если используется --combine, объединяем элементы из разных файлов
        df = aggregate_duplicate_items(df, desc_col, combine_across_files=args.combine)
        final_count = len(df)
        if initial_count != final_count:
            print(f"[OK] Объединено: {initial_count} -> {final_count} строк (сэкономлено {initial_count - final_count})")
    
    # Применить исключения элементов (если указано)
    if args.exclude_items:
        print(f"\n🔧 Применение исключений из файла: {args.exclude_items}")
        exclude_items = parse_exclude_items(args.exclude_items)
        if exclude_items:
            print(f"Найдено {len(exclude_items)} элементов для исключения")
            df = apply_exclusions(df, exclude_items, desc_col)
            df = df.reset_index(drop=True)
    
    # Исключить подборы и замены (если указано)
    if args.exclude_podbor:
        print(f"\n🔧 Исключение подборов и замен из выходного файла")
        initial_count = len(df)
        
        # Фильтруем строки, у которых в source_file есть теги подборов/замен
        # Теги: (п/б ...), (зам ...), (подбор ...)
        if 'source_file' in df.columns:
            podbor_mask = df['source_file'].astype(str).str.contains(
                r'\(п/б\s|\\(зам\s|\(подбор\s',
                regex=True,
                case=False,
                na=False
            )
            df = df[~podbor_mask]
            df = df.reset_index(drop=True)
            final_count = len(df)
            excluded_count = initial_count - final_count
            if excluded_count > 0:
                print(f"[OK] Исключено {excluded_count} позиций подборов/замен")
        else:
            print("[WARNING] Колонка 'source_file' не найдена, пропуск фильтрации")
    
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
        # Если есть колонка category, классифицируем ТОЛЬКО строки без категории
        rows_without_category = df['category'].isna() | (df['category'].astype(str).str.strip() == '')
        rows_without_category_count = rows_without_category.sum()
        
        if rows_without_category_count > 0:
            print(f"[КЛАССИФИКАЦИЯ] Обнаружено {rows_without_category_count} новых компонентов без категории.")
            print("  Классифицируем только новые компоненты...")
            
            # Классифицируем только строки без категории
            df_to_classify = df[rows_without_category].copy()
            df_to_classify = run_classification(df_to_classify, ref_col, desc_col, value_col, part_col, args.loose)
            df_to_classify = apply_rules_from_json(df_to_classify, args.assign_json, desc_col, value_col, part_col, ref_col)
            
            # Обновляем категории в основном DataFrame
            df.loc[rows_without_category, 'category'] = df_to_classify['category'].values
        else:
            print("[OK] Все компоненты уже классифицированы.")
    else:
        # Run classification для всех строк
        print("[КЛАССИФИКАЦИЯ] Классификация всех компонентов...")
        df = run_classification(df, ref_col, desc_col, value_col, part_col, args.loose)
        df = apply_rules_from_json(df, args.assign_json, desc_col, value_col, part_col, ref_col)
    
    # Interactive classification if needed
    unclassified_count = len(df[df["category"] == "unclassified"])
    auto_interactive = unclassified_count > 0 and not args.interactive and not args.no_interactive
    
    if args.interactive or auto_interactive:
        df = interactive_classification(df, desc_col, value_col, part_col, args.assign_json, auto_prompted=auto_interactive)
    
    # Удалить все элементы с "АМФИ" из выходного файла
    if desc_col in df.columns:
        initial_count = len(df)
        df = df[~df[desc_col].astype(str).str.upper().str.contains('АМФИ', na=False)]
        df = df.reset_index(drop=True)
        removed_count = initial_count - len(df)
        if removed_count > 0:
            print(f"[ФИЛЬТР] Удалено {removed_count} элементов с 'АМФИ' из выходного файла")
    
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
