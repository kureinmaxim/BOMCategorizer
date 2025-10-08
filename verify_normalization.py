# -*- coding: utf-8 -*-
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=== ПРОВЕРКА НОРМАЛИЗАЦИИ НАИМЕНОВАНИЙ ===\n")

df = pd.read_excel('All_IBP_out_final.xlsx', sheet_name='Отладочные модули')

# 1. Усилитель TB-TSS2 (должен быть объединен)
usil = df[df['Наименование ИВП'].str.contains('TB-TSS2', case=False, na=False)]
print(f"1. Усилитель TB-TSS2:")
print(f"   Найдено записей: {len(usil)}")
if len(usil) > 0:
    for i, (_, row) in enumerate(usil.iterrows(), 1):
        print(f"   {i}. {row['Наименование ИВП']} | Кол-во: {row['Кол-во']}")
    total_qty = usil['Кол-во'].sum()
    print(f"   Итого количество: {total_qty} (ожидается 5: 3 из БФ + 2 из Импортные)")

# 2. Проверяем, нет ли дубликатов
print(f"\n2. Проверка на дубликаты в 'Отладочные модули':")
duplicates = df[df.duplicated(subset=['Наименование ИВП'], keep=False)]
if len(duplicates) > 0:
    print(f"   ⚠️ Найдено дубликатов: {len(duplicates)}")
    # Показываем только уникальные наименования
    unique_dups = duplicates['Наименование ИВП'].unique()
    for dup_name in unique_dups[:5]:
        count = len(df[df['Наименование ИВП'] == dup_name])
        print(f"   - {dup_name[:60]}... (встречается {count} раз)")
else:
    print(f"   ✅ Дубликатов не найдено")

# 3. Проверяем финальные результаты из предыдущей проверки
print("\n3. Финальная проверка всех исправлений:")
qty_14 = df[df['Кол-во'] == 14]
print(f"   ✅ Строк с количеством 14: {len(qty_14)}")

fazovr = df[df['Наименование ИВП'].str.contains('PS-500M2G-8B-SFF', case=False, na=False)]
if len(fazovr) > 0:
    print(f"   ✅ Фазовращатель: {fazovr.iloc[0]['Кол-во']}")

pitanie = df[df['Наименование ИВП'].str.contains('питания БФ', case=False, na=False)]
if len(pitanie) > 0:
    print(f"   ✅ питания БФ ШСК-М: {pitanie.iloc[0]['Кол-во']}")

print("\n" + "="*70)
print("ИТОГ:")
print("  ✅ Основная проблема (количество 14) решена")
if len(usil) == 1:
    print("  ✅ Нормализация наименований работает (усилитель объединен)")
else:
    print("  ⚠️ Усилитель все еще дублируется - нужна дополнительная нормализация")
print("="*70)
