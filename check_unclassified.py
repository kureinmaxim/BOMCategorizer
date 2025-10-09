# -*- coding: utf-8 -*-
import pandas as pd

# Читаем выходной файл
df = pd.read_excel('test_output.xlsx', sheet_name='Не распределено')

print("="*70)
print(f"Всего нераспределенных элементов: {len(df)}")
print("="*70)

print("\nПервые 10 элементов:")
print("-"*70)
for i, row in df.head(10).iterrows():
    name = row.get('Наименование ИВП', '')
    tu = row.get('ТУ', '')
    print(f"{i+1}. {name[:50]} | ТУ: {tu}")

# Проверим, есть ли у них описание
print("\n" + "="*70)
print("Проверка наличия описания:")
print("="*70)
empty_count = df['Наименование ИВП'].isna().sum()
print(f"Пустых описаний: {empty_count}")
print(f"Непустых описаний: {len(df) - empty_count}")

if len(df) > 0:
    print("\nПример первого элемента:")
    first = df.iloc[0]
    for col in df.columns:
        print(f"  {col}: {first[col]}")

