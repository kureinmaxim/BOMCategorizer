#!/usr/bin/env python3
"""
Простой тест обфускации без реального AI.
Проверяет только шифрование/расшифровку через /ai_query/secure.
"""

import sys
import os
import json
import base64
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bom_categorizer.encryption import SecureMessenger
import requests

def test_obfuscation_only():
    """Тест только обфускации (без AI)"""
    
    # Конфигурация
    API_URL = "http://localhost:8000"
    API_KEY = "test_secret_key_32_bytes_long_12345"
    ENCRYPTION_KEY = "test_secret_key_32_bytes_long_12345"
    APP_ID = "bomcategorizer-v4"
    
    print("🔧 Инициализация SecureMessenger...")
    messenger = SecureMessenger(ENCRYPTION_KEY)
    
    # Простой тестовый запрос (будет ошибка от AI, но обфускация проверится)
    request_data = {
        "prompt": "Тест",
        "provider": "anthropic",
        "max_tokens": 10
    }
    
    print(f"\n📤 Шифрование запроса...")
    
    try:
        # 1. Шифруем
        encrypted_bytes = messenger.encrypt(request_data)
        print(f"   ✓ Зашифровано: {len(encrypted_bytes)} байт")
        
        # 2. Кодируем в Base64 (ОБФУСКАЦИЯ)
        b64_payload = base64.b64encode(encrypted_bytes).decode('utf-8')
        print(f"   ✓ Base64 (обфускация): {len(b64_payload)} символов")
        print(f"   ✓ Данные выглядят как обычная JSON строка")
        
        # 3. Формируем заголовки
        timestamp = str(int(time.time()))
        nonce = os.urandom(8).hex()
        
        headers = {
            "Content-Type": "application/json",  # ← Обычный JSON!
            "X-API-KEY": API_KEY,
            "X-APP-ID": APP_ID,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "User-Agent": "Mozilla/5.0"
        }
        
        print(f"\n📡 Отправка на {API_URL}/ai_query/secure...")
        print(f"   Content-Type: application/json ← выглядит как обычный REST API")
        
        # 4. Отправляем
        response = requests.post(
            f"{API_URL}/ai_query/secure",
            json={"data": b64_payload},  # ← Обычный JSON payload
            headers=headers,
            timeout=10
        )
        
        print(f"\n📥 HTTP {response.status_code}")
        
        if response.status_code == 200:
            response_json = response.json()
            
            if "data" in response_json:
                # Декодируем и расшифровываем ответ
                encrypted_response_bytes = base64.b64decode(response_json["data"])
                decrypted_response = messenger.decrypt(encrypted_response_bytes)
                
                if isinstance(decrypted_response, bytes):
                    response_data = json.loads(decrypted_response.decode('utf-8'))
                else:
                    response_data = decrypted_response
                
                print("   ✓ Ответ успешно расшифрован")
                print("\n📋 Расшифрованный ответ:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                print("\n" + "="*60)
                print("✅ ОБФУСКАЦИЯ РАБОТАЕТ!")
                print("="*60)
                print("✓ Трафик замаскирован под обычный JSON")
                print("✓ Фаервол видит: Content-Type: application/json")
                print("✓ Фаервол видит: {\"data\": \"обычная_base64_строка\"}")
                print("✓ Но внутри: AES-256-GCM зашифрованные данные!")
                print("="*60)
                return True
        else:
            # Даже если AI вернул ошибку, проверим что сервер принял запрос
            error_json = response.json()
            if "error" in error_json:
                print(f"   Сервер вернул ошибку: {error_json['error']}")
                
                # Если ошибка от AI провайдера, значит обфускация сработала
                if "AI provider" in str(error_json.get('error', '')):
                    print("\n" + "="*60)
                    print("✅ ОБФУСКАЦИЯ РАБОТАЕТ!")
                    print("="*60)
                    print("✓ Сервер успешно принял и расшифровал запрос")
                    print("✓ Ошибка произошла на уровне AI провайдера")
                    print("✓ Это значит, что шифрование/обфускация работают!")
                    print("="*60)
                    return True
        
        return False
        
    except Exception as e:
        print(f"\n❌ Ошибка: { e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Тест обфускации трафика (Base64 + JSON)")
    print("="*60)
    
    success = test_obfuscation_only()
    
    if success:
        print("\n💡 Следующий шаг: настройте API ключи OpenAI/Anthropic")
        print("   в TelegramHelper/.env для полного теста с AI")
    
    sys.exit(0 if success else 1)
