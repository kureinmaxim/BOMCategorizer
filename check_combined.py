#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

xl = pd.ExcelFile('combined_test.xlsx')

print("=" * 80)
print("=== ПРОВЕРКА ОБЪЕДИНЕННОГО ФАЙЛА (новая Plata_Preobrz) ===")
print("=" * 80)

# 1. Порядок листов
print("\n1. ПОРЯДОК ЛИСТОВ:")
for i, sheet in enumerate(xl.sheet_names, 1):
    df = pd.read_excel('combined_test.xlsx', sheet_name=sheet)
    print(f"   {i}. {sheet:<30} - {len(df):>3} строк")

# 2. SUMMARY - источники
print("\n2. SUMMARY:")
df_summary = pd.read_excel('combined_test.xlsx', sheet_name='SUMMARY')
print(df_summary.to_string(index=False))

# 3. Резисторы - по номиналам (первые 5 из каждого файла)
print("\n3. РЕЗИСТОРЫ (первые 10):")
df_r = pd.read_excel('combined_test.xlsx', sheet_name='Резисторы')
if not df_r.empty:
    print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(10).to_string(index=False))

# 4. Конденсаторы - по номиналам
print("\n4. КОНДЕНСАТОРЫ (первые 10):")
df_c = pd.read_excel('combined_test.xlsx', sheet_name='Конденсаторы')
if not df_c.empty:
    print(df_c[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(10).to_string(index=False))

# 5. Микросхемы
print("\n5. МИКРОСХЕМЫ (первые 10):")
df_ic = pd.read_excel('combined_test.xlsx', sheet_name='Микросхемы')
if not df_ic.empty:
    print(df_ic[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(10).to_string(index=False))

# 6. Другие
print("\n6. ДРУГИЕ (все):")
df_other = pd.read_excel('combined_test.xlsx', sheet_name='Другие')
if not df_other.empty:
    print(df_other[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].to_string(index=False))

# 7. Кабели
print("\n7. КАБЕЛИ (все):")
df_cables = pd.read_excel('combined_test.xlsx', sheet_name='Кабели')
if not df_cables.empty:
    print(df_cables[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].to_string(index=False))

# 8. Не распределено
print("\n8. НЕ РАСПРЕДЕЛЕНО (если есть):")
df_un = pd.read_excel('combined_test.xlsx', sheet_name='Не распределено')
if not df_un.empty:
    print(f"   Всего: {len(df_un)} строк")
    print(df_un[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(5).to_string(index=False))

print("\n" + "=" * 80)
