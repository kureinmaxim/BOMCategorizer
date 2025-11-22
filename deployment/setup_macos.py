"""
Setup script для создания macOS приложения (.app bundle)
Использование: 
  python setup_macos.py py2app                    # Standard Edition
  python setup_macos.py py2app --edition=modern   # Modern Edition
"""

from setuptools import setup
import os
import json
import sys
from pathlib import Path

# Проверка наличия иконки
if not Path('icon.icns').exists():
    print("⚠️  ВНИМАНИЕ: Файл icon.icns не найден!")
    print("   Приложение будет создано без иконки.")
    print("   Запустите: python create_icons.py для создания иконки")
    print()

# Определяем версию из аргументов командной строки
edition = 'standard'
for arg in sys.argv:
    if arg.startswith('--edition='):
        edition = arg.split('=')[1].lower()
        sys.argv.remove(arg)
        break

# Вывод информации о сборке
print("="*60)
print(f"📦 СБОРКА: {edition.upper()} EDITION")
print("="*60)

# Выбираем конфигурацию в зависимости от версии
if edition == 'modern':
    config_file = 'config_qt.json'
    app_file = 'app_qt.py'
    gui_module = 'gui_qt.py'
    dialogs_module = 'dialogs_qt.py'
    bundle_identifier = 'com.kurein.bomcategorizer.modern'
    packages = ['pandas', 'openpyxl', 'docx2txt', 'chardet', 'PySide6']
    includes = ['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'cmath', 'math', 'decimal']
    excludes_extra = ['tkinter', 'Tkinter', '_tkinter', 'bom_categorizer.gui', 'gui']
else:
    config_file = 'config.json'
    app_file = 'app.py'
    gui_module = 'gui.py'
    dialogs_module = None
    bundle_identifier = 'com.kurein.bomcategorizer'
    packages = ['tkinter', 'pandas', 'openpyxl', 'docx2txt', 'chardet']
    includes = ['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'cmath', 'math', 'decimal']
    excludes_extra = ['PySide6', 'shiboken6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'bom_categorizer.gui_qt', 'bom_categorizer.dialogs_qt', 'gui_qt', 'dialogs_qt']

# Загружаем конфигурацию
print(f"📄 Конфиг: {config_file}")
print(f"🚀 App файл: {app_file}")
print(f"🎨 GUI модуль: {gui_module}")
print(f"✅ Включаемые: {', '.join(packages[:3])}...")
print(f"❌ Исключаемые: {', '.join(excludes_extra)}")
print("="*60)
print()

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

APP = [app_file]

# Формируем список модулей bom_categorizer
bom_categorizer_modules = [
    'bom_categorizer/__init__.py',
    'bom_categorizer/main.py',
    f'bom_categorizer/{gui_module}',
    'bom_categorizer/component_database.py',
    'bom_categorizer/config_manager.py',  # Для инициализации конфигов из шаблонов
    'bom_categorizer/classifiers.py',
    'bom_categorizer/parsers.py',
    'bom_categorizer/excel_writer.py',
    'bom_categorizer/txt_writer.py',
    'bom_categorizer/formatters.py',
    'bom_categorizer/utils.py',
    'bom_categorizer/podborka_extractor.py',
]

# Добавляем дополнительные модули для Modern Edition
if dialogs_module:
    bom_categorizer_modules.extend([
        f'bom_categorizer/{dialogs_module}',
        'bom_categorizer/gui_scaling_qt.py',
        'bom_categorizer/gui_sections_qt.py',
        'bom_categorizer/gui_menu_qt.py',
        'bom_categorizer/styles.py',
        'bom_categorizer/workers_qt.py',
        'bom_categorizer/drag_drop_qt.py',
        'bom_categorizer/pdf_exporter.py',
        'bom_categorizer/pdf_search.py',
        'bom_categorizer/pdf_search_dialogs.py',
        'bom_categorizer/search_qt.py',
        'bom_categorizer/search_methods_qt.py',
        'bom_categorizer/ai_classifier_qt.py',
        'bom_categorizer/cli_interactive.py',
    ])

DATA_FILES = [
    ('', [config_file]),
    ('', ['config.json.template', 'config_qt.json.template']),  # Шаблоны для инициализации
    ('bom_categorizer', bom_categorizer_modules),
]

# Базовые опции
OPTIONS = {
    'argv_emulation': False,  # Отключено: Carbon framework больше не поддерживается в macOS
    'plist': {
        'CFBundleName': config['app_info']['description_en'].split(' - ')[0],
        'CFBundleDisplayName': config['app_info']['description_en'].split(' - ')[0],
        'CFBundleGetInfoString': config['app_info']['description_en'],
        'CFBundleIdentifier': bundle_identifier,
        'CFBundleVersion': config['app_info']['version'],
        'CFBundleShortVersionString': config['app_info']['version'],
        'NSHumanReadableCopyright': f"© 2025 {config['app_info']['developer_en']}",
        'NSHighResolutionCapable': True,
    },
    'packages': packages,
    'includes': includes,
    'excludes': ['pytest', 'setuptools'] + excludes_extra,
    'no_chdir': True,
    # Note: Автоматическое codesigning отключено через export PY2APP_CODESIGN=0 в build_macos.sh
}

# Добавляем иконку, если она существует
if Path('icon.icns').exists():
    OPTIONS['iconfile'] = 'icon.icns'

setup(
    name='BOMCategorizer',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    version=config['app_info']['version'],
    description=config['app_info']['description_en'],
    author=config['app_info']['developer_en'],
)

