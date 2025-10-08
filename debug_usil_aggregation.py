# -*- coding: utf-8 -*-
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=== ОТЛАДКА АГРЕГАЦИИ УСИЛИТЕЛЯ ===\n")

# Читаем исходный файл
all_sheets = pd.read_excel('All_IBP.xlsx', sheet_name=None)

print("1. Усилитель в ИСХОДНЫХ листах:")
total_source_qty = 0
for sheet_name, df in all_sheets.items():
    matches = df[df.astype(str).apply(lambda x: x.str.contains('TB-TSS2', case=False, na=False)).any(axis=1)]
    if len(matches) > 0:
        name_cols = [c for c in df.columns if 'наименование' in c.lower()]
        qty_cols = [c for c in df.columns if 'количество' in c.lower() or 'unnamed: 1' in c.lower()]
        
        if name_cols and qty_cols:
            name_col = name_cols[0]
            qty_col = qty_cols[0]
            
            for idx, row in matches.iterrows():
                qty = row[qty_col]
                name = row[name_col]
                print(f"   Лист '{sheet_name}': {name[:60]}... | Кол-во: {qty}")
                try:
                    total_source_qty += float(qty)
                except:
                    pass

print(f"   ИТОГО в исходнике: {total_source_qty}\n")

# Читаем выходной файл
df_out = pd.read_excel('All_IBP_out_final.xlsx', sheet_name='Отладочные модули')

print("2. Усилитель в ВЫХОДНОМ файле:")
usil = df_out[df_out['Наименование ИВП'].str.contains('TB-TSS2', case=False, na=False)]
total_out_qty = 0
for i, (_, row) in enumerate(usil.iterrows(), 1):
    print(f"   {i}. {row['Наименование ИВП']} | Кол-во: {row['Кол-во']} | Источник: {row.get('Источник', 'N/A')}")
    total_out_qty += row['Кол-во']

print(f"   ИТОГО в выходном: {total_out_qty}")

print(f"\n3. ПРОБЛЕМА:")
if total_out_qty < total_source_qty:
    print(f"   ⚠️ Потеряно {total_source_qty - total_out_qty} единиц при обработке!")
    print(f"   Причина: группировка объединяет строки с одинаковым наименованием,")
    print(f"   но берет количество только из ОДНОЙ строки вместо СУММЫ.")
else:
    print(f"   ✅ Количество сохранено")
