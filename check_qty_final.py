#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

print("=== РЕЗИСТОРЫ (первые 5 + последние 5) ===")
df_r = pd.read_excel('combined_test.xlsx', sheet_name='Резисторы')
print("Первые 5:")
print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head().to_string(index=False))
print("\nПоследние 5:")
print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].tail().to_string(index=False))

print("\n\n=== МИКРОСХЕМЫ (первые 7) ===")
df_ic = pd.read_excel('combined_test.xlsx', sheet_name='Микросхемы')
print(df_ic[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(7).to_string(index=False))

print("\n\n=== КОНДЕНСАТОРЫ (первые 5) ===")
df_c = pd.read_excel('combined_test.xlsx', sheet_name='Конденсаторы')
print(df_c[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head().to_string(index=False))

# Проверка на нулевые количества
print("\n\n=== ПРОВЕРКА КОЛИЧЕСТВ ===")
zero_qty_resistors = df_r[df_r['Кол-во'] == 0]
if not zero_qty_resistors.empty:
    print(f"❌ Найдено {len(zero_qty_resistors)} резисторов с Кол-во = 0")
    print(zero_qty_resistors[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(3).to_string(index=False))
else:
    print("✅ Все резисторы имеют правильное количество!")

zero_qty_ics = df_ic[df_ic['Кол-во'] == 0]
if not zero_qty_ics.empty:
    print(f"\n❌ Найдено {len(zero_qty_ics)} микросхем с Кол-во = 0")
    print(zero_qty_ics[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(3).to_string(index=False))
else:
    print("✅ Все микросхемы имеют правильное количество!")

