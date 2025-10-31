# -*- coding: utf-8 -*-
"""Быстрая проверка ТУ конденсаторов"""

import pandas as pd
from bom_categorizer.parsers import parse_docx

df = parse_docx('example/plata_MKVH.docx')

# Конденсаторы
df_caps = df[df['reference'].str.match('^C', case=False, na=False)]

print("\n=== Конденсаторы ===\n")
for idx, row in df_caps.head(8).iterrows():
    print(f"{row['reference']:10} | {row['description'][:40]:40} | ТУ: {row.get('note', '')[:30]}")

