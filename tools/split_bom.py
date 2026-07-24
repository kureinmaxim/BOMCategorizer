# -*- coding: utf-8 -*-
"""
BOM Categorizer — точка входа терминального CLI.

Использование:
    python tools/split_bom.py --inputs file1.xlsx file2.docx --xlsx output.xlsx --txt-dir output_txt --combine
    python tools/split_bom.py --help

Windows без активации venv:
    .\\.venv\\Scripts\\python.exe tools\\split_bom.py --inputs "bom.xlsx" --xlsx "out.xlsx" --combine
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bom_categorizer.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
