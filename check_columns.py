# -*- coding: utf-8 -*-
import pandas as pd

df = pd.read_excel('D:/!ШСК_М/Project/Example/ШСК_М_АМФИ.411734.013_out.xlsx', nrows=5)

print("=" * 60)
print("Колонки в выходном файле:")
print("=" * 60)
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

print("\n" + "=" * 60)
print("Первые 2 строки данных:")
print("=" * 60)
print(df.head(2))

