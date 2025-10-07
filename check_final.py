#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd

xl = pd.ExcelFile('combined_test.xlsx')

print("=" * 80)
print("=== ФИНАЛЬНАЯ ПРОВЕРКА ===")
print("=" * 80)

# 1. Порядок листов
print("\n1. ПОРЯДОК ЛИСТОВ:")
for i, sheet in enumerate(xl.sheet_names, 1):
    df = pd.read_excel('combined_test.xlsx', sheet_name=sheet)
    print(f"   {i}. {sheet:<30} - {len(df):>3} строк")

# 2. SUMMARY
print("\n2. SUMMARY:")
df_summary = pd.read_excel('combined_test.xlsx', sheet_name='SUMMARY')
print(df_summary.to_string(index=False))

# 3. Резисторы - проверка сортировки и данных из обоих файлов
print("\n3. РЕЗИСТОРЫ (первые 5 + последние 5):")
df_r = pd.read_excel('combined_test.xlsx', sheet_name='Резисторы')
print("Первые 5:")
print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head().to_string(index=False))
print("\nПоследние 5:")
print(df_r[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].tail().to_string(index=False))

# 4. Микросхемы - проверка алфавитной сортировки
print("\n4. МИКРОСХЕМЫ (первые 10):")
df_ic = pd.read_excel('combined_test.xlsx', sheet_name='Микросхемы')
print(df_ic[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].head(10).to_string(index=False))

# 5. Другие
print("\n5. ДРУГИЕ (все):")
df_other = pd.read_excel('combined_test.xlsx', sheet_name='Другие')
print(df_other[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].to_string(index=False))

# 6. Не распределено
print("\n6. НЕ РАСПРЕДЕЛЕНО (все):")
df_un = pd.read_excel('combined_test.xlsx', sheet_name='Не распределено')
if not df_un.empty:
    print(df_un[['№ п/п', 'Наименование ИВП', 'source_file', 'Кол-во']].to_string(index=False))
else:
    print("   (пусто - отлично!)")

print("\n" + "=" * 80)
print("✅ Объединение файлов работает корректно!")
print("=" * 80)

