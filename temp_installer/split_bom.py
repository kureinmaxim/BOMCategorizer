# -*- coding: utf-8 -*-
"""
BOM Categorizer - Entry Point

Этот файл является точкой входа для CLI приложения.
Вся логика вынесена в модуль bom_categorizer.

Использование:
    python split_bom.py --inputs file1.xlsx file2.docx --xlsx output.xlsx --txt-dir output_txt --combine

Для получения помощи:
    python split_bom.py --help
"""

import sys

# Импортируем главную функцию из модульной структуры
from bom_categorizer.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
