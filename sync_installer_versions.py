#!/usr/bin/env python3
"""
Скрипт для синхронизации версий в installer файлах (.iss)
Читает версии из шаблонов config и обновляет .iss файлы

Использование:
    python sync_installer_versions.py
"""

import json
import os
import sys
import re


def read_version_from_template(template_path):
    """
    Читает версию и edition из шаблона config
    
    Args:
        template_path: путь к файлу шаблона
        
    Returns:
        tuple: (version, edition)
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            version = config['app_info']['version']
            edition = config['app_info']['edition']
            return version, edition
    except Exception as e:
        print(f"❌ Ошибка чтения {template_path}: {e}")
        return None, None


def update_iss_file(iss_path, version, edition):
    """
    Обновляет версию и edition в .iss файле
    
    Args:
        iss_path: путь к .iss файлу
        version: новая версия
        edition: название edition
        
    Returns:
        bool: True если файл был обновлен
    """
    if not os.path.exists(iss_path):
        print(f"⚠️  Файл не найден: {iss_path}")
        return False
    
    try:
        with open(iss_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Обновляем версию
        content = re.sub(
            r'#define MyAppVersion ".*?"',
            f'#define MyAppVersion "{version}"',
            content
        )
        
        # Обновляем edition
        content = re.sub(
            r'#define MyAppEdition ".*?"',
            f'#define MyAppEdition "{edition}"',
            content
        )
        
        with open(iss_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Обновлен: {iss_path} → v{version} ({edition})")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления {iss_path}: {e}")
        return False


def main():
    """Главная функция - синхронизация версий"""
    print("🔄 Синхронизация версий installer файлов...\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Standard Edition
    print("📦 Standard Edition:")
    standard_version, standard_edition = read_version_from_template('config.json.template')
    if standard_version:
        update_iss_file('installer_clean.iss', standard_version, standard_edition)
    
    print()
    
    # Modern Edition
    print("📦 Modern Edition:")
    modern_version, modern_edition = read_version_from_template('config_qt.json.template')
    if modern_version:
        update_iss_file('installer_qt.iss', modern_version, modern_edition)
    
    print("\n✅ Синхронизация завершена!")
    print("\n💡 Теперь версии в .iss файлах соответствуют шаблонам config")


if __name__ == "__main__":
    main()

