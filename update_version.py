#!/usr/bin/env python3
"""
Центральная утилита для управления версиями BOM Categorizer

Единственный источник правды - шаблоны config:
- config.json.template (Standard Edition)
- config_qt.json.template (Modern Edition)

Использование:
    # Показать текущие версии
    python update_version.py status
    
    # Обновить версию Standard Edition
    python update_version.py set standard 3.4.0
    
    # Обновить версию Modern Edition
    python update_version.py set modern 4.3.0
    
    # Обновить обе версии
    python update_version.py set both 5.0.0
    
    # Синхронизировать все файлы сборки с шаблонами
    python update_version.py sync
"""

import json
import os
import sys
import subprocess
from datetime import datetime


class Colors:
    """ANSI цвета для вывода"""
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def read_config_template(template_path):
    """Читает config шаблон"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка чтения {template_path}: {e}{Colors.NC}")
        return None


def write_config_template(template_path, config):
    """Записывает config шаблон"""
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write('\n')
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка записи {template_path}: {e}{Colors.NC}")
        return False


def show_status():
    """Показывает текущие версии во всех файлах"""
    print(f"\n{Colors.BOLD}📊 ТЕКУЩИЕ ВЕРСИИ{Colors.NC}\n")
    print("=" * 70)
    
    # Standard Edition
    print(f"\n{Colors.BLUE}📦 Standard Edition (Tkinter){Colors.NC}")
    config = read_config_template('config.json.template')
    if config:
        version = config['app_info']['version']
        date = config['app_info'].get('release_date', 'N/A')
        print(f"  Версия:      {Colors.GREEN}{version}{Colors.NC}")
        print(f"  Дата релиза: {date}")
        print(f"  Файл:        config.json.template")
    
    # Modern Edition
    print(f"\n{Colors.BLUE}📦 Modern Edition (PySide6){Colors.NC}")
    config = read_config_template('config_qt.json.template')
    if config:
        version = config['app_info']['version']
        date = config['app_info'].get('release_date', 'N/A')
        print(f"  Версия:      {Colors.GREEN}{version}{Colors.NC}")
        print(f"  Дата релиза: {date}")
        print(f"  Файл:        config_qt.json.template")
    
    # Скрипты сборки
    print(f"\n{Colors.BLUE}🔧 Файлы сборки (читают из шаблонов){Colors.NC}")
    print(f"  ✅ build_macos.sh")
    print(f"  ✅ installer_clean.iss (через sync_installer_versions.py)")
    print(f"  ✅ installer_qt.iss (через sync_installer_versions.py)")
    
    print("\n" + "=" * 70)
    print(f"\n{Colors.YELLOW}💡 Совет:{Colors.NC} Используйте 'update_version.py sync' для синхронизации\n")


def update_version(edition, new_version, update_date=True):
    """
    Обновляет версию в шаблоне config
    
    Args:
        edition: 'standard' или 'modern'
        new_version: новая версия (например, '3.4.0')
        update_date: обновить ли дату релиза
    """
    if edition == 'standard':
        template_path = 'config.json.template'
        edition_name = "Standard Edition"
    elif edition == 'modern':
        template_path = 'config_qt.json.template'
        edition_name = "Modern Edition"
    else:
        print(f"{Colors.RED}❌ Неизвестная edition: {edition}{Colors.NC}")
        return False
    
    # Читаем config
    config = read_config_template(template_path)
    if not config:
        return False
    
    # Получаем старую версию
    old_version = config['app_info']['version']
    
    # Обновляем версию
    config['app_info']['version'] = new_version
    
    # Обновляем даты
    if update_date:
        today = datetime.now().strftime("%d.%m.%Y")
        config['app_info']['release_date'] = today
        config['app_info']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    
    # Сохраняем
    if write_config_template(template_path, config):
        print(f"{Colors.GREEN}✅ {edition_name}: {old_version} → {new_version}{Colors.NC}")
        if update_date:
            print(f"   Дата обновлена: {config['app_info']['release_date']}")
        return True
    
    return False


def sync_all():
    """Синхронизирует все файлы сборки с шаблонами"""
    print(f"\n{Colors.BOLD}🔄 СИНХРОНИЗАЦИЯ ФАЙЛОВ СБОРКИ{Colors.NC}\n")
    print("=" * 70)
    
    # Запускаем sync_installer_versions.py
    try:
        result = subprocess.run(
            [sys.executable, 'sync_installer_versions.py'],
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            print(f"{Colors.YELLOW}⚠️  Предупреждение: sync_installer_versions.py завершился с кодом {result.returncode}{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка выполнения sync_installer_versions.py: {e}{Colors.NC}")
        print(f"{Colors.YELLOW}💡 Убедитесь, что файл существует и имеет права на выполнение{Colors.NC}")
    
    print("=" * 70)
    print(f"\n{Colors.GREEN}✅ Синхронизация завершена!{Colors.NC}")
    print(f"{Colors.YELLOW}💡 build_macos.sh автоматически читает версии из шаблонов{Colors.NC}\n")


def print_usage():
    """Выводит справку по использованию"""
    print(f"""
{Colors.BOLD}📚 УПРАВЛЕНИЕ ВЕРСИЯМИ BOM CATEGORIZER{Colors.NC}

