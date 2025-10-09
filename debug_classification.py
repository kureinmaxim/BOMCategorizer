# -*- coding: utf-8 -*-
import pandas as pd
import sys
sys.path.insert(0, '.')

from bom_categorizer.utils import normalize_column_names, find_column

# Читаем файл
df = pd.read_excel('D:/!ШСК_М/Project/Example/ШСК_М_АМФИ.411734.013_out.xlsx', nrows=5)

print("="*70)
print("ОРИГИНАЛЬНЫЕ КОЛОНКИ:")
print("="*70)
for i, col in enumerate(df.columns, 1):
    print(f"{i}. '{col}'")

# Нормализуем
original_cols = list(df.columns)
lower_cols = normalize_column_names(original_cols)

print("\n" + "="*70)
print("НОРМАЛИЗОВАННЫЕ КОЛОНКИ:")
print("="*70)
for i, (orig, norm) in enumerate(zip(original_cols, lower_cols), 1):
    print(f"{i}. '{orig}' -> '{norm}'")

# Переименовываем
rename_map = {orig: norm for orig, norm in zip(original_cols, lower_cols)}
df = df.rename(columns=rename_map)

# Ищем колонку описания
desc_col = find_column([
    "description", "desc", "наименование ивп", "наименование", 
    "имя", "item", "part", "part name", "наим."
], list(df.columns))

print("\n" + "="*70)
print("РЕЗУЛЬТАТ ПОИСКА КОЛОНКИ ОПИСАНИЯ:")
print("="*70)
if desc_col:
    print(f"[OK] НАЙДЕНА: '{desc_col}'")
else:
    print("[ERROR] НЕ НАЙДЕНА!")
    print("\nДоступные колонки после нормализации:")
    for col in df.columns:
        print(f"  - '{col}'")

