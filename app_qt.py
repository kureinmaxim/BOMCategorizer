# -*- coding: utf-8 -*-
"""
Точка входа для PySide6 версии BOM Categorizer (Modern Edition)
"""

if __name__ == "__main__":
    # Настройка кодировки консоли для Windows (для корректного отображения сообщений Qt)
    import sys
    import io
    if sys.platform == 'win32':
        try:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass
    
    from bom_categorizer.gui_qt import main
    main()

