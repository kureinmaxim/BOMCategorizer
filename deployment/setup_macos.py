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
    config_file = 'config/config_qt.json.template'
    app_file = 'app_qt.py'
    bundle_identifier = 'com.kurein.bomcategorizer.modern'
    packages = ['pandas', 'openpyxl', 'docx2txt', 'chardet', 'PySide6']
    includes = ['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'cmath', 'math', 'decimal']
    excludes_extra = ['tkinter', 'Tkinter', '_tkinter', 'bom_categorizer.gui_legacy', 'gui_legacy']
else:
    config_file = 'config/config.json.template'
    app_file = 'app.py'
    bundle_identifier = 'com.kurein.bomcategorizer'
    packages = ['tkinter', 'pandas', 'openpyxl', 'docx2txt', 'chardet']
    includes = ['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'cmath', 'math', 'decimal']
    excludes_extra = ['PySide6', 'shiboken6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets']

# Загружаем конфигурацию
print(f"📄 Конфиг: {config_file}")
print(f"🚀 App файл: {app_file}")
print(f"✅ Включаемые: {', '.join(packages[:3])}...")
print(f"❌ Исключаемые: {', '.join(excludes_extra[:3])}...")
print("="*60)
print()

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

APP = [app_file]

# Формируем список модулей bom_categorizer
bom_categorizer_modules = [
    'bom_categorizer/__init__.py',
    'bom_categorizer/main.py',
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

# Добавляем GUI модули для Modern Edition
if edition == 'modern':
    bom_categorizer_modules.extend([
        'bom_categorizer/gui/__init__.py',
        'bom_categorizer/gui/main_window.py',
        'bom_categorizer/gui/dialogs.py',
        'bom_categorizer/gui/sections.py',
        'bom_categorizer/gui/menu.py',
        'bom_categorizer/gui/scaling.py',
        'bom_categorizer/gui/search.py',
        'bom_categorizer/gui/search_methods.py',
        'bom_categorizer/gui/workers.py',
        'bom_categorizer/gui/drag_drop.py',
        'bom_categorizer/gui/ai_classifier.py',
        'bom_categorizer/gui/pdf_search.py',
        'bom_categorizer/gui/pdf_search_dialogs.py',
        'bom_categorizer/pdf_exporter.py',
        'bom_categorizer/styles.py',
        'bom_categorizer/cli_interactive.py',
    ])
else:
    bom_categorizer_modules.extend([
        'bom_categorizer/gui.py',
    ])

DATA_FILES = [
    ('', [config_file]),
    ('', ['config/config.json.template', 'config/config_qt.json.template']),  # Шаблоны
    ('', ['config/rules.json']),  # Правила
    ('', ['data/component_database_template.json']),  # Шаблон БД
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
# Проверяем в нескольких местах (скрипт может запускаться из корня или deployment/)
icon_paths = [
    Path('icon.icns'),  # Если запущено из корня
    Path(__file__).parent.parent / 'icon.icns',  # Если запущено из deployment/
]
icon_file = None
for icon_path in icon_paths:
    if icon_path.exists():
        icon_file = str(icon_path)
        print(f"✅ Иконка найдена: {icon_file}")
        break

if icon_file:
    OPTIONS['iconfile'] = icon_file
else:
    print("⚠️  Иконка не найдена, приложение будет без кастомной иконки")

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

