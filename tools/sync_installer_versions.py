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

# Настройка UTF-8 для Windows консоли
def setup_console_encoding():
    """Настраивает UTF-8 кодировку для корректного вывода эмодзи в Windows"""
    if sys.platform == 'win32':
        try:
            # Попытка установить UTF-8 для stdout и stderr
            import io
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass  # Если не получилось, продолжаем без UTF-8

setup_console_encoding()


class Emoji:
    """Эмодзи для вывода"""
    CHECK = '✅'
    INFO = 'ℹ️'
    WARN = '💡'
    ERROR = '❌'


def safe_print(text):
    """
    Безопасный вывод текста с поддержкой эмодзи.
    Если эмодзи не поддерживаются, заменяет их на текстовые альтернативы.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: заменяем эмодзи на текст
        fallback_text = text.replace(Emoji.CHECK, '[OK]')
        fallback_text = fallback_text.replace(Emoji.INFO, '[INFO]')
        fallback_text = fallback_text.replace(Emoji.WARN, '[WARN]')
        fallback_text = fallback_text.replace(Emoji.ERROR, '[ERROR]')
        print(fallback_text)


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
        safe_print(f"{Emoji.ERROR} Ошибка чтения {template_path}: {e}")
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
        safe_print(f"{Emoji.WARN} Файл не найден: {iss_path}")
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
        
        safe_print(f"{Emoji.CHECK} Обновлен: {iss_path} -> v{version} ({edition})")
        return True
        
    except Exception as e:
        safe_print(f"{Emoji.ERROR} Ошибка обновления {iss_path}: {e}")
        return False


def main():
    """Главная функция - синхронизация версий"""
    safe_print("== Синхронизация версий installer файлов ==\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Standard Edition
    safe_print(f"{Emoji.INFO} Standard Edition:")
    standard_version, standard_edition = read_version_from_template('../config/config.json.template')
    if standard_version:
        update_iss_file('../deployment/installer_clean.iss', standard_version, standard_edition)
    
    safe_print("")  # пустая строка
    
    # Modern Edition
    safe_print(f"{Emoji.INFO} Modern Edition:")
    modern_version, modern_edition = read_version_from_template('../config/config_qt.json.template')
    if modern_version:
        update_iss_file('../deployment/installer_qt.iss', modern_version, modern_edition)
    
    safe_print(f"\n{Emoji.CHECK} Синхронизация завершена.")
    safe_print(f"\n{Emoji.INFO} Версии в .iss файлах соответствуют шаблонам config.")


if __name__ == "__main__":
    main()

