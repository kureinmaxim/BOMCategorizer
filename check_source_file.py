#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

print("="*80)
print("=== ПРОВЕРКА source_file ===")
print("="*80)

# Проверяем SUMMARY
df_summary = pd.read_excel('All_IBP_out.xlsx', sheet_name='SUMMARY')
print("\nSUMMARY:")
print(df_summary.to_string(index=False))

# Проверяем SOURCES
df_sources = pd.read_excel('All_IBP_out.xlsx', sheet_name='SOURCES')
print("\n\nSOURCES:")
print(df_sources.to_string(index=False))

# Проверяем резисторы (первые 10)
print("\n\n=== РЕЗИСТОРЫ (первые 10 с source_file) ===")
df_r = pd.read_excel('All_IBP_out.xlsx', sheet_name='Резисторы')
if 'source_file' in df_r.columns:
    cols = ['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']
    print(df_r[cols].head(10).to_string(index=False))
    
    # Уникальные source_file
    print(f"\n\nУникальные source_file в резисторах:")
    for sf in df_r['source_file'].unique()[:10]:
        count = (df_r['source_file'] == sf).sum()
        print(f"  - {sf}: {count} шт")
elif 'source_sheet' in df_r.columns:
    print("❌ Колонка source_sheet ещё существует!")
    cols = ['№ п/п', 'Наименование ИВП', 'source_file', 'source_sheet', 'Кол-во']
    print(df_r[[c for c in cols if c in df_r.columns]].head(10).to_string(index=False))
else:
    cols = ['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']
    print(df_r[[c for c in cols if c in df_r.columns]].head(10).to_string(index=False))

print("\n" + "="*80)