{Colors.BLUE}Использование:{Colors.NC}
  python update_version.py <команда> [аргументы]

{Colors.BLUE}Команды:{Colors.NC}
  {Colors.GREEN}status{Colors.NC}
      Показать текущие версии во всех файлах
      
  {Colors.GREEN}set standard <версия>{Colors.NC}
      Обновить версию Standard Edition
      Пример: python update_version.py set standard 3.4.0
      
  {Colors.GREEN}set modern <версия>{Colors.NC}
      Обновить версию Modern Edition
      Пример: python update_version.py set modern 4.3.0
      
  {Colors.GREEN}set both <версия>{Colors.NC}
      Обновить обе версии одновременно
      Пример: python update_version.py set both 5.0.0
      
  {Colors.GREEN}sync{Colors.NC}
      Синхронизировать файлы сборки (.iss) с шаблонами
      Выполняется автоматически после 'set'

{Colors.BLUE}Рабочий процесс:{Colors.NC}
  1. Обновите версию:    python update_version.py set modern 4.3.0
  2. Синхронизируйте:    python update_version.py sync
  3. Соберите проект:    ./build_macos.sh (macOS) или build_installer.py (Windows)

{Colors.YELLOW}💡 Источник правды:{Colors.NC}
  Все версии хранятся ТОЛЬКО в шаблонах:
  - config.json.template (Standard Edition)
  - config_qt.json.template (Modern Edition)
  
  Все скрипты сборки читают версии из этих шаблонов!
""")


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    command = sys.argv[1].lower()
    
    # Переходим в директорию скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if command == 'status':
        show_status()
        
    elif command == 'set':
        if len(sys.argv) < 4:
            print(f"{Colors.RED}❌ Недостаточно аргументов{Colors.NC}")
            print(f"Использование: python update_version.py set <standard|modern|both> <версия>")
            return 1
        
        edition = sys.argv[2].lower()
        new_version = sys.argv[3]
        
        success = True
        if edition == 'both':
            success = update_version('standard', new_version) and update_version('modern', new_version)
        elif edition in ['standard', 'modern']:
            success = update_version(edition, new_version)
        else:
            print(f"{Colors.RED}❌ Неизвестная edition: {edition}{Colors.NC}")
            print(f"Используйте: standard, modern или both")
            return 1
        
        if success:
            print(f"\n{Colors.GREEN}✅ Версия обновлена в шаблонах{Colors.NC}")
            print(f"{Colors.YELLOW}🔄 Синхронизирую файлы сборки...{Colors.NC}")
            sync_all()
        else:
            return 1
        
    elif command == 'sync':
        sync_all()
        
    elif command in ['help', '--help', '-h']:
        print_usage()
        
    else:
        print(f"{Colors.RED}❌ Неизвестная команда: {command}{Colors.NC}")
        print_usage()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

