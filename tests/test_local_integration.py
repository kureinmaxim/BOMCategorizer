#!/usr/bin/env python3
"""
Тест интеграции BOMCategorizer с TelegramHelper (локальный сервер).
Проверяет обфусцированное шифрование через /ai_query/secure endpoint.
"""

import sys
import os
import json
import base64
import time

# Добавляем путь к модулям BOMCategorizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bom_categorizer.encryption import SecureMessenger
import requests

def test_local_integration():
    """Тест полной интеграции с локальным сервером"""
    
    # Конфигурация (из TelegramHelper/.env)
    API_URL = "http://localhost:8000"
    API_KEY = "test_secret_key_32_bytes_long_12345"
    ENCRYPTION_KEY = "test_secret_key_32_bytes_long_12345"
    APP_ID = "bomcategorizer-v4"
    
    print("🔧 Инициализация...")
    messenger = SecureMessenger(ENCRYPTION_KEY)
    
    # Тестовый запрос
    test_query = """Классифицируй компонент: LM358
    
Укажи:
1. Категорию (например: Микросхема, Резистор, Конденсатор и т.д.)
2. Краткое описание
3. Уверенность (high/medium/low)"""
    
    request_data = {
        "prompt": test_query,
        "provider": "openai",
        "max_tokens": 500
    }
    
    print(f"\n📤 Отправка запроса на {API_URL}/ai_query/secure...")
    print(f"   Query: {test_query[:50]}...")
    
    try:
        # 1. Шифруем
        encrypted_bytes = messenger.encrypt(request_data)
        print(f"   ✓ Зашифровано: {len(encrypted_bytes)} байт")
        
        # 2. Маскируем (Base64)
        b64_payload = base64.b64encode(encrypted_bytes).decode('utf-8')
        print(f"   ✓ Base64: {len(b64_payload)} символов")
        
        # 3. Формируем заголовки безопасности
        timestamp = str(int(time.time()))
        nonce = os.urandom(8).hex()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": API_KEY,
            "X-APP-ID": APP_ID,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # 4. Отправляем
        response = requests.post(
            f"{API_URL}/ai_query/secure",
            json={"data": b64_payload},
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Ответ сервера: HTTP {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Ошибка: {response.text}")
            return False
        
        # 5. Разбираем ответ
        response_json = response.json()
        if "data" not in response_json:
            print(f"   ❌ Некорректный формат ответа: {response_json}")
            return False
        
        # 6. Декодируем Base64
        encrypted_response_bytes = base64.b64decode(response_json["data"])
        print(f"   ✓ Base64 декодирован: {len(encrypted_response_bytes)} байт")
        
        # 7. Расшифровываем
        decrypted_response = messenger.decrypt(encrypted_response_bytes)
        
        if isinstance(decrypted_response, bytes):
            response_data = json.loads(decrypted_response.decode('utf-8'))
        else:
            response_data = decrypted_response
        
        print(f"   ✓ Расшифровано успешно")
        
        # 8. Показываем результат
        print("\n" + "="*60)
        print("📋 РЕЗУЛЬТАТ:")
        print("="*60)
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        print("="*60)
        
        print("\n✅ Тест пройден успешно!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Не удалось подключиться к серверу!")
        print("   Убедитесь, что TelegramHelper API запущен: python3 api.py")
        return False
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Тест интеграции BOMCategorizer ↔ TelegramHelper (локально)")
    print("="*60)
    
    success = test_local_integration()
    
    sys.exit(0 if success else 1)
