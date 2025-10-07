#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
from split_bom import parse_docx

# Читаем Plata_Preobrz.xlsx
print("=== Plata_Preobrz.xlsx ===")
df1 = pd.read_excel('example/Plata_Preobrz.xlsx')

# Проверка на пустую первую строку
if all(str(col).lower().startswith('unnamed') for col in df1.columns):
    if not df1.empty and df1.iloc[0].notna().any():
        new_headers = df1.iloc[0].fillna('').astype(str)
        df1 = df1[1:].reset_index(drop=True)
        df1.columns = new_headers

print(f"Колонки: {df1.columns.tolist()}")
print(f"Строк: {len(df1)}")
print(f"\nПервые 3 строки:")
for col in df1.columns:
    print(f"  {col}: {df1[col].head(3).tolist()}")

# Читаем Плата контроллера .docx
print("\n\n=== Плата контроллера .docx ===")
df2 = parse_docx('Плата контроллера .docx')
print(f"Колонки: {df2.columns.tolist()}")
print(f"Строк: {len(df2)}")
print(f"\nПервые 3 строки:")
for col in df2.columns:
    print(f"  {col}: {df2[col].head(3).tolist()}")

# Объединяем
print("\n\n=== ПОСЛЕ CONCAT ===")
all_rows = [df1, df2]
combined = pd.concat(all_rows, ignore_index=True, sort=False)
print(f"Колонки: {combined.columns.tolist()}")
print(f"Строк: {len(combined)}")
print(f"\nПервые 3 строки из Plata_Preobrz:")
for col in combined.columns:
    print(f"  {col}: {combined[col].head(3).tolist()}")

