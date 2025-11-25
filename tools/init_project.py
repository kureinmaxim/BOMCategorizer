#!/usr/bin/env python3
"""
Скрипт инициализации проекта BOM Categorizer после клонирования с GitHub

Этот скрипт:
1. Создает config.json из config.json.template (Standard Edition)
2. Создает config_qt.json из config_qt.json.template (Modern Edition)
3. Проверяет наличие виртуального окружения
4. Выводит инструкции по дальнейшим действиям

Использование:
    python init_project.py
"""

import os
import sys
import shutil
import json


def print_header(text):
    """Красивый заголовок"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(num, text):
    """Шаг выполнения"""
    print(f"\n[{num}] {text}")


def check_file_exists(file_path):
    """Проверяет существование файла"""
    if os.path.exists(file_path):
        print(f"  ✅ {file_path} - существует")
        return True
    else:
        print(f"  ❌ {file_path} - НЕ НАЙДЕН")
        return False


def copy_template_to_config(template_path, config_path, edition_name):
    """Копирует template в config если config не существует"""
    if os.path.exists(config_path):
        print(f"  ℹ️  {config_path} уже существует, пропускаю")
        return True
    
    if not os.path.exists(template_path):
        print(f"  ❌ Template не найден: {template_path}")
        return False
    
    try:
        shutil.copy2(template_path, config_path)
        print(f"  ✅ Создан {config_path} из {template_path}")
        
        # Показываем версию
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            version = config.get('app_info', {}).get('version', 'N/A')
            print(f"     {edition_name}: версия {version}")
        
        return True
    except Exception as e:
        print(f"  ❌ Ошибка копирования: {e}")
        return False


def check_venv():
    """Проверяет наличие виртуального окружения"""
    venv_paths = ['venv', '.venv']
    for venv in venv_paths:
        if os.path.exists(venv):
            print(f"  ✅ Виртуальное окружение найдено: {venv}/")
            return True
    
    print("  ⚠️  Виртуальное окружение не найдено")
    return False


def print_next_steps(venv_exists):
    """Выводит инструкции по дальнейшим действиям"""
    print_header("СЛЕДУЮЩИЕ ШАГИ")
    
    if not venv_exists:
        print("\n1. Создайте виртуальное окружение:")
        if sys.platform == 'win32':
            print("   python -m venv venv")
            print("   venv\\Scripts\\activate")
        else:
            print("   python3 -m venv venv")
            print("   source venv/bin/activate")
        
        print("\n2. Установите зависимости:")
        print("   pip install -r requirements.txt")
        
        print("\n3. Запустите приложение:")
        print("   Standard Edition:  python app.py")
        print("   Modern Edition:    python app_qt.py")
    else:
        print("\n1. Активируйте виртуальное окружение:")
        if sys.platform == 'win32':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        print("\n2. Установите зависимости (если ещё не установлены):")
        print("   pip install -r requirements.txt")
        
        print("\n3. Запустите приложение:")
        print("   Standard Edition:  python app.py")
        print("   Modern Edition:    python app_qt.py")
    
    print("\n" + "=" * 70)


def main():
    """Главная функция"""
    print_header("ИНИЦИАЛИЗАЦИЯ ПРОЕКТА BOM CATEGORIZER")
    
    # Переходим в директорию скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"\nТекущая директория: {os.getcwd()}")
    
    # Шаг 1: Проверка template файлов
    print_step(1, "Проверка наличия template файлов")
    
    templates_exist = True
    templates_exist &= check_file_exists("config.json.template")
    templates_exist &= check_file_exists("config_qt.json.template")
    
    if not templates_exist:
        print("\n❌ ОШИБКА: Не найдены template файлы!")
        print("   Убедитесь что вы находитесь в корне проекта BOMCategorizer")
        return 1
    
    # Шаг 2: Создание config файлов
    print_step(2, "Создание config файлов из templates")
    
    success = True
    success &= copy_template_to_config(
        "config.json.template",
        "config.json",
        "Standard Edition"
    )
    success &= copy_template_to_config(
        "config_qt.json.template",
        "config_qt.json",
        "Modern Edition"
    )
    
    if not success:
        print("\n⚠️  Некоторые config файлы не были созданы")
        print("   Приложение будет использовать fallback настройки")
    
    # Шаг 3: Проверка виртуального окружения
    print_step(3, "Проверка виртуального окружения")
    venv_exists = check_venv()
    
    # Инструкции по дальнейшим действиям
    print_next_steps(venv_exists)
    
    print("\n✅ Инициализация завершена!")
    print("   Проект готов к запуску\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

