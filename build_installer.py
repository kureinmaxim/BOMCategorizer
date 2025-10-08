# -*- coding: utf-8 -*-
"""
Скрипт для автоматической сборки инсталлятора BOM Categorizer

Этот скрипт:
1. Копирует все необходимые файлы в temp_installer/
2. Запускает Inno Setup Compiler для создания .exe инсталлятора
3. Очищает временные файлы после сборки

Использование:
    python build_installer.py
"""

import os
import shutil
import subprocess
import sys

# Конфигурация
TEMP_DIR = "temp_installer"
INNO_SETUP_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Файлы для копирования (в корне проекта)
FILES_TO_COPY = [
    "app.py",
    "split_bom.py",
    "config.json",
    "requirements.txt",
    "rules.json",
    "interactive_classify.py",
    "interactive_classify_improved.py",
    "preview_unclassified.py",
    "installer_clean.iss",
    "post_install.ps1",
    "run_app.bat",
    "split_bom.bat",
    "start_gui.bat",
    "README.md",
    "BUILD.md"
]

# Директории для копирования
DIRECTORIES_TO_COPY = [
    "bom_categorizer",  # Модульная структура
    "docs",             # Документация
    "offline_packages"  # Оффлайн пакеты для установки
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
    
    for directory in DIRECTORIES_TO_COPY:
        if os.path.exists(directory):
            dest = os.path.join(TEMP_DIR, directory)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(directory, dest)
            print(f"  [OK] {directory}/ (директория)")
        else:
            print(f"  [SKIP] {directory}/ (не найдена)")


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


def run_inno_setup():
    """Запускает Inno Setup Compiler"""
    if not os.path.exists(INNO_SETUP_PATH):
        print(f"\n[ERROR] Inno Setup не найден: {INNO_SETUP_PATH}")
        print("Установите Inno Setup или укажите правильный путь в переменной INNO_SETUP_PATH")
        return False
    
    print(f"\nЗапуск Inno Setup Compiler...")
    try:
        result = subprocess.run(
            [INNO_SETUP_PATH, "installer_clean.iss"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("[OK] Инсталлятор успешно собран!")
            
            # Проверяем размер файла
            if os.path.exists("BOMCategorizerSetup.exe"):
                size_mb = os.path.getsize("BOMCategorizerSetup.exe") / (1024 * 1024)
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


def main():
    """Главная функция"""
    print_step("Сборка инсталлятора BOM Categorizer")
    
    # Шаг 1: Очистка и создание temp_installer
    print_step("Шаг 1: Подготовка временной директории")
    clean_temp_dir()
    
    # Шаг 2: Копирование файлов
    print_step("Шаг 2: Копирование файлов проекта")
    copy_files()
    
    # Шаг 3: Копирование .iss в корень
    print_step("Шаг 3: Подготовка скрипта Inno Setup")
    if not copy_iss_to_root():
        print("\n[FAIL] Не удалось подготовить скрипт установки")
        return 1
    
    # Шаг 4: Запуск Inno Setup
    print_step("Шаг 4: Компиляция инсталлятора")
    if not run_inno_setup():
        print("\n[FAIL] Не удалось собрать инсталлятор")
        return 1
    
    # Успех
    print_step("УСПЕХ! Инсталлятор готов")
    print("\nФайл: BOMCategorizerSetup.exe")
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
