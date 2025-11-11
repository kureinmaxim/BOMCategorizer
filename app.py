"""
BOM Categorizer - Tkinter GUI Entry Point (Standard Edition)

Этот файл является точкой входа для Tkinter GUI приложения.
Вся логика вынесена в модуль bom_categorizer.gui.

Использование:
    python app.py
"""

import sys

# Исправление кодировки для корректного вывода русских символов
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Импортируем Tkinter GUI из модульной структуры
from bom_categorizer.gui import launch_gui


if __name__ == "__main__":
    launch_gui()
