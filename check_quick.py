#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

print("=== РЕЗИСТОРЫ (первые 5) ===")
df_r = pd.read_excel('combined_test.xlsx', sheet_name='Резисторы')
print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head().to_string(index=False))

print("\n=== ДРУГИЕ (все) ===")
df_other = pd.read_excel('combined_test.xlsx', sheet_name='Другие')
print(df_other[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].to_string(index=False))

print("\n=== НЕ РАСПРЕДЕЛЕНО (первые 10) ===")
df_un = pd.read_excel('combined_test.xlsx', sheet_name='Не распределено')
print(df_un[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(10).to_string(index=False))

