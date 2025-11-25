# 🤖 Руководство по AI-интеграции BOMCategorizer + TelegramHelper

> **Версия:** 1.2  
> **Дата:** 25.11.2025  
> **Автор:** Куреин М.Н.

---

## 📋 Содержание

1. [Быстрый старт](#-быстрый-старт)
2. [Обзор архитектуры](#-обзор-архитектуры)
3. [Протокол взаимодействия](#-протокол-взаимодействия)
4. [Защита от неправомерного использования](#-защита-от-неправомерного-использования)
5. [Используемые технологии](#-используемые-технологии)
6. [Компоненты системы](#-компоненты-системы)
7. [API провайдеры](#-api-провайдеры)
8. [Система промптов](#-система-промптов)
   - [Уточняющая подсказка (Hint)](#-уточняющая-подсказка-hint)
9. [Настройка и конфигурация](#-настройка-и-конфигурация)
10. [Безопасность API ключей](#-безопасность-api-ключей)
11. [Примеры использования](#-примеры-использования)
12. [Расширение функционала](#-расширение-функционала)
13. [Лучшие практики](#-лучшие-практики)
14. [Troubleshooting](#-troubleshooting)

---

## 🚀 Быстрый старт

### Получение API ключа (для админа бота)

1. **Откройте Telegram** и найдите вашего бота
2. **Отправьте команду:** `/api`
3. **Скопируйте** URL и ключ из ответа бота

```
🔐 API для BOMCategorizer

📍 URL: http://138.124.19.67:8000/ai_query
🔑 API Key: 754c7afb2b146882...

📋 Как использовать:
1. Откройте BOMCategorizer
2. Настройки → API Ключи
3. Вкладка "Настройки Telegram Bot API"
4. Вставьте URL и ключ выше
5. Выберите провайдер "Telegram Bot"
```

### Настройка BOMCategorizer

1. Откройте **BOMCategorizer Modern Edition**
2. Меню **Поиск PDF** → кнопка **⚙️ Настройки**
3. Перейдите на вкладку **🔑 API Ключи**
4. В разделе **Настройки Telegram Bot API**:
   - **Bot API URL:** вставьте URL из команды `/api`
   - **Bot API Key:** вставьте ключ из команды `/api`
5. Нажмите **OK**

### Проверка работы

1. Откройте **Поиск PDF**
2. Выберите вкладку **🤖 AI поиск**
3. Выберите провайдер: **Telegram Bot**
4. Введите название компонента: `TPS54302`
5. *(Опционально)* Добавьте уточняющую подсказку если AI даёт неточный ответ
6. Нажмите **Найти**

Если всё настроено правильно — вы получите информацию о компоненте!

> 💡 **Совет:** Если AI путает тип компонента, используйте поле "Уточняющая подсказка" для уточнения контекста. Подробнее: [Уточняющая подсказка](#-уточняющая-подсказка-hint)

---

## 🏗 Обзор архитектуры

### Схема взаимодействия

```
┌─────────────────────────────────────────────────────────────────┐
│                        ПОЛЬЗОВАТЕЛЬ                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BOMCategorizer (GUI)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ PDFSearchDialog │  │  AIClassifier   │  │   PromptSelect  │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                 │
│                    ┌───────────▼───────────┐                    │
│                    │    AIPDFSearcher      │                    │
│                    │   (pdf_search.py)     │                    │
│                    └───────────┬───────────┘                    │
└────────────────────────────────┼────────────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Anthropic API   │  │   OpenAI API     │  │  TelegramHelper  │
│  (claude-3.5)    │  │   (gpt-4o)       │  │   (FastAPI)      │
└──────────────────┘  └──────────────────┘  └────────┬─────────┘
                                                      │
                                           ┌──────────▼──────────┐
                                           │  Anthropic/OpenAI   │
                                           │  (через бота)       │
                                           └─────────────────────┘
```

### Принцип работы

1. **BOMCategorizer** — десктопное приложение (PySide6/Qt)
2. **TelegramHelper** — два Docker-сервиса на VPS:
   - `telegram-helper` — Telegram бот (python main.py)
   - `telegram-api` — REST API (uvicorn api:app)
3. **Три режима работы AI в BOMCategorizer:**
   - Прямой вызов Anthropic Claude API
   - Прямой вызов OpenAI GPT API
   - Через TelegramHelper API (проксирование) ← **рекомендуется**

### Docker Compose архитектура (VPS)

```yaml
services:
  telegram-helper:        # Telegram бот
    command: python main.py
    
  telegram-api:           # REST API для BOMCategorizer  
    ports: "8000:8000"
    command: uvicorn api:app --host 0.0.0.0 --port 8000
```

---

## 🔗 Протокол взаимодействия

### Детальная схема коммуникации

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           BOMCategorizer (Клиент)                          │
│                                                                            │
│  1. Пользователь вводит название компонента: "TPS54302"                    │
│  2. Выбирает тип промпта: "Краткое описание ИВП"                           │
│  3. Нажимает "Найти"                                                       │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Формирование запроса                              │  │
│  │                                                                      │  │
│  │  • Генерация промпта из шаблона                                      │  │
│  │  • Добавление timestamp (Unix time)                                  │  │
│  │  • Генерация nonce (уникальный ID запроса)                           │  │
│  │  • Вычисление HMAC-SHA256 подписи                                    │  │
│  │  • Добавление APP_ID клиента                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         HTTP POST Request                            │  │
│  │                                                                      │  │
│  │  URL: https://api.example.com/ai_query                               │  │
│  │  Headers:                                                            │  │
│  │    X-API-KEY: secret_key                                             │  │
│  │    X-APP-ID: bomcategorizer-v4                                       │  │
│  │    X-Timestamp: 1732454400                                           │  │
│  │    X-Nonce: a1b2c3d4-e5f6-7890                                       │  │
│  │    X-Signature: hmac_sha256(payload + timestamp + nonce)             │  │
│  │  Body (JSON):                                                        │  │
│  │    { "prompt": "...", "provider": "anthropic", "max_tokens": 2048 }  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │
                          HTTPS (TLS 1.3)
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         TelegramHelper (Сервер)                            │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Проверка безопасности                           │  │
│  │                                                                      │  │
│  │  1. ✓ Проверка X-API-KEY (совпадает с API_SECRET_KEY?)               │  │
│  │  2. ✓ Проверка X-APP-ID (в whitelist разрешённых приложений?)        │  │
│  │  3. ✓ Проверка X-Timestamp (не старше 5 минут?)                      │  │
│  │  4. ✓ Проверка X-Nonce (не использовался ранее?)                     │  │
│  │  5. ✓ Проверка X-Signature (HMAC валидна?)                           │  │
│  │  6. ✓ Проверка IP (в whitelist? - опционально)                       │  │
│  │  7. ✓ Rate limiting (не превышен лимит запросов?)                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                        Все проверки пройдены?                              │
│                           /              \                                  │
│                         ДА               НЕТ                                │
│                          │                │                                 │
│                          ▼                ▼                                 │
│  ┌────────────────────────────┐  ┌────────────────────────────────────┐    │
│  │    Выполнение запроса      │  │      Отклонение запроса            │    │
│  │                            │  │                                    │    │
│  │  • Определение провайдера  │  │  HTTP 401/403/429                  │    │
│  │  • Вызов Anthropic/OpenAI  │  │  { "error": "Unauthorized" }       │    │
│  │  • Форматирование ответа   │  │                                    │    │
│  └────────────────────────────┘  └────────────────────────────────────┘    │
│                    │                                                        │
│                    ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         HTTP Response                                │  │
│  │                                                                      │  │
│  │  Status: 200 OK                                                      │  │
│  │  Body (JSON):                                                        │  │
│  │    {                                                                 │  │
│  │      "response": "TPS54302 - это синхронный DC-DC...",              │  │
│  │      "provider": "anthropic",                                        │  │
│  │      "status": "success",                                            │  │
│  │      "request_id": "req_abc123"                                      │  │
│  │    }                                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### Жизненный цикл запроса

```
Время →

[0ms]     Пользователь нажимает "Найти"
          │
[5ms]     BOMCategorizer формирует промпт
          │
[10ms]    Генерация заголовков безопасности (timestamp, nonce, signature)
          │
[15ms]    Отправка HTTP POST запроса
          │
[50ms]    TelegramHelper получает запрос
          │
[55ms]    Проверка всех параметров безопасности
          │
[60ms]    Запрос к Anthropic/OpenAI API
          │
[2000ms]  Получение ответа от AI
          │
[2010ms]  Форматирование и отправка ответа
          │
[2050ms]  BOMCategorizer получает ответ
          │
[2100ms]  Отображение результата пользователю
```

### Форматы данных

#### Запрос (Request)

```json
{
  "prompt": "Составь краткое описание ИВП TPS54302...",
  "provider": "anthropic",
  "max_tokens": 2048,
  "template_category": "ivp_short",
  "input_text": "TPS54302"
}
```

#### Ответ (Response)

```json
{
  "response": "TPS54302 - синхронный понижающий DC-DC преобразователь...",
  "provider": "anthropic",
  "status": "success",
  "template_used": "ivp_short",
  "tokens_used": {
    "input": 245,
    "output": 512
  },
  "request_id": "req_1732454400_abc123",
  "processing_time_ms": 1950
}
```

---

## 🛡 Защита от неправомерного использования

### Многоуровневая система безопасности

```
┌─────────────────────────────────────────────────────────────────────┐
│                    УРОВНИ ЗАЩИТЫ                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  УРОВЕНЬ 1: Транспортный                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • HTTPS (TLS 1.3) - шифрование канала                      │   │
│  │  • Certificate pinning (опционально)                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                       │
│  УРОВЕНЬ 2: Аутентификация                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • X-API-KEY - секретный ключ API                           │   │
│  │  • X-APP-ID - идентификатор приложения                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                       │
│  УРОВЕНЬ 3: Целостность                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • HMAC-SHA256 подпись запроса                              │   │
│  │  • Timestamp (защита от replay attacks)                     │   │
│  │  • Nonce (уникальность запроса)                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                       │
│  УРОВЕНЬ 4: Авторизация                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Whitelist разрешённых APP_ID                             │   │
│  │  • Whitelist IP адресов (опционально)                       │   │
│  │  • Проверка прав доступа к endpoint                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                       │
│  УРОВЕНЬ 5: Rate Limiting                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Ограничение запросов в минуту (RPM)                      │   │
│  │  • Ограничение запросов в день (RPD)                        │   │
│  │  • Sliding window algorithm                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                       │
│  УРОВЕНЬ 6: Мониторинг                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Логирование всех запросов                                │   │
│  │  • Алерты при подозрительной активности                     │   │
│  │  • Автоматическая блокировка при атаках                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Реализация HMAC подписи

#### Алгоритм формирования подписи (клиент)

```python
import hmac
import hashlib
import time
import uuid
import json

def create_signed_request(payload: dict, api_key: str, secret: str) -> dict:
    """
    Создание подписанного запроса для безопасной передачи
    
    Args:
        payload: Тело запроса (prompt, provider, etc.)
        api_key: API ключ для аутентификации
        secret: Секретный ключ для HMAC подписи
        
    Returns:
        Словарь с заголовками безопасности
    """
    # 1. Генерируем timestamp (Unix time в секундах)
    timestamp = str(int(time.time()))
    
    # 2. Генерируем уникальный nonce (защита от replay attacks)
    nonce = str(uuid.uuid4())
    
    # 3. Формируем строку для подписи
    # Включаем: timestamp + nonce + отсортированный JSON payload
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    sign_string = f"{timestamp}:{nonce}:{payload_json}"
    
    # 4. Вычисляем HMAC-SHA256
    signature = hmac.new(
        secret.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # 5. Возвращаем заголовки
    return {
        "X-API-KEY": api_key,
        "X-APP-ID": "bomcategorizer-v4",
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature
    }
```

#### Алгоритм проверки подписи (сервер)

```python
import hmac
import hashlib
import time
from typing import Optional
from fastapi import HTTPException, Request

# Хранилище использованных nonce (в production - Redis)
used_nonces = set()

# Whitelist разрешённых приложений
ALLOWED_APPS = {
    "bomcategorizer-v4": {
        "name": "BOM Categorizer Modern Edition",
        "allowed_endpoints": ["/ai_query", "/prompt_templates"],
        "rate_limit": 60  # запросов в минуту
    },
    "bomcategorizer-v3": {
        "name": "BOM Categorizer Standard Edition", 
        "allowed_endpoints": ["/ai_query"],
        "rate_limit": 30
    }
}

def verify_request_signature(
    request: Request,
    payload: dict,
    api_key: str,
    app_id: str,
    timestamp: str,
    nonce: str,
    signature: str,
    secret: str
) -> bool:
    """
    Проверка подписи и валидности запроса
    
    Проверяет:
    1. API ключ
    2. APP_ID в whitelist
    3. Timestamp не устарел (< 5 минут)
    4. Nonce не использовался
    5. HMAC подпись валидна
    """
    
    # 1. Проверка API ключа
    expected_key = os.getenv("API_SECRET_KEY")
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # 2. Проверка APP_ID
    if app_id not in ALLOWED_APPS:
        raise HTTPException(
            status_code=403, 
            detail=f"Application '{app_id}' is not authorized"
        )
    
    # 3. Проверка timestamp (не старше 5 минут)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - request_time) > 300:  # 5 минут
            raise HTTPException(
                status_code=401, 
                detail="Request timestamp expired"
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp")
    
    # 4. Проверка nonce (защита от replay attacks)
    if nonce in used_nonces:
        raise HTTPException(
            status_code=401, 
            detail="Nonce already used (possible replay attack)"
        )
    used_nonces.add(nonce)
    
    # Очистка старых nonce (в production - TTL в Redis)
    # Здесь упрощённая версия
    
    # 5. Проверка HMAC подписи
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    sign_string = f"{timestamp}:{nonce}:{payload_json}"
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=401, 
            detail="Invalid signature"
        )
    
    return True
```

### Конфигурация безопасности

#### TelegramHelper `.env`

```bash
# === ОСНОВНЫЕ КЛЮЧИ ===
API_SECRET_KEY=your_very_long_random_secret_key_here_64_chars_minimum
HMAC_SECRET=another_random_secret_for_hmac_signing_also_64_chars

# === AI ПРОВАЙДЕРЫ ===
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...

# === БЕЗОПАСНОСТЬ ===
# Whitelist разрешённых приложений (через запятую)
ALLOWED_APP_IDS=bomcategorizer-v4,bomcategorizer-v3

# Whitelist IP адресов (опционально, через запятую)
# Оставьте пустым для разрешения всех IP
ALLOWED_IPS=192.168.1.100,10.0.0.50

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_DAY=1000

# Время жизни timestamp (секунды)
TIMESTAMP_TOLERANCE=300

# === ЛОГИРОВАНИЕ ===
LOG_LEVEL=INFO
LOG_FILE=/var/log/telegramhelper/api.log
```

#### BOMCategorizer `config_qt.json`

```json
{
  "api_keys": {
    "anthropic": "",
    "openai": "",
    "ollama_url": "http://localhost:11434",
    "telegram_url": "http://ВАШ_СЕРВЕР_IP:8000/ai_query",
    "telegram_key": "ключ_из_команды_/api",
    "telegram_hmac_secret": ""
  },
  "telegram_security": {
    "app_id": "bomcategorizer-v4",
    "enable_signature": true,
    "verify_ssl": true
  }
}
```

> 💡 **Как получить ключ:** отправьте команду `/api` боту в Telegram (только для админа)

### Защита от типичных атак

#### 1. Replay Attack (повторное использование запроса)

**Защита:** Nonce + Timestamp

```python
# Атакующий перехватывает запрос и пытается отправить повторно
# Сервер проверяет:
# 1. Timestamp устарел? (> 5 минут) → Отклонить
# 2. Nonce уже использовался? → Отклонить
```

#### 2. Man-in-the-Middle (перехват и модификация)

**Защита:** HTTPS + HMAC подпись

```python
# Атакующий пытается изменить payload
# Сервер проверяет:
# 1. HMAC подпись не совпадает → Отклонить
```

#### 3. Brute Force (подбор ключей)

**Защита:** Rate limiting + длинные ключи

```python
# Атакующий пытается подобрать API ключ
# Сервер:
# 1. Ограничивает количество неудачных попыток
# 2. Блокирует IP после N неудачных попыток
# 3. Использует ключи длиной 64+ символов
```

#### 4. Unauthorized Access (несанкционированный доступ)

**Защита:** Whitelist APP_ID + проверка прав

```python
# Неизвестное приложение пытается получить доступ
# Сервер:
# 1. APP_ID не в whitelist → 403 Forbidden
# 2. Endpoint не разрешён для этого APP_ID → 403 Forbidden
```

### Генерация безопасных ключей

```bash
# Генерация API_SECRET_KEY (64 символа)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Генерация HMAC_SECRET (64 символа)
openssl rand -hex 32

# Пример вывода:
# a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678
```

### Рекомендации по развёртыванию

#### Production окружение

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                                   │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   CloudFlare    │───▶│     Nginx       │───▶│  TelegramHelper │ │
│  │   (WAF + DDoS)  │    │  (Reverse Proxy)│    │    (Uvicorn)    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                        │            │
│                                                        ▼            │
│                                               ┌─────────────────┐   │
│                                               │      Redis      │   │
│                                               │  (nonce store,  │   │
│                                               │   rate limits)  │   │
│                                               └─────────────────┘   │
│                                                                     │
│  Рекомендации:                                                      │
│  • SSL сертификат от Let's Encrypt                                  │
│  • Firewall (ufw/iptables)                                          │
│  • fail2ban для защиты от брутфорса                                 │
│  • Регулярное обновление зависимостей                               │
│  • Мониторинг (Prometheus + Grafana)                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Docker Compose (безопасная конфигурация)

```yaml
version: '3.8'

services:
  telegramhelper:
    build: .
    ports:
      - "127.0.0.1:8000:8000"  # Только localhost!
    environment:
      - API_SECRET_KEY=${API_SECRET_KEY}
      - HMAC_SECRET=${HMAC_SECRET}
    secrets:
      - anthropic_key
      - openai_key
    networks:
      - internal
    deploy:
      resources:
        limits:
          memory: 512M
    security_opt:
      - no-new-privileges:true
    read_only: true
    
  redis:
    image: redis:alpine
    networks:
      - internal
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    networks:
      - internal
      - external

networks:
  internal:
    internal: true
  external:

secrets:
  anthropic_key:
    file: ./secrets/anthropic.txt
  openai_key:
    file: ./secrets/openai.txt

volumes:
  redis_data:
```

---

## 🔧 Используемые технологии

### BOMCategorizer (Desktop Client)

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Python** | 3.13+ | Основной язык |
| **PySide6** | 6.6+ | GUI фреймворк (Qt for Python) |
| **anthropic** | 0.34+ | Официальный SDK Anthropic |
| **openai** | 1.0+ | Официальный SDK OpenAI |
| **requests** | 2.31+ | HTTP-клиент для TelegramHelper |

### TelegramHelper (API Server)

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Python** | 3.11+ | Основной язык |
| **FastAPI** | 0.104+ | Async веб-фреймворк |
| **Uvicorn** | 0.24+ | ASGI сервер |
| **Pydantic** | 2.5+ | Валидация данных |
| **python-telegram-bot** | 20.6+ | Telegram Bot API |
| **anthropic** | 0.34+ | Claude API |
| **openai** | 1.0+ | GPT API |

### Протоколы и форматы

| Протокол | Использование |
|----------|---------------|
| **HTTP/HTTPS** | REST API взаимодействие |
| **JSON** | Формат данных запросов/ответов |
| **WebSocket** | Telegram Bot long-polling |

---

## 🧩 Компоненты системы

### BOMCategorizer

#### 1. `pdf_search_dialogs.py` — GUI диалоги

```python
class PDFSearchDialog(QDialog):
    """Главный диалог поиска PDF и AI-запросов"""
    
    def _create_ai_tab(self):
        """Создание вкладки AI поиска с выбором промптов"""
        
    def _get_prompt_template(self, component_name: str) -> str:
        """Генерация промпта на основе выбранного типа"""
        
    def run_ai_search(self, query: str):
        """Запуск AI-поиска в фоновом потоке"""
```

#### 2. `pdf_search.py` — Логика AI-поиска

```python
class AIPDFSearcher:
    """Класс для AI-поиска информации о компонентах"""
    
    def search(self, component_name: str) -> Dict:
        """Стандартный поиск с дефолтным промптом"""
        
    def search_with_prompt(self, component_name: str, custom_prompt: str) -> Dict:
        """Поиск с кастомным промптом"""
        
    def _search_anthropic(self, ...) -> Dict:
        """Прямой вызов Anthropic API"""
        
    def _search_openai(self, ...) -> Dict:
        """Прямой вызов OpenAI API"""
        
    def _search_telegram_bot(self, ...) -> Dict:
        """Вызов через TelegramHelper API"""
```

#### 3. `AISearchWorker` — Фоновый поток

```python
class AISearchWorker(QThread):
    """Worker для асинхронного AI-поиска"""
    finished = Signal(dict)
    
    def run(self):
        """Выполнение запроса в отдельном потоке"""
```

### TelegramHelper

#### 1. `api.py` — REST API endpoints

```python
@app.post("/ai_query")
async def ai_query(request: AIQueryRequest) -> AIQueryResponse:
    """Основной endpoint для AI-запросов"""

@app.get("/prompt_templates")
async def get_templates() -> PromptTemplatesResponse:
    """Получение списка шаблонов промптов"""

@app.get("/prompt_categories")
async def get_categories():
    """Получение категорий шаблонов"""
```

#### 2. `utils.py` — AI утилиты

```python
def get_anthropic_completion(prompt: str, max_tokens: int) -> str:
    """Получение ответа от Claude"""

def get_openai_completion(prompt: str, max_tokens: int) -> str:
    """Получение ответа от GPT"""

def render_prompt(category: str, input_text: str) -> str:
    """Рендеринг промпта из шаблона"""
```

---

## 🌐 API провайдеры

### Anthropic Claude

**Модель:** `claude-3-5-sonnet-20241022`

**Особенности:**
- Отличное понимание технической документации
- Хорошая работа с русским языком
- Высокая точность при анализе электронных компонентов
- Поддержка длинного контекста (200K токенов)

**Пример вызова:**
```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{"role": "user", "content": prompt}]
)
response = message.content[0].text
```

**Цены (на ноябрь 2025):**
- Input: $3 / 1M токенов
- Output: $15 / 1M токенов

### OpenAI GPT-4o

**Модель:** `gpt-4o`

**Особенности:**
- Multimodal (текст + изображения)
- Быстрый inference
- Хорошая структуризация данных
- JSON mode для структурированных ответов

**Пример вызова:**
```python
import openai

client = openai.OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Ты эксперт по электронике."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=4096
)
text = response.choices[0].message.content
```

**Цены (на ноябрь 2025):**
- Input: $2.50 / 1M токенов
- Output: $10 / 1M токенов

### TelegramHelper API (прокси)

**Endpoint:** `POST /ai_query`

**Преимущества:**
- Централизованное управление ключами
- Логирование всех запросов
- Fallback между провайдерами
- Кэширование ответов (опционально)

**Пример запроса:**
```python
import requests

response = requests.post(
    "http://localhost:8000/ai_query",
    json={
        "prompt": "Информация о компоненте LM2596",
        "provider": "anthropic",
        "max_tokens": 2048
    },
    headers={"X-API-KEY": "secret_key"}
)
data = response.json()
```

---

## 📝 Система промптов

### Встроенные промпты BOMCategorizer

#### 1. Стандартный промпт (информация о компоненте)

```
Найди информацию об электронном компоненте: {component}

Предоставь:
1. Полное название и производитель
2. Тип компонента
3. Основные характеристики
4. Описание назначения
5. Примеры использования
6. Ссылка на PDF документацию

Формат: JSON
```

#### 2. Краткое описание ИВП

```
Составь краткое техническое описание ИВП: {component}

Требуется:
1. Полное название и производитель
2. Тип (DC-DC, LDO, POL и т.д.)
3. Технические характеристики (Vin, Vout, Iout, КПД, частота, корпус)
4. Ключевые преимущества
5. Обоснование невозможности замены на отечественные аналоги

Формат: текст 150-200 слов
```

#### 3. Развёрнутое описание (обзор даташита)

```
Подготовь развёрнутое описание ИВП: {component}

Структура:
1. ОБЩАЯ ИНФОРМАЦИЯ
2. ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ
3. КОНСТРУКТИВНЫЕ ОСОБЕННОСТИ
4. ПРЕИМУЩЕСТВА И ОСОБЕННОСТИ
5. РЕКОМЕНДАЦИИ ПО ПРИМЕНЕНИЮ

Объём: 200-400 слов
```

#### 4. Поиск аналогов

```
Найди все существующие аналоги для: {component}

Категории:
1. ПРЯМЫЕ АНАЛОГИ (pin-to-pin)
2. ФУНКЦИОНАЛЬНЫЕ АНАЛОГИ
3. БЮДЖЕТНЫЕ АЛЬТЕРНАТИВЫ
4. ПРЕМИУМ АЛЬТЕРНАТИВЫ

Для каждого:
- Название и производитель
- Ссылка на документацию
- Степень совместимости
```

#### 5. Сравнительный анализ

```
Проведи сравнительный анализ: {component}

Требуется:
1. Идентификация компонента
2. 3-5 основных конкурентов
3. Сравнительная таблица параметров
4. Выводы и рекомендации
```

### Шаблоны TelegramHelper (`prompt_templates.json`)

```json
{
  "science": {
    "title": "Научный запрос",
    "template": "Ты научный ассистент. Сформулируй ответ на: {input}"
  },
  "programming": {
    "title": "Программирование",
    "template": "Ты опытный разработчик. Объясни: {input}"
  },
  "debunk": {
    "title": "Разоблачение фейков",
    "template": "Проверь утверждение: {input}"
  }
}
```

### 💡 Уточняющая подсказка (Hint)

Новая функция для уменьшения ошибок AI при классификации компонентов.

#### Проблема

AI иногда неправильно определяет тип компонента:
- Путает делители частоты с DC-DC преобразователями
- Неверно определяет производителя
- Даёт устаревшую информацию

#### Решение

В интерфейсе AI-поиска добавлено поле **"💡 Уточняющая подсказка"** — дополнительный контекст, который помогает AI дать точный ответ.

```
┌─ AI поиск ────────────────────────────────────────────────────┐
│  Компонент: [HMC435AMS8GE                              ]      │
│                                                               │
│  📝 Тип запроса: [Развёрнутое описание ИВП ▼]                │
│                                                               │
│  💡 Уточняющая подсказка (опционально):                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ This is a frequency divider, NOT a DC-DC converter     │ │
│  │ Manufactured by Analog Devices (formerly Hittite)      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  [🔎 Найти]                                                  │
└───────────────────────────────────────────────────────────────┘
```

#### Как работает

Подсказка добавляется в конец промпта перед отправкой к AI:

```python
# Базовый промпт
prompt = "Подготовь описание компонента HMC435AMS8GE..."

# + Уточняющая подсказка
prompt += """

ВАЖНАЯ ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ от пользователя:
This is a frequency divider, NOT a DC-DC converter
Manufactured by Analog Devices (formerly Hittite)

ОБЯЗАТЕЛЬНО: Ответ должен быть ТОЛЬКО на русском языке.
"""
```

#### Примеры подсказок

| Компонент | Проблема | Уточняющая подсказка |
|-----------|----------|---------------------|
| HMC435AMS8GE | AI думает что это DC-DC | `This is a frequency divider for RF applications, NOT a power converter` |
| TPS54302 | Устаревшие данные | `Check latest datasheet from ti.com, product is active` |
| LM358N | Путает с LM358P | `LM358N is DIP-8 package, not SOIC` |
| STM32F103 | Общее описание | `Focus on Blue Pill board usage in hobbyist projects` |

#### Особенности

| Свойство | Описание |
|----------|----------|
| **Язык подсказки** | Любой (английский рекомендуется для точности) |
| **Язык ответа** | Всегда русский |
| **Обязательность** | Опционально |
| **Длина** | До 500 символов рекомендуется |

#### Когда использовать

✅ **Используйте подсказку когда:**
- AI даёт неточную информацию о компоненте
- Компонент имеет неочевидный тип (делитель частоты, RF компонент)
- Нужно уточнить производителя или серию
- Требуется фокус на конкретном применении

❌ **Не нужна подсказка когда:**
- Стандартные популярные компоненты (LM7805, NE555)
- AI уже даёт правильный ответ
- Используете промпт "Свой текст" с полным контекстом

---

## ⚙️ Настройка и конфигурация

### BOMCategorizer (`config_qt.json`)

```json
{
  "api_keys": {
    "anthropic": "sk-ant-api03-...",
    "openai": "sk-proj-...",
    "ollama_url": "http://localhost:11434",
    "telegram_url": "http://localhost:8000/ai_query",
    "telegram_key": "your_secret_key"
  },
  "ui": {
    "ai_classifier_enabled": true,
    "ai_auto_classify": false
  }
}
```

### TelegramHelper (`.env`)

```bash
# Telegram Bot
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# AI Providers
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
DEFAULT_AI_PROVIDER=anthropic

# API Security (генерация: python3 -c "import secrets; print(secrets.token_hex(32))")
API_SECRET_KEY=your_secure_random_key_here_64_chars

# API URL для команды /api (отображается админу)
API_URL=http://ВАШ_СЕРВЕР_IP:8000/ai_query

# Optional
CLAUDE_MODEL=claude-3-5-sonnet-20241022
GPT_MODEL=gpt-4o
```

### Настройка через GUI

1. Откройте **BOMCategorizer Modern Edition**
2. Откройте **Поиск PDF** (кнопка 🔍 или меню)
3. Нажмите кнопку **⚙️ Настройки**
4. Перейдите на вкладку **🔑 API Ключи**
5. В разделе **Настройки Telegram Bot API**:
   - **Bot API URL:** `http://ВАШ_СЕРВЕР:8000/ai_query`
   - **Bot API Key:** ключ из команды `/api` в Telegram боте
6. Нажмите **OK**

> 💡 **Подсказка:** Для облачных AI ключи Anthropic/OpenAI не нужны — используйте провайдер "Telegram Bot"

---

## 🔐 Безопасность API ключей

### ⚠️ КРИТИЧЕСКИ ВАЖНО

> **НИКОГДА** не коммитьте API ключи в Git!  
> **НИКОГДА** не отправляйте ключи в чатах!  
> **НИКОГДА** не храните ключи в открытом виде в коде!

### Рекомендации по безопасности

#### 1. Используйте переменные окружения

```bash
# ~/.zshrc или ~/.bashrc
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-proj-..."
```

#### 2. Используйте `.env` файлы (локально)

```bash
# .env (добавьте в .gitignore!)
ANTHROPIC_API_KEY=sk-ant-...
```

#### 3. Используйте менеджеры секретов

| Сервис | Описание |
|--------|----------|
| **macOS Keychain** | Встроенное хранилище macOS |
| **1Password** | Популярный менеджер паролей |
| **Bitwarden** | Open-source альтернатива |
| **AWS Secrets Manager** | Для production |
| **HashiCorp Vault** | Enterprise-решение |

#### 4. Создайте `.gitignore`

```gitignore
# API Keys and Secrets
.env
.env.local
*.env
config_qt.json
secrets/

# Never commit these
*_key.txt
*_secret.txt
```

#### 5. Ротация ключей

- Меняйте ключи каждые **90 дней**
- Сразу отзывайте скомпрометированные ключи
- Используйте разные ключи для dev/prod

#### 6. Ограничение доступа

**Anthropic Console:**
- Установите лимиты расходов
- Включите уведомления о превышении

**OpenAI Dashboard:**
- Создайте отдельные API ключи для проектов
- Установите monthly limits

### Как восстановить утерянный ключ

1. **Anthropic:** https://console.anthropic.com/
   - Settings → API Keys → Create New Key
   
2. **OpenAI:** https://platform.openai.com/api-keys
   - Create new secret key

> ⚠️ Старый ключ восстановить **НЕВОЗМОЖНО**. Только создать новый.

### Проверка утечки ключей

```bash
# Поиск ключей в истории Git
git log -p | grep -E "(sk-ant|sk-proj|api.key)"

# Если нашли - перевыпустите ключ НЕМЕДЛЕННО!
```

---

## 💡 Примеры использования

### Пример 1: Поиск информации о DC-DC преобразователе

```
Компонент: TPS54302DDCR
Промпт: Краткое описание ИВП

Результат:
┌─────────────────────────────────────────────────────────┐
│ TPS54302DDCR - Texas Instruments                        │
│ Тип: Синхронный понижающий DC-DC преобразователь       │
│                                                         │
│ Характеристики:                                         │
│ • Vin: 4.5V - 28V                                      │
│ • Vout: 0.6V - 7V (программируемый)                    │
│ • Iout: до 3A                                          │
│ • КПД: до 95%                                          │
│ • Частота: 500kHz (фиксированная)                      │
│ • Корпус: SOT-23-6 (DDCR)                              │
│                                                         │
│ Преимущества:                                           │
│ • Высокий КПД при малых токах нагрузки                 │
│ • Компактный корпус с низким тепловым сопротивлением   │
│ • Внутренняя компенсация                               │
│                                                         │
│ Невозможность замены на отечественные аналоги:         │
│ Российские производители не выпускают DC-DC            │
│ преобразователи с аналогичными параметрами в           │
│ компактном корпусе SOT-23. Ближайшие отечественные    │
│ аналоги (1180ЕН) имеют значительно больший корпус     │
│ и не обеспечивают требуемый КПД.                       │
└─────────────────────────────────────────────────────────┘
```

### Пример 2: Поиск аналогов

```
Компонент: LM2596S-5.0
Промпт: Поиск аналогов

Результат:
┌─────────────────────────────────────────────────────────┐
│ ПРЯМЫЕ АНАЛОГИ (pin-to-pin):                            │
│ • XL2596-5.0 (XLSEMI) - 100% совместим                 │
│   https://www.xlsemi.com/datasheet/xl2596.pdf           │
│ • MP2596 (Monolithic Power) - 100% совместим           │
│   https://www.monolithicpower.com/mp2596               │
│                                                         │
│ ФУНКЦИОНАЛЬНЫЕ АНАЛОГИ:                                 │
│ • TPS54540 (Texas Instruments) - улучшенный КПД        │
│ • LMR33630 (Texas Instruments) - более современный     │
│ • AP63203 (Diodes Inc) - компактнее, дешевле           │
│                                                         │
│ БЮДЖЕТНЫЕ АЛЬТЕРНАТИВЫ:                                 │
│ • MC34063 - классика, но низкий КПД                    │
│ • XL4005 - дешевле, но требует радиатор                │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Расширение функционала

### Что можно добавить в будущем

#### 1. Кэширование ответов

```python
# Redis кэш для повторяющихся запросов
import redis

cache = redis.Redis()

def get_cached_or_fetch(component: str, prompt_type: str):
    cache_key = f"ai:{component}:{prompt_type}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    result = fetch_from_ai(component, prompt_type)
    cache.setex(cache_key, 86400, json.dumps(result))  # 24h TTL
    return result
```

#### 2. Batch-обработка компонентов

```python
async def batch_search(components: List[str]) -> List[Dict]:
    """Параллельный поиск нескольких компонентов"""
    tasks = [search_component(c) for c in components]
    return await asyncio.gather(*tasks)
```

#### 3. OCR распознавание из изображений

```python
# Использование GPT-4 Vision для распознавания маркировки
def recognize_component_from_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Определи маркировку компонента"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
        }]
    )
```

#### 4. RAG (Retrieval Augmented Generation)

```python
# Использование собственной базы даташитов
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Индексация PDF даташитов
vectorstore = Chroma.from_documents(
    documents=pdf_documents,
    embedding=OpenAIEmbeddings()
)

# Поиск релевантных документов
relevant_docs = vectorstore.similarity_search(query, k=3)
```

#### 5. Голосовой ввод

```python
# Whisper API для распознавания речи
def transcribe_audio(audio_file: str) -> str:
    with open(audio_file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcript.text
```

#### 6. Экспорт в различные форматы

- **PDF** — красивый отчёт с характеристиками
- **Excel** — таблица для закупок
- **JSON** — для интеграции с ERP
- **Markdown** — для документации

#### 7. Интеграция с поставщиками

```python
# API DigiKey, Mouser, LCSC
async def check_availability(component: str) -> Dict:
    results = await asyncio.gather(
        digikey_api.search(component),
        mouser_api.search(component),
        lcsc_api.search(component)
    )
    return {
        "digikey": results[0],
        "mouser": results[1],
        "lcsc": results[2]
    }
```

#### 8. Machine Learning для классификации

```python
# Fine-tuned модель для классификации компонентов
from transformers import pipeline

classifier = pipeline("text-classification", 
                     model="electronics-component-classifier")

def classify_component(name: str) -> str:
    result = classifier(name)
    return result[0]["label"]  # "resistor", "capacitor", "ic", etc.
```

---

## ✨ Лучшие практики

### Промпт-инжиниринг

1. **Будьте конкретны:**
   ```
   ❌ "Расскажи про LM358"
   ✅ "Предоставь технические характеристики операционного 
       усилителя LM358 в формате таблицы"
   ```

2. **Указывайте формат вывода:**
   ```
   ✅ "Формат ответа: JSON с полями name, manufacturer, specs"
   ```

3. **Используйте few-shot примеры:**
   ```
   Пример:
   Вход: "1N4148"
   Выход: {"type": "diode", "category": "semiconductors"}
   
   Теперь классифицируй: "LM7805"
   ```

### Обработка ошибок

```python
def safe_ai_request(prompt: str, max_retries: int = 3) -> Dict:
    for attempt in range(max_retries):
        try:
            return make_request(prompt)
        except RateLimitError:
            time.sleep(2 ** attempt)  # Exponential backoff
        except APIError as e:
            logger.error(f"API Error: {e}")
            if attempt == max_retries - 1:
                return {"error": str(e)}
    return {"error": "Max retries exceeded"}
```

### Оптимизация токенов

```python
# Сжатие промпта для экономии токенов
def optimize_prompt(prompt: str) -> str:
    # Убираем лишние пробелы
    prompt = " ".join(prompt.split())
    # Сокращаем повторяющиеся инструкции
    prompt = prompt.replace("Пожалуйста, ", "")
    return prompt
```

### Мониторинг использования

```python
# Логирование запросов и расходов
import logging

logger = logging.getLogger("ai_usage")

def log_request(provider: str, tokens_in: int, tokens_out: int):
    cost = calculate_cost(provider, tokens_in, tokens_out)
    logger.info(f"Provider: {provider}, In: {tokens_in}, Out: {tokens_out}, Cost: ${cost:.4f}")
```

---

## 🔧 Troubleshooting

### Частые проблемы

#### 1. "API ключ не найден"

**Причина:** Ключ не сохранён в `config_qt.json`

**Решение:**
```bash
# Проверьте наличие ключа
cat config_qt.json | grep -A5 "api_keys"
```

#### 2. "401 Unauthorized"

**Причина:** Неверный API ключ

**Решение:**
- Проверьте правильность ключа
- Убедитесь, что ключ активен в консоли провайдера
- Проверьте наличие пробелов в начале/конце

#### 3. "429 Too Many Requests"

**Причина:** Превышен лимит запросов

**Решение:**
```python
# Добавьте задержку между запросами
import time
time.sleep(1)  # 1 запрос в секунду
```

#### 4. "Connection refused" (TelegramHelper)

**Причина:** API сервер не запущен на VPS

**Проверка:**
```bash
# На сервере
ssh root@ВАШ_СЕРВЕР -p 22542
docker ps | grep telegram
# Должны быть ОБА контейнера: telegram-helper и telegram-api

# Проверка health endpoint
curl http://localhost:8000/health
```

**Решение:**
```bash
cd /opt/TelegramHelper
docker compose up -d
docker logs telegram-api --tail=20
```

#### 5. "Команда /api не работает"

**Причина:** Вы не админ бота или бот не обновлён

**Решение:**
1. Проверьте, что ваш Telegram ID в списке админов
2. Обновите код на сервере:
```bash
rsync -avz -e 'ssh -p 22542' ./TelegramHelper/ root@СЕРВЕР:/opt/TelegramHelper/
ssh root@СЕРВЕР -p 22542 "cd /opt/TelegramHelper && docker compose build --no-cache && docker compose up -d"
```

#### 5. Пустой ответ от AI

**Причина:** Слишком короткий `max_tokens`

**Решение:** Увеличьте `max_tokens` до 2048-4096

### Логи для отладки

```python
# Включите подробное логирование
import logging
logging.basicConfig(level=logging.DEBUG)

# Логирование HTTP запросов
import httpx
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)
```

---

## 📚 Дополнительные ресурсы

### Документация провайдеров

- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Полезные инструменты

- [Promptfoo](https://github.com/promptfoo/promptfoo) — тестирование промптов
- [LangSmith](https://smith.langchain.com/) — мониторинг LLM
- [Helicone](https://helicone.ai/) — аналитика API вызовов

### Сообщество

- [r/MachineLearning](https://reddit.com/r/MachineLearning)
- [Hugging Face Discord](https://discord.gg/huggingface)
- [AI Engineering Telegram](https://t.me/ai_engineering)

---

## 📄 Лицензия

Данная документация и связанный код распространяются под лицензией MIT.

---

*Последнее обновление: 25.11.2025 v1.2 — добавлена уточняющая подсказка*

