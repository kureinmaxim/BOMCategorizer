#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

xl = pd.ExcelFile('test_controller.xlsx')
print("=== Листы в порядке ===")
for i, sheet in enumerate(xl.sheet_names, 1):
    df = pd.read_excel('test_controller.xlsx', sheet_name=sheet)
    print(f"{i}. {sheet} - {len(df)} строк")

# Проверим, где находятся отладочные платы
print("\n=== Ищем A1, A2 ===")
for sheet in xl.sheet_names:
    df = pd.read_excel('test_controller.xlsx', sheet_name=sheet)
    if 'reference' in df.columns:
        a_items = df[df['reference'].str.contains('A1|A2', na=False, case=False)]
        if not a_items.empty:
            print(f"\nНайдено в листе '{sheet}':")
            print(a_items[['reference', 'Наименование ИВП', 'Кол-во']].to_string(index=False))

