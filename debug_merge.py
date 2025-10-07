#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

# Симулируем concat двух файлов
df1 = pd.read_excel('Plata_Preobrz.xlsx')
if all(str(col).lower().startswith('unnamed') for col in df1.columns):
    if not df1.empty and df1.iloc[0].notna().any():
        new_headers = df1.iloc[0].fillna('').astype(str)
        df1 = df1[1:].reset_index(drop=True)
        df1.columns = new_headers

from split_bom import parse_docx
df2 = parse_docx('Плата контроллера .docx')

# Объединяем
combined = pd.concat([df1, df2], ignore_index=True, sort=False)

print("=== Колонки после concat ===")
print(combined.columns.tolist())

print("\n=== Первые 3 строки (из Plata_Preobrz) ===")
for col in combined.columns:
    print(f"  {col}: {combined[col].head(3).tolist()}")

# Проверяем логику создания _merged_description_
from split_bom import normalize_column_names

lower_cols = normalize_column_names(list(combined.columns))
print("\n=== Нормализованные колонки ===")
print(lower_cols)

# Ищем desc_col
from split_bom import find_column
desc_col = find_column(["description", "desc", "наименование", "имя", "item", "part", "part name", "наим."], lower_cols)
print(f"\n=== desc_col найден: {desc_col} ===")

# Проверяем логику merge
if not desc_col or combined[desc_col].isna().all():
    print("\n=== desc_col пустой или NaN, ищем possible_desc_cols ===")
    possible_desc_cols = [col for col in combined.columns if any(
        col.startswith(prefix) for prefix in ["description", "наименование", "desc", "имя"]
    )]
    print(f"possible_desc_cols: {possible_desc_cols}")
    
    if len(possible_desc_cols) > 1:
        print("\nСоздаем _merged_description_")
        def merge_desc(row):
            for col in possible_desc_cols:
                val = row.get(col)
                if pd.notna(val) and str(val).strip():
                    return val
            return None
        
        combined["_merged_description_"] = combined.apply(merge_desc, axis=1)
        print("\n=== Первые 5 значений _merged_description_ ===")
        print(combined["_merged_description_"].head().tolist())

