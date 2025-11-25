#!/usr/bin/env python3
"""
AI Search CLI - Поиск информации о компонентах через AI

Использование:
    python tools/ai_search.py "TPS54302" --provider telegram
    python tools/ai_search.py "LM2596" --provider anthropic --prompt analogs
    python tools/ai_search.py --list-prompts
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Добавляем корень проекта в PATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_config():
    """Загружает конфигурацию из config_qt.json"""
    config_path = PROJECT_ROOT / "config_qt.json"
    if not config_path.exists():
        config_path = PROJECT_ROOT / "config.json"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_prompt_templates():
    """Возвращает доступные шаблоны промптов"""
    return {
        "info": {
            "name": "Информация о компоненте",
            "template": """Найди информацию об электронном компоненте: {component}

Предоставь:
1. Полное название и производитель
2. Тип компонента
3. Основные характеристики
4. Описание назначения
5. Примеры использования

Формат: краткий текст 100-150 слов."""
        },
        "ivp_short": {
            "name": "Краткое описание ИВП",
            "template": """Составь краткое техническое описание ИВП: {component}

Требуется:
1. Полное название и производитель
2. Тип (DC-DC, LDO, POL и т.д.)
3. Характеристики (Vin, Vout, Iout, КПД, частота, корпус)
4. Ключевые преимущества
5. Обоснование невозможности замены на отечественные аналоги

Формат: текст 150-200 слов."""
        },
        "ivp_full": {
            "name": "Полное описание ИВП",
            "template": """Подготовь развёрнутое описание ИВП: {component}

Структура:
1. ОБЩАЯ ИНФОРМАЦИЯ
2. ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ (таблица)
3. КОНСТРУКТИВНЫЕ ОСОБЕННОСТИ
4. ПРЕИМУЩЕСТВА
5. РЕКОМЕНДАЦИИ ПО ПРИМЕНЕНИЮ

Объём: 200-400 слов."""
        },
        "analogs": {
            "name": "Поиск аналогов",
            "template": """Найди все существующие аналоги для: {component}

Категории:
1. ПРЯМЫЕ АНАЛОГИ (pin-to-pin совместимые)
2. ФУНКЦИОНАЛЬНЫЕ АНАЛОГИ
3. БЮДЖЕТНЫЕ АЛЬТЕРНАТИВЫ

Для каждого укажи:
- Название и производитель
- Степень совместимости
- Ключевые отличия"""
        },
        "compare": {
            "name": "Сравнительный анализ",
            "template": """Проведи сравнительный анализ: {component}

Требуется:
1. Идентификация компонента
2. 3-5 основных конкурентов
3. Сравнительная таблица параметров
4. Выводы и рекомендации"""
        }
    }

def search_telegram(prompt: str, config: dict) -> str:
    """Поиск через TelegramHelper API"""
    import requests
    
    api_keys = config.get("api_keys", {})
    url = api_keys.get("telegram_url", "")
    api_key = api_keys.get("telegram_key", "")
    
    if not url or not api_key:
        return "❌ Ошибка: telegram_url или telegram_key не настроены в config_qt.json"
    
    try:
        response = requests.post(
            url,
            json={"prompt": prompt, "provider": "anthropic", "max_tokens": 2048},
            headers={"X-API-KEY": api_key},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "Пустой ответ от API")
        else:
            return f"❌ Ошибка API: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return "❌ Ошибка: Не удалось подключиться к серверу. Проверьте telegram_url."
    except Exception as e:
        return f"❌ Ошибка: {e}"

def search_anthropic(prompt: str, config: dict) -> str:
    """Прямой поиск через Anthropic API"""
    try:
        import anthropic
    except ImportError:
        return "❌ Ошибка: pip install anthropic"
    
    api_key = config.get("api_keys", {}).get("anthropic", "")
    if not api_key:
        return "❌ Ошибка: anthropic ключ не настроен в config_qt.json"
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"❌ Ошибка Anthropic: {e}"

def search_openai(prompt: str, config: dict) -> str:
    """Прямой поиск через OpenAI API"""
    try:
        import openai
    except ImportError:
        return "❌ Ошибка: pip install openai"
    
    api_key = config.get("api_keys", {}).get("openai", "")
    if not api_key:
        return "❌ Ошибка: openai ключ не настроен в config_qt.json"
    
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты эксперт по электронным компонентам."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка OpenAI: {e}"

def main():
    parser = argparse.ArgumentParser(
        description="AI поиск информации о компонентах",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python tools/ai_search.py "TPS54302"
  python tools/ai_search.py "LM2596" --provider anthropic
  python tools/ai_search.py "STM32F103" --prompt analogs
  python tools/ai_search.py --list-prompts
        """
    )
    
    parser.add_argument("component", nargs="?", help="Название компонента для поиска")
    parser.add_argument("--provider", "-p", 
                        choices=["telegram", "anthropic", "openai"],
                        default="telegram",
                        help="AI провайдер (по умолчанию: telegram)")
    parser.add_argument("--prompt", "-t",
                        choices=["info", "ivp_short", "ivp_full", "analogs", "compare"],
                        default="info",
                        help="Тип промпта (по умолчанию: info)")
    parser.add_argument("--list-prompts", "-l", action="store_true",
                        help="Показать доступные типы промптов")
    parser.add_argument("--raw", "-r", action="store_true",
                        help="Использовать component как сырой промпт")
    parser.add_argument("--output", "-o", help="Сохранить результат в файл")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Вывод в формате JSON")
    
    args = parser.parse_args()
    
    # Показать список промптов
    if args.list_prompts:
        templates = get_prompt_templates()
        print("\n📋 Доступные типы промптов:\n")
        for key, value in templates.items():
            print(f"  {key:12} - {value['name']}")
        print("\nИспользование: python tools/ai_search.py \"КОМПОНЕНТ\" --prompt ТИП")
        return
    
    # Проверка наличия компонента
    if not args.component:
        parser.print_help()
        return
    
    # Загрузка конфига
    config = load_config()
    
    # Формирование промпта
    if args.raw:
        prompt = args.component
    else:
        templates = get_prompt_templates()
        template = templates[args.prompt]["template"]
        prompt = template.format(component=args.component)
    
    # Вывод информации о запросе
    if not args.json:
        print(f"\n🔍 Поиск: {args.component}")
        print(f"📡 Провайдер: {args.provider}")
        print(f"📝 Тип промпта: {args.prompt}")
        print("-" * 50)
    
    # Выполнение поиска
    if args.provider == "telegram":
        result = search_telegram(prompt, config)
    elif args.provider == "anthropic":
        result = search_anthropic(prompt, config)
    elif args.provider == "openai":
        result = search_openai(prompt, config)
    
    # Вывод результата
    if args.json:
        output = {
            "component": args.component,
            "provider": args.provider,
            "prompt_type": args.prompt,
            "result": result
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n{result}\n")
    
    # Сохранение в файл
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            if args.json:
                json.dump(output, f, ensure_ascii=False, indent=2)
            else:
                f.write(result)
        print(f"✅ Результат сохранён в: {args.output}")

if __name__ == "__main__":
    main()







