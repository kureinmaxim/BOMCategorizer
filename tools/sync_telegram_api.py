#!/usr/bin/env python3
"""
Синхронизация API ключа TelegramHelper с BOMCategorizer.

Использование:
    python tools/sync_telegram_api.py              # Интерактивный режим
    python tools/sync_telegram_api.py --fetch      # Получить ключ с сервера
    python tools/sync_telegram_api.py --key KEY    # Установить конкретный ключ
    python tools/sync_telegram_api.py --show       # Показать текущие настройки
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path

# Конфигурация
SERVER_SSH = "root@YOUR_SERVER_IP"
SERVER_PORT = "22542"
SERVER_PATH = "/opt/TelegramHelper/.env"
API_URL = "http://YOUR_SERVER_IP:8000/ai_query"

def get_project_root() -> Path:
    """Получить корень проекта BOMCategorizer."""
    return Path(__file__).parent.parent

def get_config_paths() -> dict:
    """Получить пути к конфигурационным файлам."""
    project_root = get_project_root()
    
    # Путь в проекте
    project_config = project_root / "config_qt.json"
    
    # Путь установки (зависит от ОС)
    # ВАЖНО: Modern Edition использует папку BOMCategorizerModern!
    if sys.platform == "darwin":
        # macOS - Modern Edition
        app_support = Path.home() / "Library" / "Application Support" / "BOMCategorizerModern"
        installed_config = app_support / "config_qt.json"
    elif sys.platform == "win32":
        # Windows - Modern Edition
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        installed_config = appdata / "BOMCategorizerModern" / "config_qt.json"
    else:
        # Linux
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        installed_config = config_home / "BOMCategorizerModern" / "config_qt.json"
    
    return {
        "project": project_config,
        "installed": installed_config
    }

def load_config(config_path: Path) -> dict:
    """Загрузить конфигурацию из файла."""
    if not config_path.exists():
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config_path: Path, config: dict):
    """Сохранить конфигурацию в файл."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def fetch_key_from_server() -> str:
    """Получить API ключ с сервера через SSH."""
    print(f"🔄 Получение ключа с сервера {SERVER_SSH}...")
    
    try:
        cmd = [
            "ssh", "-p", SERVER_PORT, SERVER_SSH,
            f"grep '^API_SECRET_KEY=' {SERVER_PATH} | cut -d'=' -f2"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ Ошибка SSH: {result.stderr}")
            return ""
        
        key = result.stdout.strip()
        if key:
            print(f"✅ Ключ получен: {key[:16]}...")
            return key
        else:
            print("❌ Ключ не найден на сервере")
            return ""
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут подключения к серверу")
        return ""
    except FileNotFoundError:
        print("❌ SSH не найден. Установите OpenSSH.")
        return ""
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return ""

def update_config_with_key(config: dict, key: str, url: str = None) -> dict:
    """Обновить конфигурацию с новым ключом."""
    if "api_keys" not in config:
        config["api_keys"] = {}
    
    config["api_keys"]["telegram_key"] = key
    
    if url:
        config["api_keys"]["telegram_url"] = url
    elif "telegram_url" not in config["api_keys"]:
        config["api_keys"]["telegram_url"] = API_URL
    
    return config

def show_current_settings():
    """Показать текущие настройки API."""
    paths = get_config_paths()
    
    print("\n📋 Текущие настройки API:\n")
    print("=" * 60)
    
    for name, path in paths.items():
        location = "Проект" if name == "project" else "Установка"
        print(f"\n📁 {location}: {path}")
        
        if path.exists():
            config = load_config(path)
            api_keys = config.get("api_keys", {})
            url = api_keys.get("telegram_url", "не установлен")
            key = api_keys.get("telegram_key", "")
            
            print(f"   URL: {url}")
            if key:
                print(f"   Key: {key[:16]}...{key[-8:]}")
            else:
                print("   Key: не установлен")
        else:
            print("   ⚠️  Файл не существует")
    
    print("\n" + "=" * 60)

def sync_api_key(key: str, url: str = None):
    """Синхронизировать ключ во все конфигурации."""
    paths = get_config_paths()
    
    print(f"\n🔄 Синхронизация API ключа...")
    print(f"   Ключ: {key[:16]}...{key[-8:]}")
    if url:
        print(f"   URL: {url}")
    
    updated = []
    
    for name, path in paths.items():
        location = "Проект" if name == "project" else "Установка"
        
        try:
            config = load_config(path) if path.exists() else {}
            config = update_config_with_key(config, key, url)
            save_config(path, config)
            print(f"   ✅ {location}: {path}")
            updated.append(name)
        except Exception as e:
            print(f"   ❌ {location}: {e}")
    
    return updated

def test_api_connection():
    """Тестировать соединение с API."""
    import urllib.request
    import urllib.error
    
    paths = get_config_paths()
    config = load_config(paths["project"])
    
    api_keys = config.get("api_keys", {})
    url = api_keys.get("telegram_url", API_URL)
    key = api_keys.get("telegram_key", "")
    
    # Тест 1: Health check
    health_url = url.replace("/ai_query", "/health")
    print(f"\n🔍 Тестирование API...")
    print(f"   URL: {health_url}")
    
    try:
        req = urllib.request.Request(health_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode("utf-8")
            print(f"   ✅ Health check: OK")
            print(f"   📋 Ответ: {data[:100]}...")
    except urllib.error.URLError as e:
        print(f"   ❌ Health check: {e.reason}")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Тест 2: AI запрос
    if not key:
        print(f"   ⚠️  API ключ не настроен, пропускаю тест AI запроса")
        return True
    
    print(f"\n🤖 Тестирование AI запроса...")
    print(f"   URL: {url}")
    print(f"   Key: {key[:16]}...")
    
    try:
        import json as json_module
        
        data = json_module.dumps({
            "prompt": "Кратко опиши компонент NE555",
            "provider": "anthropic",
            "max_tokens": 200
        }).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": key
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json_module.loads(response.read().decode("utf-8"))
            status = result.get("status", "unknown")
            provider = result.get("provider", "unknown")
            
            if status == "success":
                print(f"   ✅ AI запрос: OK")
                print(f"   📋 Провайдер: {provider}")
                print(f"   📋 Ответ: {result.get('response', '')[:100]}...")
                return True
            else:
                print(f"   ❌ AI запрос: {result.get('error', 'Unknown error')}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP ошибка: {e.code} {e.reason}")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

def interactive_mode():
    """Интерактивный режим."""
    print("\n🔐 Синхронизация API ключа TelegramHelper\n")
    print("Выберите действие:")
    print("  1) Получить ключ с сервера и синхронизировать")
    print("  2) Ввести ключ вручную")
    print("  3) Показать текущие настройки")
    print("  4) Тестировать соединение с API")
    print("  5) Выход")
    
    choice = input("\nВыберите (1-5): ").strip()
    
    if choice == "1":
        key = fetch_key_from_server()
        if key:
            sync_api_key(key, API_URL)
            print("\n✅ Синхронизация завершена!")
            print("   Перезапустите BOMCategorizer для применения изменений.")
    
    elif choice == "2":
        key = input("Введите API ключ: ").strip()
        if key:
            url = input(f"Введите URL (Enter для {API_URL}): ").strip() or API_URL
            sync_api_key(key, url)
            print("\n✅ Синхронизация завершена!")
        else:
            print("❌ Ключ не введён")
    
    elif choice == "3":
        show_current_settings()
    
    elif choice == "4":
        test_api_connection()
    
    elif choice == "5":
        print("Выход.")
    
    else:
        print("❌ Неверный выбор")

def main():
    parser = argparse.ArgumentParser(
        description="Синхронизация API ключа TelegramHelper с BOMCategorizer"
    )
    parser.add_argument(
        "--fetch", "-f",
        action="store_true",
        help="Получить ключ с сервера и синхронизировать"
    )
    parser.add_argument(
        "--key", "-k",
        type=str,
        help="Установить конкретный API ключ"
    )
    parser.add_argument(
        "--url", "-u",
        type=str,
        default=API_URL,
        help=f"URL API (по умолчанию: {API_URL})"
    )
    parser.add_argument(
        "--show", "-s",
        action="store_true",
        help="Показать текущие настройки"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Тестировать соединение с API"
    )
    
    args = parser.parse_args()
    
    if args.test:
        success = test_api_connection()
        sys.exit(0 if success else 1)
    elif args.show:
        show_current_settings()
    elif args.fetch:
        key = fetch_key_from_server()
        if key:
            sync_api_key(key, args.url)
            print("\n✅ Синхронизация завершена!")
    elif args.key:
        sync_api_key(args.key, args.url)
        print("\n✅ Синхронизация завершена!")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()

