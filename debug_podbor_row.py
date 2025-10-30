#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bom_categorizer.parsers import parse_docx
import pandas as pd

df = parse_docx('example/Plata_preobrz.docx')

# Находим R48*
r48_row = df[df['reference'].astype(str).str.contains('R48', na=False)]

if len(r48_row) > 0:
    print("Структура row для R48*:")
    print("=" * 80)
    row = r48_row.iloc[0]
    for col in row.index:
        val = row[col]
        print(f"{col:20s}: {val}")

