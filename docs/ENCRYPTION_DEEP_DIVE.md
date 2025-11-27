# 🔐 Лекция: Глубокое погружение в шифрование и обфускацию трафика
## Архитектура безопасности BOMCategorizer ↔ TelegramHelper

В этом документе мы подробно разберем, как реализована защита данных при передаче между клиентом (BOMCategorizer) и сервером (TelegramHelper). Мы рассмотрим "матрешку" протоколов, разберем код и увидим, что видит хакер (или фаервол) при перехвате трафика.

---

## 1. Проблема: Зачем нам это нужно?

Обычный HTTPS (TLS) шифрует канал, но:
1.  **SSL Termination**: На промежуточных узлах (CDN, прокси, балансировщики) трафик расшифровывается.
2.  **DPI / WAF**: Корпоративные фаерволы могут "вскрывать" HTTPS (MITM) и блокировать подозрительные запросы.
3.  **Блокировки**: Бинарные протоколы часто блокируются по умолчанию.

**Решение**: Application-Level Encryption (ALE) + Obfuscation.
Мы шифруем данные *до* отправки в сеть и маскируем их под обычный, безобидный JSON.

---

## 2. Архитектура "Матрешка" (Russian Doll)

Наш пакет данных упакован в несколько слоев, как матрешка. Давайте посмотрим на структуру "изнутри наружу":

```mermaid
graph TD
    A[Полезная нагрузка (JSON)] -->|1. Шифрование AES-GCM| B[Бинарный пакет]
    B -->|2. Кодирование Base64| C[Строка Base64]
    C -->|3. Обертка JSON| D[JSON Request]
    D -->|4. HTTP POST| E[HTTP Пакет]
    E -->|5. TCP/IP| F[Сетевой пакет]
```

### Слой 1: Полезная нагрузка (Payload)
Это то, что мы хотим передать. Обычный JSON с промптом для AI.
```json
{
  "query": "Классифицируй компонент LM358",
  "provider": "openai",
  "model": "gpt-4"
}
```

### Слой 2: Шифрование (Encryption)
Мы используем **AES-256-GCM**. Это симметричное шифрование с аутентификацией (AEAD). Оно гарантирует не только конфиденциальность, но и целостность данных.

**Код (`encryption.py`):**
```python
# 1. Генерация уникального Nonce (12 байт) для каждого пакета
nonce = os.urandom(12)

# 2. Шифрование данных
# aesgcm.encrypt возвращает: Ciphertext + AuthTag (16 байт)
encrypted_data = self._aesgcm.encrypt(nonce, payload, None)

# 3. Сборка бинарного пакета
# [Version(1B)] + [KeyID(4B)] + [Nonce(12B)] + [EncryptedData(N)] + [Tag(16B)]
packet = version_bytes + key_id_bytes + nonce + encrypted_data
```

**Что получается:** Абсолютно нечитаемый бинарный мусор.

### Слой 3: Обфускация (Obfuscation)
Бинарные данные подозрительны для WAF. Мы превращаем их в текст с помощью **Base64** и кладем в JSON.

**Код клиента (`ai_classifier.py`):**
```python
# 1. Получаем зашифрованные байты
encrypted_bytes = messenger.encrypt(request_data)

# 2. Кодируем в Base64 (превращаем в строку)
b64_payload = base64.b64encode(encrypted_bytes).decode('utf-8')

# 3. Оборачиваем в JSON
json_body = {"data": b64_payload}
```

### Слой 4: Транспорт (HTTP)
Мы отправляем это как обычный POST запрос.

**Заголовки:**
```http
POST /ai_query/secure HTTP/1.1
Host: 138.124.19.67:8000
Content-Type: application/json
User-Agent: Mozilla/5.0 ...
```

---

## 3. Что видит сниффер (Wireshark)?

Если хакер перехватит наш пакет, он увидит следующее:

### ✅ Видимая часть (Открытым текстом)
Эти данные **НЕ** зашифрованы (на уровне HTTP, если нет HTTPS):

1.  **IP адреса и порты**: `Src: 192.168.1.5`, `Dst: 138.124.19.67:8000`
2.  **HTTP Заголовки**:
    *   `POST /ai_query/secure` (Виден endpoint)
    *   `Host: ...`
    *   `Content-Type: application/json` (Выглядит легитимно)
3.  **Тело запроса (JSON)**:
    ```json
    {
      "data": "VGVzdCBtZXNzYWdl... (длинная строка) ..."
    }
    ```

### ❌ Невидимая часть (Зашифровано)
Хакер видит строку Base64, но если он её декодирует, он получит **зашифрованные байты**. Без ключа `ENCRYPTION_KEY` (32 байта) он **не сможет**:
1.  Прочитать содержимое (`query`, `model`).
2.  Подделать содержимое (изменить промпт).
3.  Повторить запрос (Replay Attack) — благодаря проверке `Timestamp` и `Nonce` в заголовках безопасности (дополнительный слой защиты в `security.py`).

---

## 4. Реализация на сервере (`api.py`)

Сервер выполняет обратный процесс:

```python
@app.post("/ai_query/secure")
async def ai_query_secure(request: ObfuscatedRequest):
    # 1. Декодируем Base64 -> получаем бинарный пакет
    encrypted_bytes = base64.b64decode(request.data)

    # 2. Расшифровываем AES-GCM
    # SecureMessenger проверяет целостность (Tag) и расшифровывает
    decrypted_data = secure_messenger.decrypt(encrypted_bytes)
    
    # 3. Парсим исходный JSON
    query_data = json.loads(decrypted_data)
    
    # ... обработка AI ...
    
    # 4. Шифруем ответ и снова в Base64
    response_encrypted = secure_messenger.encrypt(response)
    return {"data": base64.b64encode(response_encrypted)}
```

---

## 5. Ключевые особенности безопасности

1.  **Деривация ключей (HKDF)**:
    Мы не используем `ENCRYPTION_KEY` напрямую для шифрования. Мы используем его как "Мастер-ключ" для генерации рабочего ключа через HKDF-SHA256. Это защищает мастер-ключ от криптоанализа.
    ```python
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'TelegramHelper_v1_Salt',
        info=b'AES-256-GCM-Key',
    )
    derived_key = hkdf.derive(master_secret)
    ```

2.  **Authenticated Encryption (AEAD)**:
    AES-GCM добавляет к данным "тег аутентификации". Если кто-то изменит хоть один бит в зашифрованном пакете, расшифровка выдаст ошибку `Decryption failed`. Это защищает от подделки данных.

3.  **Маскировка (Obfuscation)**:
    Для внешнего наблюдателя мы — обычное веб-приложение, отправляющее JSON. Нет бинарных заголовков, нет странных портов. Это позволяет проходить через строгие корпоративные прокси.

---

## 6. Пример использования (Python)

```python
from encryption import SecureMessenger
import base64

# 1. Инициализация
key = "ваш_32_байтный_hex_ключ..."
messenger = SecureMessenger(key)

# 2. Данные
data = {"msg": "Секретный план"}

# 3. Защита
encrypted = messenger.encrypt(data)
obfuscated = base64.b64encode(encrypted).decode()

print(f"Отправляем: {{'data': '{obfuscated}'}}")
```

---

© 2025 BOMCategorizer Security Team
