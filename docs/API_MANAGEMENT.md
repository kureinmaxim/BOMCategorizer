# 🔐 Управление API для интеграции с TelegramHelper

> **Версия:** 1.0  
> **Дата:** 25.11.2025  
> **Автор:** Куреин М.Н.

---

## 📋 Содержание

1. [Обзор](#-обзор)
2. [Быстрый старт](#-быстрый-старт)
3. [Команды управления](#-команды-управления)
4. [Синхронизация ключа](#-синхронизация-ключа)
5. [Тестирование API](#-тестирование-api)
6. [Конфигурация](#-конфигурация)
7. [Устранение проблем](#-устранение-проблем)

---

## 🎯 Обзор

BOMCategorizer интегрируется с TelegramHelper для AI-поиска информации о компонентах. Для работы требуется:

| Параметр | Описание |
|----------|----------|
| `telegram_url` | URL API сервера |
| `telegram_key` | Секретный ключ для аутентификации |

### Архитектура

```
┌─────────────────────┐                    ┌─────────────────────┐
│   BOMCategorizer    │    HTTP Request    │   TelegramHelper    │
│   (Desktop App)     │ ────────────────→  │   (VPS Server)      │
│                     │                    │                     │
│  config_qt.json:    │    AI Response     │  .env:              │
│  - telegram_url     │ ←────────────────  │  - API_SECRET_KEY   │
│  - telegram_key     │                    │  - API_URL          │
└─────────────────────┘                    └─────────────────────┘
```

---

## 🚀 Быстрый старт

### 1. Получить ключ с сервера и синхронизировать

```bash
cd /path/to/BOMCategorizer
source venv/bin/activate  # macOS/Linux
# или: .\.venv\Scripts\activate  # Windows

python tools/sync_telegram_api.py --fetch
```

### 2. Проверить что всё работает

```bash
python tools/sync_telegram_api.py --test
```

### 3. Готово!

Перезапустите BOMCategorizer — AI поиск должен работать.

---

## 🛠 Команды управления

### sync_telegram_api.py — Синхронизация API ключа

```bash
# Интерактивный режим (меню)
python tools/sync_telegram_api.py

# Получить ключ с сервера и синхронизировать
python tools/sync_telegram_api.py --fetch

# Показать текущие настройки
python tools/sync_telegram_api.py --show

# Установить конкретный ключ
python tools/sync_telegram_api.py --key "ваш_ключ"

# Установить ключ и URL
python tools/sync_telegram_api.py --key "ключ" --url "http://IP:8000/ai_query"

# Тест соединения с API
python tools/sync_telegram_api.py --test
```

### ai_search.py — AI поиск компонентов

```bash
# Простой поиск
python tools/ai_search.py "TPS54302"

# Поиск аналогов
python tools/ai_search.py "LM2596" --prompt analogs

# Краткое описание ИВП
python tools/ai_search.py "NE555" --prompt ivp_short

# JSON вывод
python tools/ai_search.py "MAX232" --json

# Сохранить в файл
python tools/ai_search.py "STM32F103" --output result.txt

# Список доступных промптов
python tools/ai_search.py --list-prompts
```

---

## 🔄 Синхронизация ключа

### Автоматическая (рекомендуется)

```bash
python tools/sync_telegram_api.py --fetch
```

Скрипт:
1. Подключается к серверу по SSH
2. Получает `API_SECRET_KEY` из `.env`
3. Обновляет `config_qt.json` в проекте
4. Обновляет `config_qt.json` в папке установки

### Ручная синхронизация

**Шаг 1:** Получить ключ на сервере
```bash
ssh -p 22542 root@138.124.19.67
grep API_SECRET_KEY /opt/TelegramHelper/.env
```

**Шаг 2:** Скопировать ключ в BOMCategorizer

Отредактируйте `config_qt.json`:
```json
{
  "api_keys": {
    "telegram_url": "http://138.124.19.67:8000/ai_query",
    "telegram_key": "ваш_ключ_здесь"
  }
}
```

### Через Telegram бот

Администратор может получить ключ командой:
```
/api
```

---

## 🧪 Тестирование API

### Проверка доступности сервера

```bash
# curl (macOS/Linux)
curl http://138.124.19.67:8000/health

# PowerShell (Windows)
Invoke-WebRequest -Uri "http://138.124.19.67:8000/health"
```

Ожидаемый ответ:
```json
{"status":"healthy","timestamp":...,"anthropic_available":true}
```

### Тест AI запроса

```bash
python tools/ai_search.py "NE555" --json
```

Ожидаемый ответ:
```json
{
  "response": "NE555 - это таймер...",
  "provider": "anthropic",
  "status": "success"
}
```

### Проверка через скрипт

```bash
python tools/sync_telegram_api.py --test
```

---

## ⚙️ Конфигурация

### Расположение файлов

| Платформа | Путь |
|-----------|------|
| **Проект** | `BOMCategorizer/config_qt.json` |
| **macOS** | `~/Library/Application Support/BOMCategorizer/config_qt.json` |
| **Windows** | `%APPDATA%\BOMCategorizer\config_qt.json` |
| **Linux** | `~/.config/BOMCategorizer/config_qt.json` |

### Структура config_qt.json

```json
{
  "api_keys": {
    "anthropic": "",
    "openai": "",
    "ollama_url": "http://localhost:11434",
    "telegram_url": "http://138.124.19.67:8000/ai_query",
    "telegram_key": "754c7afb2b146882181bac0af01f21607158e3ffba8d5853628364b61101464c",
    "telegram_hmac_secret": ""
  },
  "telegram_security": {
    "app_id": "bomcategorizer-v4",
    "enable_signature": true,
    "verify_ssl": false
  }
}
```

### Параметры API

| Параметр | Описание | Обязательный |
|----------|----------|--------------|
| `telegram_url` | URL эндпоинта `/ai_query` | ✅ |
| `telegram_key` | Секретный ключ (64 символа hex) | ✅ |
| `telegram_hmac_secret` | HMAC секрет для подписи | ❌ |
| `app_id` | Идентификатор приложения | ❌ |
| `enable_signature` | Включить подпись запросов | ❌ |

---

## 🔧 Команды на сервере TelegramHelper

### Управление API ключом

```bash
cd /opt/TelegramHelper

# Показать текущий ключ
./scripts/api_key.sh show

# Сгенерировать новый ключ
./scripts/api_key.sh generate

# После изменения — перезапустить
docker compose down && docker compose up -d
```

### Проверка

```bash
# Ключ в .env
grep API_SECRET_KEY .env

# Ключ в контейнере
docker exec telegram-helper env | grep API_SECRET_KEY

# Статус API
curl http://localhost:8000/health
```

---

## 🆘 Устранение проблем

### ❌ Ошибка "Connection refused"

**Причина:** API сервер не запущен

**Решение:**
```bash
# На сервере
docker ps | grep telegram-api
# Если нет — запустить
docker compose up -d
```

### ❌ Ошибка "401 Unauthorized"

**Причина:** Неверный API ключ

**Решение:**
```bash
# Синхронизировать ключ
python tools/sync_telegram_api.py --fetch
```

### ❌ Ошибка "Timeout"

**Причина:** Сервер недоступен или медленный

**Решение:**
1. Проверить доступность: `ping 138.124.19.67`
2. Проверить порт: `curl http://138.124.19.67:8000/health`
3. Проверить firewall на сервере

### ❌ SSH не подключается

**Причина:** Неверный порт или ключи

**Решение:**
```bash
# Проверить подключение
ssh -p 22542 root@138.124.19.67 "echo OK"
```

### ❌ Ключ не синхронизируется в установленное приложение

**Причина:** Приложение использует собственную папку конфигурации

**Решение:**
```bash
# Показать все пути
python tools/sync_telegram_api.py --show

# Убедиться что оба файла обновлены
```

---

## 📚 Связанная документация

- [AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md) — Полное руководство по AI интеграции
- [CLI_USAGE.md](CLI_USAGE.md) — Использование командной строки
- [TelegramHelper/VPS_GUIDE.md](../../TelegramHelper/VPS_GUIDE.md) — Управление сервером

---

## 🔑 Краткая шпаргалка

```bash
# Синхронизировать ключ с сервера
python tools/sync_telegram_api.py --fetch

# Показать настройки
python tools/sync_telegram_api.py --show

# Тест AI поиска
python tools/ai_search.py "NE555"

# На сервере: новый ключ
./scripts/api_key.sh generate && docker compose down && docker compose up -d
```

---

*Версия документа: 1.0*  
*Автор: Куреин М.Н.*

