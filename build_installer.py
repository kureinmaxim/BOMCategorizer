# -*- coding: utf-8 -*-
"""
Скрипт для автоматической сборки инсталлятора BOM Categorizer

Этот скрипт:
1. Спрашивает какую версию собирать (Standard или Modern Edition)
2. Копирует все необходимые файлы в temp_installer/
3. Запускает Inno Setup Compiler для создания .exe инсталлятора
4. Очищает временные файлы после сборки

Использование:
    python build_installer.py
"""

import os
import shutil
import subprocess
import sys
import json
import re

# Конфигурация
TEMP_DIR = "temp_installer"
INNO_SETUP_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"


def read_version_from_config(config_file):
    """Читает версию из config файла"""
    try:
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("app_info", {}).get("version", "Unknown")
        return "Unknown"
    except Exception as e:
        print(f"⚠️  Ошибка чтения версии из {config_file}: {e}")
        return "Unknown"


# Версии приложения (версии читаются автоматически из config файлов)
EDITIONS = {
    "1": {
        "name": "Standard",
        "version": read_version_from_config("config.json"),
        "app_file": "app.py",
        "config": "config.json",
        "iss_file": "installer_clean.iss",
        "output": "BOMCategorizerSetup.exe",
        "description": "Tkinter GUI (стабильная версия)"
    },
    "2": {
        "name": "Modern Edition",
        "version": read_version_from_config("config_qt.json"),
        "app_file": "app_qt.py",
        "config": "config_qt.json",
        "iss_file": "installer_qt.iss",
        "output": "BOMCategorizerModernSetup.exe",
        "description": "PySide6 GUI (современный дизайн + экспериментальные функции)"
    }
}

# Файлы для копирования (в корне проекта)
FILES_TO_COPY = [
    "app.py",
    "app_qt.py",  # Modern Edition entry point
    "split_bom.py",
    "config.json",
    "config_qt.json",  # Modern Edition config
    "component_database_template.json",  # Шаблон БД (пустая база для новых установок)
    "merge_component_database.py",  # Скрипт слияния баз данных при обновлении
    "requirements_install.txt",  # Используем облегченную версию без тестовых зависимостей
    "rules.json",
    "interactive_classify.py",
    "interactive_classify_improved.py",
    "preview_unclassified.py",
    "installer_clean.iss",
    "installer_qt.iss",  # Modern Edition installer script
    "post_install.ps1",
    "repair_install.ps1",
    "repair_install.bat",
    "run_app.bat",
    "run_app_debug.bat",  # Debug version with console output
    "run_app_simple.bat",  # Simple version with console output (for troubleshooting)
    "split_bom.bat",
    "start_gui.bat",
    "README.md",
    "BUILD.md"
]

# Директории для копирования
DIRECTORIES_TO_COPY = [
    "bom_categorizer",  # Модульная структура
    "docs",             # Документация
    "offline_packages", # Оффлайн пакеты для установки
    "fonts"             # Шрифты для PDF экспорта (кириллица)
]


def print_step(message):
    """Вывод шага выполнения"""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}")


def clean_temp_dir():
    """Удаляет временную директорию если она существует"""
    if os.path.exists(TEMP_DIR):
        print(f"Удаляю старую директорию {TEMP_DIR}...")
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    print(f"Создана директория {TEMP_DIR}")


def copytree_exclude(src, dst, exclude_dirs=None, exclude_files=None):
    """
    Копирует директорию с исключением указанных директорий и файлов.
    
    Args:
        src: исходная директория
        dst: целевая директория
        exclude_dirs: список имен директорий для исключения (по умолчанию: __pycache__, .git, .pytest_cache)
        exclude_files: список паттернов файлов для исключения (по умолчанию: *.pyc, *.pyo, *.pyd)
    """
    if exclude_dirs is None:
        exclude_dirs = ['__pycache__', '.git', '.pytest_cache', '.mypy_cache', '.ruff_cache']
    if exclude_files is None:
        exclude_files = ['*.pyc', '*.pyo', '*.pyd']
    
    os.makedirs(dst, exist_ok=True)
    
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        
        # Пропускаем исключенные директории
        if os.path.isdir(src_path) and item in exclude_dirs:
            continue
        
        # Пропускаем исключенные файлы
        if os.path.isfile(src_path):
            skip = False
            for pattern in exclude_files:
                if item.endswith(pattern.replace('*', '')):
                    skip = True
                    break
            if skip:
                continue
            shutil.copy2(src_path, dst_path)
        else:
            # Рекурсивно копируем поддиректории
            copytree_exclude(src_path, dst_path, exclude_dirs, exclude_files)


