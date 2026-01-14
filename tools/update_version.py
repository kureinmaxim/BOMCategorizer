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
import re
from datetime import datetime

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

# ВАЖНО: скрипт использует относительные пути вида "../config/...".
# Чтобы его можно было запускать из ЛЮБОЙ папки (например, из корня репозитория),
# фиксируем рабочую директорию на папку tools/.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(SCRIPT_DIR)
except Exception:
    pass


class Colors:
    """ANSI цвета для вывода"""
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class Emoji:
    """Эмодзи для вывода"""
    CHECK = '✅'
    INFO = 'ℹ️'
    WARN = '💡'
    ERROR = '❌'
    SYNC = '🔄'
    ARROW = '→'


def safe_print(text, use_emoji=True):
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
        fallback_text = fallback_text.replace(Emoji.WARN, '[TIP]')
        fallback_text = fallback_text.replace(Emoji.ERROR, '[ERROR]')
        fallback_text = fallback_text.replace(Emoji.SYNC, '[SYNC]')
        fallback_text = fallback_text.replace(Emoji.ARROW, '->')
        print(fallback_text)


def read_config_template(template_path):
    """Читает config шаблон"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Ошибка чтения {template_path}: {e}{Colors.NC}")
        return None


def write_config_template(template_path, config):
    """Записывает config шаблон"""
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write('\n')
        return True
    except Exception as e:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Ошибка записи {template_path}: {e}{Colors.NC}")
        return False


def update_local_config(config_path, version, edition, release_date=None, last_updated=None):
    """
    Обновляет секцию app_info в локальном config, не затрагивая остальные настройки.
    
    Args:
        config_path: путь к локальному config (config.json или config_qt.json)
        version: новая версия
        edition: название edition
        release_date: дата релиза (строка) или None, если не нужно обновлять
        last_updated: дата обновления (строка) или None, если не нужно обновлять
    """
    if not os.path.exists(config_path):
        safe_print(f"{Colors.YELLOW}{Emoji.WARN} Локальный файл не найден: {config_path}. Пропускаю обновление.{Colors.NC}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Ошибка чтения {config_path}: {e}{Colors.NC}")
        return False
    
    app_info = config.get('app_info', {})
    app_info['version'] = version
    if edition:
        app_info['edition'] = edition
    if release_date is not None:
        app_info['release_date'] = release_date
    if last_updated is not None:
        app_info['last_updated'] = last_updated
    
    config['app_info'] = app_info
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write('\n')
        safe_print(f"{Colors.GREEN}   {Emoji.ARROW} Обновлен локальный файл: {config_path}{Colors.NC}")
        return True
    except Exception as e:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Ошибка записи {config_path}: {e}{Colors.NC}")
        return False


def read_config_file(config_path):
    """Читает config файл (локальный или шаблон)"""
    try:
        if not os.path.exists(config_path):
            return None
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _git_run(args, repo_root):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            return None
        return (result.stdout or "").strip()
    except Exception:
        return None


def _get_repo_root():
    # tools/ -> repo root is one level up
    return os.path.abspath(os.path.join(SCRIPT_DIR, ".."))


def write_build_meta():
    """
    Генерирует build метаданные (время, git commit/tag/branch, версии из шаблонов)
    в файл ../bom_categorizer/_build_meta.json.

    Файл предназначен для отображения в UI (About/tooltip) и включается в сборки.
    """
    try:
        repo_root = _get_repo_root()

        standard = read_config_template("../config/config.json.template") or {}
        modern = read_config_template("../config/config_qt.json.template") or {}

        # Git info (best-effort)
        commit = _git_run(["rev-parse", "--short", "HEAD"], repo_root)
        branch = _git_run(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
        describe = _git_run(["describe", "--tags", "--always", "--dirty"], repo_root)
        dirty_flag = _git_run(["status", "--porcelain"], repo_root)
        dirty = bool(dirty_flag) if dirty_flag is not None else None

        meta = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "repo": {
                "commit": commit,
                "branch": branch,
                "describe": describe,
                "dirty": dirty,
            },
            "editions": {
                "standard": {
                    "version": ((standard.get("app_info") or {}).get("version")),
                    "release_date": ((standard.get("app_info") or {}).get("release_date")),
                    "last_updated": ((standard.get("app_info") or {}).get("last_updated")),
                },
                "modern": {
                    "version": ((modern.get("app_info") or {}).get("version")),
                    "release_date": ((modern.get("app_info") or {}).get("release_date")),
                    "last_updated": ((modern.get("app_info") or {}).get("last_updated")),
                },
            },
        }

        out_path = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "bom_categorizer", "_build_meta.json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            f.write("\n")
        safe_print(f"{Colors.GREEN}   {Emoji.ARROW} Build meta: обновлен bom_categorizer/_build_meta.json{Colors.NC}")
        return True
    except Exception as e:
        safe_print(f"{Colors.YELLOW}{Emoji.WARN} Не удалось сгенерировать build meta: {e}{Colors.NC}")
        return False


def show_status():
    """Показывает текущие версии во всех файлах (шаблоны и локальные)"""
    safe_print(f"\n{Colors.BOLD}[STATUS] ТЕКУЩИЕ ВЕРСИИ{Colors.NC}\n")
    safe_print("=" * 70)
    
    versions_differ = False
    
    # Standard Edition
    safe_print(f"\n{Colors.BLUE}{Emoji.INFO} Standard Edition (Tkinter){Colors.NC}")
    
    # Шаблон
    template_config = read_config_template('../config/config.json.template')
    if template_config:
        template_version = template_config['app_info']['version']
        template_date = template_config['app_info'].get('release_date', 'N/A')
        safe_print(f"  {Colors.BOLD}Шаблон:{Colors.NC}")
        safe_print(f"    Версия:      {Colors.GREEN}{template_version}{Colors.NC}")
        safe_print(f"    Дата релиза: {template_date}")
        safe_print(f"    Файл:        config/config.json.template")
    
    # Локальный config
    local_config = read_config_file('../config.json')
    if local_config:
        local_version = local_config['app_info']['version']
        local_date = local_config['app_info'].get('release_date', 'N/A')
        safe_print(f"  {Colors.BOLD}Локальный:{Colors.NC}")
        safe_print(f"    Версия:      {Colors.GREEN}{local_version}{Colors.NC}")
        safe_print(f"    Дата релиза: {local_date}")
        safe_print(f"    Файл:        config.json")
        
        # Сравнение версий
        if template_config and template_version != local_version:
            versions_differ = True
            safe_print(f"    {Colors.RED}{Emoji.WARN} ⚠️ Версии отличаются!{Colors.NC}")
    else:
        safe_print(f"  {Colors.YELLOW}Локальный: config.json не найден{Colors.NC}")
    
    # Modern Edition
    safe_print(f"\n{Colors.BLUE}{Emoji.INFO} Modern Edition (PySide6){Colors.NC}")
    
    # Шаблон
    template_config = read_config_template('../config/config_qt.json.template')
    if template_config:
        template_version = template_config['app_info']['version']
        template_date = template_config['app_info'].get('release_date', 'N/A')
        # Проверяем app_id в разных секциях
        template_app_id = template_config.get('telegram_security', {}).get('app_id') or \
                          template_config.get('api_keys', {}).get('app_id') or 'N/A'
        safe_print(f"  {Colors.BOLD}Шаблон:{Colors.NC}")
        safe_print(f"    Версия:      {Colors.GREEN}{template_version}{Colors.NC}")
        safe_print(f"    Дата релиза: {template_date}")
        safe_print(f"    APP_ID:      {template_app_id}")
        safe_print(f"    Файл:        config/config_qt.json.template")
    
    # Локальный config
    local_config = read_config_file('../config_qt.json')
    if local_config:
        local_version = local_config['app_info']['version']
        local_date = local_config['app_info'].get('release_date', 'N/A')
        local_app_id = local_config.get('telegram_security', {}).get('app_id') or \
                       local_config.get('api_keys', {}).get('app_id') or 'N/A'
        safe_print(f"  {Colors.BOLD}Локальный:{Colors.NC}")
        safe_print(f"    Версия:      {Colors.GREEN}{local_version}{Colors.NC}")
        safe_print(f"    Дата релиза: {local_date}")
        safe_print(f"    APP_ID:      {local_app_id}")
        safe_print(f"    Файл:        config_qt.json")
        
        # Сравнение версий
        if template_config and template_version != local_version:
            versions_differ = True
            safe_print(f"    {Colors.RED}{Emoji.WARN} ⚠️ Версии отличаются!{Colors.NC}")
        
        # Сравнение app_id
        if template_config and template_app_id != local_app_id:
            versions_differ = True
            safe_print(f"    {Colors.RED}{Emoji.WARN} ⚠️ APP_ID отличается! (Шаблон: {template_app_id}, Локальный: {local_app_id}){Colors.NC}")
    else:
        safe_print(f"  {Colors.YELLOW}Локальный: config_qt.json не найден{Colors.NC}")
    
    # User config (установленное приложение)
    import os
    import sys
    if sys.platform == 'darwin':  # macOS
        user_config_path = os.path.expanduser('~/Library/Application Support/BOMCategorizerModern/config_qt.json')
    elif sys.platform == 'win32':  # Windows
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        user_config_path = os.path.join(appdata, 'BOMCategorizerModern', 'config_qt.json')
    else:  # Linux
        user_config_path = os.path.expanduser('~/.config/BOMCategorizerModern/config_qt.json')
    
    user_config = read_config_file(user_config_path)
    if user_config:
        user_version = user_config['app_info']['version']
        user_date = user_config['app_info'].get('release_date', 'N/A')
        safe_print(f"  {Colors.BOLD}User config (установленное приложение):{Colors.NC}")
        safe_print(f"    Версия:      {Colors.GREEN}{user_version}{Colors.NC}")
        safe_print(f"    Дата релиза: {user_date}")
        safe_print(f"    Файл:        {user_config_path}")
        # User config может отличаться от текущего репозитория (это настройки установленной сборки).
        # Это НЕ повод делать sync репозитория — установленная сборка сама синхронизирует app_info при запуске.
        if template_config and template_version != user_version:
            safe_print(f"    {Colors.YELLOW}{Emoji.WARN} ⚠️ Версии отличаются (repo vs installed).{Colors.NC}")
            safe_print(f"    {Colors.YELLOW}      Запустите установленное приложение после обновления или переустановите сборку.{Colors.NC}")
    
    # Скрипты сборки
    safe_print(f"\n{Colors.BLUE}{Emoji.INFO} Файлы сборки (читают из шаблонов){Colors.NC}")
    safe_print(f"  - deployment/build_macos.sh")
    safe_print(f"  - deployment/installer_clean.iss (через sync_installer_versions.py)")
    safe_print(f"  - deployment/installer_qt.iss (через sync_installer_versions.py)")
    
    safe_print("\n" + "=" * 70)
    
    # Рекомендации
    if versions_differ:
        safe_print(f"\n{Colors.RED}{Emoji.WARN} ⚠️ ОБНАРУЖЕНЫ РАСХОЖДЕНИЯ В ВЕРСИЯХ!{Colors.NC}")
        safe_print(f"{Colors.YELLOW}   Локальные версии отличаются от версий в шаблонах.{Colors.NC}")
        safe_print(f"{Colors.YELLOW}   Выполните синхронизацию:{Colors.NC}")
        safe_print(f"{Colors.BOLD}   {Colors.GREEN}python tools/update_version.py sync{Colors.NC}\n")
    else:
        safe_print(f"\n{Colors.GREEN}{Emoji.CHECK} Все версии синхронизированы{Colors.NC}")
        safe_print(f"{Colors.YELLOW}{Emoji.INFO} Используйте 'python tools/update_version.py sync' для синхронизации файлов сборки{Colors.NC}\n")


def update_version(edition, new_version, update_date=True):
    """
    Обновляет версию в шаблоне config
    
    Args:
        edition: 'standard' или 'modern'
        new_version: новая версия (например, '3.4.0')
        update_date: обновить ли дату релиза
    """
    if edition == 'standard':
        template_path = '../config/config.json.template'
        edition_name = "Standard Edition"
    elif edition == 'modern':
        template_path = '../config/config_qt.json.template'
        edition_name = "Modern Edition"
    else:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Неизвестная edition: {edition}{Colors.NC}")
        return False
    
    # Читаем config
    config = read_config_template(template_path)
    if not config:
        return False
    
    # Получаем старую версию
    old_version = config['app_info']['version']
    edition_value = config['app_info'].get('edition', edition_name)
    
    # Обновляем версию
    config['app_info']['version'] = new_version
    
    # Обновляем даты
    if update_date:
        now = datetime.now()
        release_date = now.strftime("%d.%m.%Y")
        last_updated = now.strftime("%Y-%m-%d")
        config['app_info']['release_date'] = release_date
        config['app_info']['last_updated'] = last_updated
    else:
        release_date = None
        last_updated = None
    
    # Сохраняем
    if write_config_template(template_path, config):
        safe_print(f"{Colors.GREEN}{Emoji.CHECK} {edition_name}: {old_version} {Emoji.ARROW} {new_version}{Colors.NC}")
        if update_date:
            safe_print(f"   Дата обновлена: {config['app_info']['release_date']}")
        
        # Обновляем локальный config, если он существует
        if edition == 'standard':
            local_config_path = '../config.json'
        elif edition == 'modern':
            local_config_path = '../config_qt.json'
        else:
            local_config_path = None
        
        if local_config_path:
            update_local_config(
                local_config_path,
                new_version,
                edition_value,
                release_date=release_date if update_date else None,
                last_updated=last_updated if update_date else None
            )
        return True
    
    return False


def update_hardcoded_version(file_path, old_version_pattern, new_version, description):
    """
    Обновляет захардкоженную версию в Python файле
    
    Args:
        file_path: путь к файлу
        old_version_pattern: регулярное выражение для поиска старой версии
        new_version: новая версия
        description: описание файла для вывода
    
    Returns:
        bool: True если обновление прошло успешно
    """
    if not os.path.exists(file_path):
        safe_print(f"{Colors.YELLOW}{Emoji.WARN} Файл не найден: {file_path}{Colors.NC}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем и заменяем версию
        new_content, count = re.subn(old_version_pattern, rf'\g<1>"{new_version}"', content)
        
        if count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            safe_print(f"{Colors.GREEN}   {Emoji.ARROW} {description}: обновлено {count} вхождени{'е' if count == 1 else 'й'} → {new_version}{Colors.NC}")
            return True
        else:
            safe_print(f"{Colors.YELLOW}   {Emoji.INFO} {description}: версия не найдена для обновления{Colors.NC}")
            return False
    except Exception as e:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Ошибка обновления {file_path}: {e}{Colors.NC}")
        return False


def sync_hardcoded_versions():
    """Синхронизирует захардкоженные версии в Python файлах с шаблоном"""
    safe_print(f"\n{Colors.BLUE}{Emoji.INFO} Синхронизация захардкоженных версий в коде:{Colors.NC}")
    
    # Читаем версию из шаблона Modern Edition
    template_config = read_config_template('../config/config_qt.json.template')
    if not template_config:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Не удалось прочитать config_qt.json.template{Colors.NC}")
        return False
    
    modern_version = template_config['app_info']['version']
    safe_print(f"  Целевая версия Modern Edition: {Colors.GREEN}{modern_version}{Colors.NC}")
    
    # Обновляем gui_qt.py (fallback версия)
    # Ищем: return {"app_info": {"version": "X.X.X"
    pattern_gui = r'(return \{"app_info": \{"version": )"[^"]+"'
    gui_qt_path = '../bom_categorizer/gui_qt.py'
    if os.path.exists(gui_qt_path):
        update_hardcoded_version(
            gui_qt_path,
            pattern_gui,
            modern_version,
            'bom_categorizer/gui_qt.py (fallback)'
        )
    else:
        safe_print(f"{Colors.YELLOW}   {Emoji.INFO} bom_categorizer/gui_qt.py отсутствует — пропускаю{Colors.NC}")
    
    # Обновляем config_manager.py (default config)
    # Ищем: "version": "X.X.X" в блоке if "qt" in config_name
    pattern_config = r'(if "qt" in config_name:[\s\S]{0,200}"version": )"[^"]+"'
    update_hardcoded_version(
        '../bom_categorizer/config_manager.py',
        pattern_config,
        modern_version,
        'bom_categorizer/config_manager.py (default config)'
    )
    
    safe_print(f"{Colors.GREEN}   {Emoji.CHECK} Захардкоженные версии синхронизированы{Colors.NC}")
    return True


def sync_all():
    """Синхронизирует все файлы сборки и локальные config с шаблонами"""
    safe_print(f"\n{Colors.BOLD}{Emoji.SYNC} СИНХРОНИЗАЦИЯ ФАЙЛОВ СБОРКИ И ЛОКАЛЬНЫХ CONFIG{Colors.NC}\n")
    safe_print("=" * 70)

    # ВАЖНО:
    # sync НЕ должен менять шаблоны (источник правды).
    # Даты/версии в шаблонах меняются только через команду `set` или scripts/bump_version.py.

    # Синхронизация локальных config файлов
    safe_print(f"\n{Colors.BLUE}{Emoji.INFO} Синхронизация локальных config файлов:{Colors.NC}")
    
    # Standard Edition
    template_config = read_config_template('../config/config.json.template')
    if template_config:
        template_version = template_config['app_info']['version']
        template_edition = template_config['app_info'].get('edition', 'Standard')
        template_release_date = template_config['app_info'].get('release_date')
        template_last_updated = template_config['app_info'].get('last_updated')
        
        local_config = read_config_file('../config.json')
        if local_config:
            local_version = local_config['app_info']['version']
            local_date = local_config.get('app_info', {}).get('release_date')
            local_last_updated = local_config.get('app_info', {}).get('last_updated')
            needs_update = (
                template_version != local_version
                or (template_release_date is not None and template_release_date != local_date)
                or (template_last_updated is not None and template_last_updated != local_last_updated)
            )
            if needs_update:
                safe_print(f"  {Colors.YELLOW}config.json: синхронизирую app_info → v{template_version} / {template_release_date}{Colors.NC}")
                update_local_config(
                    '../config.json',
                    template_version,
                    template_edition,
                    release_date=template_release_date,
                    last_updated=template_last_updated
                )
            else:
                safe_print(f"  {Colors.GREEN}{Emoji.CHECK} config.json уже синхронизирован (v{local_version}){Colors.NC}")
        else:
            safe_print(f"  {Colors.YELLOW}config.json не найден (будет создан при первом запуске){Colors.NC}")
    
    # Modern Edition
    template_config = read_config_template('../config/config_qt.json.template')
    if template_config:
        template_version = template_config['app_info']['version']
        template_edition = template_config['app_info'].get('edition', 'Modern Edition')
        template_release_date = template_config['app_info'].get('release_date')
        template_last_updated = template_config['app_info'].get('last_updated')
        template_app_id = template_config.get('telegram_security', {}).get('app_id') or \
                          template_config.get('api_keys', {}).get('app_id')
        
        local_config = read_config_file('../config_qt.json')
        if local_config:
            local_version = local_config['app_info']['version']
            local_date = local_config.get('app_info', {}).get('release_date')
            local_last_updated = local_config.get('app_info', {}).get('last_updated')
            local_app_id = local_config.get('telegram_security', {}).get('app_id') or \
                           local_config.get('api_keys', {}).get('app_id')
            
            needs_update = False
            
            if template_version != local_version:
                safe_print(f"  {Colors.YELLOW}config_qt.json: версия {local_version} → {template_version}{Colors.NC}")
                needs_update = True

            if template_release_date is not None and template_release_date != local_date:
                safe_print(f"  {Colors.YELLOW}config_qt.json: дата {local_date} → {template_release_date}{Colors.NC}")
                needs_update = True

            if template_last_updated is not None and template_last_updated != local_last_updated:
                safe_print(f"  {Colors.YELLOW}config_qt.json: last_updated {local_last_updated} → {template_last_updated}{Colors.NC}")
                needs_update = True
            
            if template_app_id and local_app_id != template_app_id:
                safe_print(f"  {Colors.YELLOW}config_qt.json: app_id {local_app_id} → {template_app_id}{Colors.NC}")
                needs_update = True
            
            if needs_update:
                # Обновляем app_info
                update_local_config(
                    '../config_qt.json',
                    template_version,
                    template_edition,
                    release_date=template_release_date,
                    last_updated=template_last_updated
                )
                
                # Обновляем app_id в соответствующих секциях
                if template_app_id:
                    try:
                        with open('../config_qt.json', 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        # Обновляем в обеих секциях для совместимости
                        if 'telegram_security' not in config:
                            config['telegram_security'] = {}
                        config['telegram_security']['app_id'] = template_app_id
                        
                        if 'api_keys' not in config:
                            config['api_keys'] = {}
                        config['api_keys']['app_id'] = template_app_id
                        
                        with open('../config_qt.json', 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=2, ensure_ascii=False)
                            f.write('\n')
                        
                        safe_print(f"{Colors.GREEN}   {Emoji.ARROW} APP_ID обновлен → {template_app_id}{Colors.NC}")
                    except Exception as e:
                        safe_print(f"{Colors.RED}{Emoji.ERROR} Ошибка обновления APP_ID: {e}{Colors.NC}")
            else:
                safe_print(f"  {Colors.GREEN}{Emoji.CHECK} config_qt.json уже синхронизирован (v{local_version}, app_id: {local_app_id}){Colors.NC}")
        else:
            safe_print(f"  {Colors.YELLOW}config_qt.json не найден (будет создан при первом запуске){Colors.NC}")
        # ВАЖНО:
        # sync НЕ должен трогать user config установленного приложения в профиле пользователя.
        # Версия/дата для installed app синхронизируются при запуске самого приложения
        # (из шаблона, упакованного в .app/.exe), иначе возможны "понижения" при работе с разными репозиториями.
    
    # Синхронизация захардкоженных версий в Python файлах
    sync_hardcoded_versions()
    
    # Синхронизация файлов сборки (.iss)
    safe_print(f"\n{Colors.BLUE}{Emoji.INFO} Синхронизация файлов сборки:{Colors.NC}")
    
    # Запускаем sync_installer_versions.py
    try:
        result = subprocess.run(
            [sys.executable, 'sync_installer_versions.py'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False
        )
        safe_print(result.stdout)
        if result.returncode != 0:
            safe_print(result.stderr)
            safe_print(f"{Colors.YELLOW}{Emoji.WARN} sync_installer_versions.py завершился с кодом {result.returncode}{Colors.NC}")
    except Exception as e:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Ошибка выполнения sync_installer_versions.py: {e}{Colors.NC}")
        safe_print(f"{Colors.YELLOW}{Emoji.WARN} Убедитесь, что файл существует и имеет права на выполнение{Colors.NC}")
    
    # Build meta для UI (About/tooltip)
    write_build_meta()

    safe_print("=" * 70)
    safe_print(f"\n{Colors.GREEN}{Emoji.CHECK} Синхронизация завершена.{Colors.NC}")
    safe_print(f"{Colors.YELLOW}{Emoji.INFO} Локальные config обновлены (только секция app_info, личные настройки сохранены){Colors.NC}")
    safe_print(f"{Colors.YELLOW}{Emoji.INFO} Захардкоженные версии в Python файлах обновлены автоматически{Colors.NC}")
    safe_print(f"{Colors.YELLOW}{Emoji.INFO} build_macos.sh автоматически читает версии из шаблонов{Colors.NC}\n")


def print_usage():
    """Выводит справку по использованию"""
    safe_print(f"""
{Colors.BOLD}УПРАВЛЕНИЕ ВЕРСИЯМИ BOM CATEGORIZER{Colors.NC}

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

