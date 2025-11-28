#!/usr/bin/env python3
"""
Скрипт управления версиями BOM Categorizer.

По умолчанию обновляет только Modern Edition (v5+).
Для обновления Standard Edition используйте --edition standard или --edition both.

Примеры:
    ./scripts/bump_version.py --bump patch           # Modern Edition
    ./scripts/bump_version.py --bump minor --edition standard  # Standard Edition
    ./scripts/bump_version.py --bump major --edition both      # Обе редакции
"""

import argparse
import re
import sys
import json
from datetime import datetime
from pathlib import Path

# Regex for JSON fields
VERSION_RE = re.compile(r'("version"\s*:\s*")(?P<version>[^"]+)(")', re.MULTILINE)
RELEASE_DATE_RE = re.compile(r'("release_date"\s*:\s*")(?P<date>[^"]+)(")', re.MULTILINE)
DEVELOPER_RE = re.compile(r'("developer"\s*:\s*")(?P<dev>[^"]+)(")', re.MULTILINE)
LAST_UPDATED_RE = re.compile(r'("last_updated"\s*:\s*")(?P<date>[^"]+)(")', re.MULTILINE)

# File configurations
EDITIONS = {
    "modern": {
        "template": "config/config_qt.json.template",
        "config": "config_qt.json",
        "name": "Modern Edition (v5+)"
    },
    "standard": {
        "template": "config/config.json.template", 
        "config": "config.json",
        "name": "Standard Edition (v3)"
    }
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Управление версиями BOM Categorizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s --bump patch                    # Увеличить patch версию Modern Edition
  %(prog)s --bump minor                    # Увеличить minor версию Modern Edition
  %(prog)s --bump major --edition both     # Увеличить major версию обеих редакций
  %(prog)s --version 5.1.0                 # Установить версию Modern Edition
  %(prog)s --version 3.4.0 --edition standard  # Установить версию Standard Edition
  %(prog)s --bump patch --no-release-date  # Без обновления даты релиза
        """
    )
    
    parser.add_argument(
        "--edition", 
        choices=["modern", "standard", "both"],
        default="modern",
        help="Какую редакцию обновить (по умолчанию: modern)"
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--version", help="Установить конкретную версию (например, 5.1.0)")
    group.add_argument("--bump", choices=["major", "minor", "patch"], help="Увеличить часть версии")
    
    parser.add_argument("--release-date", dest="release_date", help="Дата релиза в формате DD.MM.YYYY (по умолчанию: сегодня)")
    parser.add_argument("--developer", help="Имя разработчика")
    parser.add_argument("--no-release-date", action="store_true", help="Не обновлять дату релиза")
    parser.add_argument("--dry-run", action="store_true", help="Показать изменения без записи")
    
    return parser.parse_args()

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None

def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def get_current_version(content: str) -> str:
    m = VERSION_RE.search(content)
    if not m:
        return None
    return m.group("version")

def bump_version_str(v: str, which: str) -> str:
    parts = v.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        print(f"Error: неподдерживаемый формат версии '{v}'. Ожидается X.Y.Z", file=sys.stderr)
        sys.exit(1)
    major, minor, patch = map(int, parts)
    if which == "major":
        major += 1; minor = 0; patch = 0
    elif which == "minor":
        minor += 1; patch = 0
    elif which == "patch":
        patch += 1
    return f"{major}.{minor}.{patch}"

def update_content(content: str, new_version: str, args) -> str:
    # Apply version change
    if new_version:
        if VERSION_RE.search(content):
            content = VERSION_RE.sub(rf'\g<1>{new_version}\3', content, count=1)

    # Dates
    today_ymd = datetime.now().strftime("%Y-%m-%d")
    today_dmy = datetime.now().strftime("%d.%m.%Y")

    # last_updated always set to today
    if LAST_UPDATED_RE.search(content):
        content = LAST_UPDATED_RE.sub(rf'\g<1>{today_ymd}\3', content, count=1)

    # release_date set if provided or if version changed and not disabled
    if args.release_date:
        rd = args.release_date.strip()
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", rd):
            print("Error: --release-date должен быть в формате DD.MM.YYYY", file=sys.stderr)
            sys.exit(1)
        if RELEASE_DATE_RE.search(content):
            content = RELEASE_DATE_RE.sub(rf'\g<1>{rd}\3', content, count=1)
    elif new_version and not args.no_release_date:
        if RELEASE_DATE_RE.search(content):
            content = RELEASE_DATE_RE.sub(rf'\g<1>{today_dmy}\3', content, count=1)

    # developer
    if args.developer is not None:
        dev = args.developer
        if DEVELOPER_RE.search(content):
            content = DEVELOPER_RE.sub(rf'\g<1>{dev}\3', content, count=1)
            
    return content

def get_editions_to_update(edition_arg: str) -> list:
    """Возвращает список редакций для обновления."""
    if edition_arg == "both":
        return ["modern", "standard"]
    return [edition_arg]

def main():
    args = parse_args()
    
    if not args.version and not args.bump and not args.developer:
        print("Ничего не указано для обновления. Используйте --bump, --version или --developer")
        print("Справка: ./scripts/bump_version.py --help")
        sys.exit(0)
    
    editions_to_update = get_editions_to_update(args.edition)
    
    print(f"🎯 Обновление: {', '.join(ed.upper() for ed in editions_to_update)}")
    print()
    
    updated_files = []
    
    for edition_key in editions_to_update:
        edition = EDITIONS[edition_key]
        template_path = Path(edition["template"])
        config_path = Path(edition["config"])
        
        print(f"📦 {edition['name']}:")
        
        # Read template (required)
        template_content = read_text(template_path)
        if not template_content:
            print(f"   ❌ Шаблон не найден: {template_path}")
            continue
        
        current_version = get_current_version(template_content)
        if not current_version:
            print(f"   ❌ Версия не найдена в {template_path}")
            continue
        
        # Determine new version
        new_version = None
        if args.version:
            new_version = args.version.strip()
            if not re.match(r"^\d+\.\d+\.\d+$", new_version):
                print("Error: --version должен быть в формате X.Y.Z", file=sys.stderr)
                sys.exit(1)
        elif args.bump:
            new_version = bump_version_str(current_version, args.bump)
        
        if new_version:
            print(f"   Версия: {current_version} → {new_version}")
        
        if args.dry_run:
            print(f"   [DRY-RUN] Изменения не записаны")
            continue
        
        # Update template
        new_template_content = update_content(template_content, new_version, args)
        write_text(template_path, new_template_content)
        updated_files.append(template_path)
        print(f"   ✓ {template_path}")
        
        # Update active config if exists
        config_content = read_text(config_path)
        if config_content and get_current_version(config_content):
            new_config_content = update_content(config_content, new_version, args)
            write_text(config_path, new_config_content)
            updated_files.append(config_path)
            print(f"   ✓ {config_path}")
        
        print()
    
    # Summary
    if not args.dry_run and updated_files:
        today_dmy = datetime.now().strftime("%d.%m.%Y")
        print(f"✅ Обновлено {len(updated_files)} файл(ов)")
        
        if args.release_date or (new_version and not args.no_release_date):
            print(f"📅 Дата релиза: {args.release_date or today_dmy}")
        
        if args.developer:
            print(f"👤 Разработчик: {args.developer}")
        
        print()
        print("💡 Не забудьте:")
        print("   git add config/")
        print(f"   git commit -m \"Bump version to {new_version}\"")


if __name__ == "__main__":
    main()