def copy_files():
    """Копирует необходимые файлы в temp_installer"""
    print("\nКопирую файлы...")
    
    for file in FILES_TO_COPY:
        if os.path.exists(file):
            dest = os.path.join(TEMP_DIR, file)
            shutil.copy2(file, dest)
            print(f"  [OK] {file}")
        else:
            print(f"  [SKIP] {file} (не найден)")
    
    # Переименовываем requirements_install.txt в requirements.txt для инсталлятора
    req_install = os.path.join(TEMP_DIR, "requirements_install.txt")
    req_final = os.path.join(TEMP_DIR, "requirements.txt")
    if os.path.exists(req_install):
        shutil.move(req_install, req_final)
        print(f"  [OK] requirements_install.txt -> requirements.txt")
    
    # Переименовываем шаблон БД в component_database.json для инсталлятора
    db_template = os.path.join(TEMP_DIR, "component_database_template.json")
    db_final = os.path.join(TEMP_DIR, "component_database.json")
    if os.path.exists(db_template):
        shutil.copy2(db_template, db_final)
        print(f"  [OK] component_database_template.json -> component_database.json (пустая БД)")
    
    # Копируем директории с исключением ненужных файлов
    for directory in DIRECTORIES_TO_COPY:
        if os.path.exists(directory):
            dest = os.path.join(TEMP_DIR, directory)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            copytree_exclude(directory, dest)
            print(f"  [OK] {directory}/ (директория, исключены __pycache__ и *.pyc)")
        else:
            print(f"  [SKIP] {directory}/ (не найдена)")
    
    # Дополнительная очистка: удаляем __pycache__ если они все-таки попали
    print("\nОчистка временных файлов...")
    for root, dirs, files in os.walk(TEMP_DIR):
        # Удаляем директории __pycache__
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache_path)
            print(f"  [CLEAN] Удален {pycache_path}")
            dirs.remove('__pycache__')  # Убираем из списка для обхода
        
        # Удаляем .pyc файлы
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                pyc_path = os.path.join(root, file)
                os.remove(pyc_path)
                print(f"  [CLEAN] Удален {pyc_path}")


def copy_iss_to_root():
    """Копирует installer_clean.iss в корень проекта для Inno Setup"""
    source = os.path.join(TEMP_DIR, "installer_clean.iss")
    dest = "installer_clean.iss"
    
    if os.path.exists(source):
        shutil.copy2(source, dest)
        print(f"\n[OK] Скопирован installer_clean.iss в корень")
        return True
    else:
        print(f"\n[ERROR] Не найден {source}")
        return False


