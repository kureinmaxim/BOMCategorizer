#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

print("=== РЕЗИСТОРЫ (первые 3 + последние 3) ===")
df_r = pd.read_excel('combined_test.xlsx', sheet_name='Резисторы')
print(f"Колонки: {df_r.columns.tolist()}")
print("\nПервые 3 (из DOCX):")
print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(3).to_string(index=False))
print("\nПоследние 3 (из Excel):")
print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].tail(3).to_string(index=False))

print("\n\n=== МИКРОСХЕМЫ (первые 5) ===")
df_ic = pd.read_excel('combined_test.xlsx', sheet_name='Микросхемы')
print(df_ic[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(5).to_string(index=False))

print("\n\n=== ДРУГИЕ (все) ===")
df_other = pd.read_excel('combined_test.xlsx', sheet_name='Другие')
print(df_other[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].to_string(index=False))

print("\n\n✅ ВСЕ ОТЛИЧНО!" if df_r['Наименование ИВП'].notna().all() else "\n\n❌ Есть NaN в Наименование ИВП")

