"""
Setup script для создания macOS приложения (.app bundle)
Использование: python setup_macos.py py2app
"""

from setuptools import setup
import os
import json

# Загружаем конфигурацию
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

APP = ['app.py']
DATA_FILES = [
    ('', ['config.json']),
    ('bom_categorizer', [
        'bom_categorizer/__init__.py',
        'bom_categorizer/main.py',
        'bom_categorizer/gui.py',
        'bom_categorizer/component_database.py',
        'bom_categorizer/classifiers.py',
        'bom_categorizer/parsers.py',
        'bom_categorizer/excel_writer.py',
        'bom_categorizer/txt_writer.py',
        'bom_categorizer/formatters.py',
        'bom_categorizer/utils.py',
        'bom_categorizer/podborka_extractor.py',
    ]),
]

OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': 'BOM Categorizer',
        'CFBundleDisplayName': 'BOM Categorizer',
        'CFBundleGetInfoString': config['app_info']['description_en'],
        'CFBundleIdentifier': 'com.kurein.bomcategorizer',
        'CFBundleVersion': config['app_info']['version'],
        'CFBundleShortVersionString': config['app_info']['version'],
        'NSHumanReadableCopyright': f"© 2025 {config['app_info']['developer_en']}",
        'NSHighResolutionCapable': True,
    },
    'packages': ['tkinter', 'pandas', 'openpyxl', 'docx2txt', 'chardet'],
    'includes': ['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox'],
    'excludes': ['pytest', 'setuptools'],
    'codesign_identity': '-',  # Ad-hoc подпись
}

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

