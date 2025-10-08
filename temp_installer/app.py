"""
BOM Categorizer - GUI Entry Point

Этот файл является точкой входа для GUI приложения.
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

# Импортируем GUI из модульной структуры
from bom_categorizer.gui import BOMCategorizerApp


if __name__ == "__main__":
    app = BOMCategorizerApp()
    app.mainloop()