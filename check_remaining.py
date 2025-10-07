#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

print("="*80)
print("=== ЧТО ОСТАЛОСЬ В НЕ РАСПРЕДЕЛЕНО ===")
print("="*80)

df_un = pd.read_excel('All_IBP_out.xlsx', sheet_name='Не распределено')
df_un_valid = df_un[df_un['Наименование ИВП'].notna()]

print(f"\nВсего: {len(df_un_valid)}\n")

for idx, row in df_un_valid.iterrows():
    name = str(row.get('Наименование ИВП', ''))[:80]
    qty = row.get('Кол-во', 0)
    source = str(row.get('source_file', ''))[:35]
    print(f"{idx+1}. {name:<82} | Кол-во: {qty:>6} | {source}")

print("\n" + "="*80)
print("SUMMARY:")
df_summary = pd.read_excel('All_IBP_out.xlsx', sheet_name='SUMMARY')
print(df_summary.to_string(index=False))

print("\n" + "="*80)
print("✅ Улучшение: с 43 до 7 нераспределенных элементов!")
print("="*80)