def update_iss_version(iss_file, version):
    """Обновляет версию в .iss файле"""
    try:
        with open(iss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем строку с версией и заменяем её
        content = re.sub(
            r'#define MyAppVersion ".*?"',
            f'#define MyAppVersion "{version}"',
            content
        )
        
        with open(iss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] Версия в {iss_file} обновлена на {version}")
        return True
    except Exception as e:
        print(f"⚠️  Ошибка обновления версии в {iss_file}: {e}")
        return False


def run_inno_setup_edition(iss_file, output_file):
    """Запускает Inno Setup Compiler"""
    if not os.path.exists(INNO_SETUP_PATH):
        print(f"\n[ERROR] Inno Setup не найден: {INNO_SETUP_PATH}")
        print("Установите Inno Setup или укажите правильный путь в переменной INNO_SETUP_PATH")
        return False
    
    print(f"\nЗапуск Inno Setup Compiler...")
    try:
        result = subprocess.run(
            [INNO_SETUP_PATH, iss_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("[OK] Инсталлятор успешно собран!")
            
            # Проверяем размер файла
            if os.path.exists(output_file):
                size_mb = os.path.getsize(output_file) / (1024 * 1024)
                print(f"\nРазмер инсталлятора: {size_mb:.2f} MB")
            
            return True
        else:
            print(f"[ERROR] Ошибка при сборке инсталлятора")
            print(f"Код возврата: {result.returncode}")
            if result.stdout:
                print(f"Вывод:\n{result.stdout}")
            if result.stderr:
                print(f"Ошибки:\n{result.stderr}")
            return False
    
    except Exception as e:
        print(f"[ERROR] Исключение при запуске Inno Setup: {e}")
        return False


def select_edition():
    """Диалог выбора версии для сборки"""
    print("\n" + "="*60)
    print("  ВЫБЕРИТЕ ВЕРСИЮ ДЛЯ СБОРКИ:")
    print("="*60)
    
    for key, edition in EDITIONS.items():
        print(f"\n  [{key}] {edition['name']} v{edition['version']}")
        print(f"      {edition['description']}")
        print(f"      Файл: {edition['output']}")
    
    print("\n" + "="*60)
    
    while True:
        choice = input("\nВведите номер версии (1 или 2): ").strip()
        if choice in EDITIONS:
            return EDITIONS[choice]
        print("[ERROR] Неверный выбор. Введите 1 или 2.")


def main():
    """Главная функция"""
    print_step("Сборка инсталлятора BOM Categorizer")
    
    # Выбор версии
    edition = select_edition()
    
    print_step(f"Выбрана версия: {edition['name']} v{edition['version']}")
    
    # Шаг 1: Очистка и создание temp_installer
    print_step("Шаг 1: Подготовка временной директории")
    clean_temp_dir()
    
    # Шаг 2: Копирование файлов
    print_step("Шаг 2: Копирование файлов проекта")
    copy_files()
    
    # Копируем правильный конфигурационный файл
    print(f"\nКопирую {edition['config']} -> config.json...")
    if not os.path.exists(edition['config']):
        print(f"[ERROR] Файл {edition['config']} не найден!")
        print(f"       Убедитесь, что файл существует в корне проекта.")
        return 1
    shutil.copy2(edition['config'], os.path.join(TEMP_DIR, 'config.json'))
    print(f"[OK] {edition['config']} -> config.json")
    
    # Копируем правильный файл запуска
    print(f"Копирую {edition['app_file']} -> app.py...")
    if not os.path.exists(edition['app_file']):
        print(f"[ERROR] Файл {edition['app_file']} не найден!")
        print(f"       Убедитесь, что файл существует в корне проекта.")
        return 1
    shutil.copy2(edition['app_file'], os.path.join(TEMP_DIR, 'app.py'))
    print(f"[OK] {edition['app_file']} -> app.py")
    
    # Шаг 3: Копирование .iss в корень
    print_step("Шаг 3: Подготовка скрипта Inno Setup")
    
    # Копируем правильный .iss файл
    iss_source = edition['iss_file']
    if os.path.exists(iss_source):
        shutil.copy2(iss_source, os.path.join(TEMP_DIR, 'installer.iss'))
        shutil.copy2(iss_source, 'installer_active.iss')
        print(f"[OK] Скопирован {iss_source}")
        
        # Обновляем версию в .iss файле
        print(f"\nОбновление версии в .iss файле...")
        update_iss_version('installer_active.iss', edition['version'])
    else:
        print(f"[ERROR] Не найден {iss_source}")
        return 1
    
    # Шаг 4: Запуск Inno Setup
    print_step("Шаг 4: Компиляция инсталлятора")
    if not run_inno_setup_edition('installer_active.iss', edition['output']):
        print("\n[FAIL] Не удалось собрать инсталлятор")
        return 1
    
    # Успех
    print_step(f"УСПЕХ! Инсталлятор готов")
    print(f"\nВерсия: {edition['name']} v{edition['version']}")
    print(f"Файл: {edition['output']}")
    print("\nВы можете распространять этот файл для установки на других компьютерах.")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[ОТМЕНЕНО] Сборка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
