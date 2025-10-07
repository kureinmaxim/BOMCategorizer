#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
from collections import Counter

print("="*80)
print("=== АНАЛИЗ НЕРАСПРЕДЕЛЕННЫХ ЭЛЕМЕНТОВ ===")
print("="*80)

df_un = pd.read_excel('All_IBP_out.xlsx', sheet_name='Не распределено')
print(f"\nВсего нераспределенных: {len(df_un)}")

# Исключаем NaN
df_un_valid = df_un[df_un['Наименование ИВП'].notna()].copy()
print(f"Из них с валидным наименованием: {len(df_un_valid)}")

print("\n" + "="*80)
print("ВСЕ НЕРАСПРЕДЕЛЕННЫЕ ЭЛЕМЕНТЫ:")
print("="*80)

for idx, row in df_un_valid.iterrows():
    name = str(row.get('Наименование ИВП', ''))[:70]
    qty = row.get('Кол-во', 0)
    source = str(row.get('source_file', ''))[:30]
    print(f"{idx+1:3}. {name:<72} | Кол-во: {qty:>6} | {source}")

# Анализ по первым словам
print("\n" + "="*80)
print("АНАЛИЗ ПО ТИПАМ (первое слово):")
print("="*80)

first_words = []
for name in df_un_valid['Наименование ИВП']:
    if pd.notna(name):
        words = str(name).split()
        if words:
            first_words.append(words[0].strip().upper())

word_counts = Counter(first_words)
for word, count in word_counts.most_common(20):
    print(f"  {word:<30}: {count} шт")

print("\n" + "="*80)
print("РЕКОМЕНДАЦИИ ПО КАТЕГОРИЗАЦИИ:")
print("="*80)
print("1. Платы инструментальные → Отладочные модули")
print("2. Коммутаторы → Другие (или создать категорию 'Сетевое оборудование')")
print("3. Вставки плавкие → Другие")
print("4. Кварц → Другие")
print("5. Сетка защитная → Другие")
print("6. Прибор, Вентиль → Полупроводники или СВЧ компоненты")
print("7. Модуль электропитания → Модули питания")
print("="*80)

