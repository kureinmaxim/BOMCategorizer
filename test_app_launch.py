# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки запуска приложения
"""
import sys
import traceback

print("=" * 60)
print("Testing BOM Categorizer Launch")
print("=" * 60)
print()

try:
    print("Step 1: Importing sys and os...")
    import os
    print("  [OK]")
    print()
    
    print("Step 2: Checking current directory...")
    print(f"  Current dir: {os.getcwd()}")
    print(f"  Script dir: {os.path.dirname(os.path.abspath(__file__))}")
    print()
    
    print("Step 3: Adding current directory to sys.path...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("  [OK]")
    print()
    
    print("Step 4: Importing bom_categorizer.gui_qt...")
    from bom_categorizer.gui_qt import main
    print("  [OK] Import successful")
    print()
    
    print("Step 5: Checking PySide6...")
    from PySide6.QtWidgets import QApplication
    print("  [OK] PySide6 available")
    print()
    
    print("Step 6: Initializing QApplication...")
    app = QApplication(sys.argv)
    print("  [OK] QApplication created")
    print()
    
    print("Step 7: Creating main window...")
    from bom_categorizer.gui_qt import BOMCategorizerMainWindow
    window = BOMCategorizerMainWindow()
    print("  [OK] Main window created")
    print()
    
    print("Step 8: Showing window...")
    window.show()
    print("  [OK] Window shown")
    print()
    
    print("=" * 60)
    print("SUCCESS! Application should be visible now.")
    print("=" * 60)
    print()
    print("Starting event loop...")
    print("(Close the window to exit)")
    print()
    
    sys.exit(app.exec())
    
except Exception as e:
    print()
    print("=" * 60)
    print("ERROR OCCURRED!")
    print("=" * 60)
    print()
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print()
    print("Full traceback:")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    print()
    input("Press Enter to exit...")
    sys.exit(1)