{Colors.YELLOW}{Emoji.WARN} Источник правды:{Colors.NC}
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
            safe_print(f"{Colors.RED}{Emoji.ERROR} Недостаточно аргументов{Colors.NC}")
            safe_print(f"Использование: python update_version.py set <standard|modern|both> <версия>")
            return 1
        
        edition = sys.argv[2].lower()
        new_version = sys.argv[3]
        
        success = True
        if edition == 'both':
            success = update_version('standard', new_version) and update_version('modern', new_version)
        elif edition in ['standard', 'modern']:
            success = update_version(edition, new_version)
        else:
            safe_print(f"{Colors.RED}{Emoji.ERROR} Неизвестная edition: {edition}{Colors.NC}")
            safe_print(f"Используйте: standard, modern или both")
            return 1
        
        if success:
            safe_print(f"\n{Colors.GREEN}{Emoji.CHECK} Версия обновлена в шаблонах{Colors.NC}")
            safe_print(f"{Colors.YELLOW}{Emoji.INFO} Синхронизирую файлы сборки...{Colors.NC}")
            sync_all()
        else:
            return 1
        
    elif command == 'sync':
        sync_all()
        
    elif command in ['help', '--help', '-h']:
        print_usage()
        
    else:
        safe_print(f"{Colors.RED}{Emoji.ERROR} Неизвестная команда: {command}{Colors.NC}")
        print_usage()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

