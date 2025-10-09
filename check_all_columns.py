# -*- coding: utf-8 -*-
import pandas as pd

# Читаем исходный файл (_out.xlsx)
df = pd.read_excel('D:/!ШСК_М/Project/Example/ШСК_М_АМФИ.411734.013_out.xlsx')

print("="*70)
print("ВСЕ КОЛОНКИ В ФАЙЛЕ:")
print("="*70)
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

# Найдем строку где DS18B20
ds_row = df[df.iloc[:, 1].astype(str).str.contains('DS18B20', na=False)]

if len(ds_row) > 0:
    print("\n" + "="*70)
    print("ПРИМЕР СТРОКИ DS18B20:")
    print("="*70)
    first = ds_row.iloc[0]
    for col in df.columns:
        print(f"  {col}: {first[col]}")

