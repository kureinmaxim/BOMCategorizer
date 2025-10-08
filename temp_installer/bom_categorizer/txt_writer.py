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
        
        # Очистить названия компонентов и извлечь ТУ
        cleaned_names = []
        tu_codes = []
        
        for idx, row in output_df.iterrows():
            text = str(row[desc_col_found]) if pd.notna(row[desc_col_found]) else ""
            note = str(row['note']) if 'note' in output_df.columns and pd.notna(row['note']) else ""
            
            # Очистить название
            cleaned_text = clean_component_name(text, note)
            
            # Извлечь ТУ
            cleaned_text, tu_code = extract_tu_code(cleaned_text)
            
            # Если ТУ был в note, используем его
            if note and '|' in note:
                parts = note.split('|')
                if len(parts) >= 2 and 'ТУ' in parts[1]:
                    tu_code = parts[1].strip()
            
            cleaned_names.append(cleaned_text)
            tu_codes.append(tu_code)
        
        output_df[desc_col_found] = cleaned_names
        output_df['ТУ'] = tu_codes
        
        # Найти колонку с количеством
        qty_col_candidates = ['Общее количество', 'qty', 'Количество', '_merged_qty_']
        qty_col_found = None
        for candidate in qty_col_candidates:
            if candidate in output_df.columns:
                qty_col_found = candidate
                break
        
        # Фильтровать строки с пустым описанием
        output_df = output_df[output_df[desc_col_found].notna() & (output_df[desc_col_found].astype(str).str.strip() != '')]
        
        if output_df.empty:
            continue
        
        # Записать TXT файл
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"=== {category_name.upper()} ===\n")
            f.write(f"Всего элементов: {len(output_df)}\n")
            f.write("=" * 80 + "\n\n")
            
            for idx, (_, row) in enumerate(output_df.iterrows(), start=1):
                name = row[desc_col_found]
                tu = row.get('ТУ', '')
                qty = row.get(qty_col_found, 1) if qty_col_found else 1
                
                line = f"{idx}. {name}"
                if tu and str(tu).strip() and str(tu).strip() != '-':
                    line += f" | ТУ: {tu}"
                line += f" | Кол-во: {qty} шт"
                
                f.write(line + "\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Всего записей: {len(output_df)}\n")
    
    print(f"TXT files written to: {txt_dir}")
