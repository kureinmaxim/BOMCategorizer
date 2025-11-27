#!/usr/bin/env python3
"""
Тест подключения к РЕАЛЬНОМУ серверу с обфускацией.
"""

import sys
import os
import json
import base64
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bom_categorizer.encryption import SecureMessenger
import requests

def test_production_server():
    """Тест подключения к реальному серверу"""
    
    # Конфигурация РЕАЛЬНОГО сервера
    API_URL = "http://138.124.19.67:8000"
    API_KEY = "13ab4a4f0c5d57ecf93727ad684f1ac46f35971a65511bc962740b8eb8bb79a2"
    ENCRYPTION_KEY = "13ab4a4f0c5d57ecf93727ad684f1ac46f35971a65511bc962740b8eb8bb79a2"
    APP_ID = "bomcategorizer-v4"
    
    print("🌐 Подключение к РЕАЛЬНОМУ серверу...")
    print(f"   URL: {API_URL}")
    
    messenger = SecureMessenger(ENCRYPTION_KEY)
    
    # Тестовый запрос (простой, чтобы не тратить много токенов AI)
    request_data = {
        "prompt": "Кратко опиши компонент LM358 в одном предложении.",
        "provider": "anthropic",
        "max_tokens": 100
    }
    
    print(f"\n📤 Отправка запроса...")
    
    try:
        # 1. Шифруем
        encrypted_bytes = messenger.encrypt(request_data)
        print(f"   ✓ Зашифровано: {len(encrypted_bytes)} байт")
        
        # 2. Обфускация (Base64)
        b64_payload = base64.b64encode(encrypted_bytes).decode('utf-8')
        print(f"   ✓ Обфусцировано: {len(b64_payload)} символов")
        
        # 3. Формируем заголовки
        timestamp = str(int(time.time()))
        nonce = os.urandom(8).hex()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": API_KEY,
            "X-APP-ID": APP_ID,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "User-Agent": "BOMCategorizer/4.5.2"
        }
        
        print(f"\n📡 Отправка на {API_URL}/ai_query/secure...")
        
        # 4. Отправляем
        response = requests.post(
            f"{API_URL}/ai_query/secure",
            json={"data": b64_payload},
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 HTTP {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Ошибка: {response.text}")
            return False
        
        # 5. Разбираем ответ
        response_json = response.json()
        if "data" not in response_json:
            print(f"   ❌ Некорректный формат: {response_json}")
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
        print("\n" + "="*70)
        print("🎉 УСПЕШНОЕ ПОДКЛЮЧЕНИЕ К РЕАЛЬНОМУ СЕРВЕРУ!")
        print("="*70)
        print("\n📋 Ответ от AI:")
        print("-"*70)
        print(response_data.get('response', 'N/A'))
        print("-"*70)
        print(f"\n📊 Метаданные:")
        print(f"   Провайдер: {response_data.get('provider', 'N/A')}")
        print(f"   Модель: {response_data.get('model', 'N/A')}")
        print(f"   Статус: {response_data.get('status', 'N/A')}")
        print(f"   Время обработки: {response_data.get('processing_time_ms', 'N/A')} мс")
        print("="*70)
        
        print("\n✅ ТЕСТ ПРОЙДЕН!")
        print("✓ Обфускация работает")
        print("✓ Шифрование работает")
        print("✓ Сервер доступен")
        print("✓ AI провайдер отвечает")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Не удалось подключиться к серверу!")
        print("   Проверьте доступность http://138.124.19.67:8000")
        return False
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Тест подключения к production серверу")
    print("   (с обфускацией Base64+JSON)")
    print("="*70)
    
    success = test_production_server()
    
    sys.exit(0 if success else 1)
