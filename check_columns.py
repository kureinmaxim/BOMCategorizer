#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

df = pd.read_excel('combined_test.xlsx', sheet_name='Резисторы')
print("=== Все колонки ===")
print(df.columns.tolist())

print("\n=== Первая строка (DOCX) ===")
row0 = df.iloc[0]
for col in df.columns:
    print(f"{col}: {row0[col]}")

print("\n=== Последняя строка (Excel) ===")
row_last = df.iloc[-1]
for col in df.columns:
    print(f"{col}: {row_last[col]}")

