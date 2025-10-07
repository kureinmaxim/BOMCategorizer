#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
from split_bom import find_column, normalize_column_names

# Читаем Plata_Preobrz.xlsx
df = pd.read_excel('Plata_Preobrz.xlsx')

# Проверка на пустую первую строку
if all(str(col).lower().startswith('unnamed') for col in df.columns):
    if not df.empty and df.iloc[0].notna().any():
        new_headers = df.iloc[0].fillna('').astype(str)
        df = df[1:].reset_index(drop=True)
        df.columns = new_headers

print("=== Исходный файл Plata_Preobrz.xlsx ===")
print(f"Колонки: {df.columns.tolist()}")
print(f"\nПервые 3 строки:")
print(df.head(3).to_string())

# Нормализуем колонки
lower_cols = normalize_column_names(list(df.columns))
print(f"\n\n=== Нормализованные колонки ===")
print(lower_cols)

# Ищем qty_col
qty_col = find_column([
    "qty", "quantity", "количество", "кол.", "кол-во", "кол. в ктд", "кол в ктд", "кол. в спецификации", "кол. в кдт",
    "кол. в ктд", "кол. в ктд, шт", "кол. в ктд (шт)", "кол. в ктд, шт."
], lower_cols)

print(f"\n\n=== qty_col найден: '{qty_col}' ===")

if qty_col:
    # Найти индекс в нормализованных колонках
    idx = lower_cols.index(qty_col)
    original_col = df.columns[idx]
    print(f"Оригинальная колонка: '{original_col}'")
    print(f"Первые 5 значений: {df[original_col].head().tolist()}")
else:
    print("qty_col НЕ найден!")

