# 📦 BOM Categorizer

**Автоматическая сортировка электронных компонентов из спецификаций (BOM) по категориям.**  
Загружаете файл → Получаете Excel с разделением на: Резисторы, Конденсаторы, Микросхемы и др.

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v5.0.0 (PySide6)

---

## ⚡️ Быстрый старт

### 🚀 Запуск

**Windows:**
```cmd
scripts\run_modern_debug.bat     # Modern Edition (рекомендуется)
scripts\run_standard_debug.bat   # Standard Edition
```

**macOS / Linux:**
```bash
source venv/bin/activate
python3 app_qt.py    # Modern Edition
python3 app.py       # Standard Edition
```

### 🛠 Установка (первый раз)

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🎯 Возможности

| Функция | Описание |
|---------|----------|
| 📂 **Все форматы** | Excel (.xlsx), Word (.doc/.docx), Text (.txt) |
| 🤖 **Авто-сортировка** | 14+ категорий компонентов |
| 🧠 **Умный парсинг** | Номиналы, допуски, корпуса, ТУ |
| 💾 **База знаний** | Запоминает ваш выбор |
| 🔍 **AI поиск** | Информация о компонентах через TelegramHelper |
| 🔐 **Шифрование** | AES-256-GCM для защиты данных |
| 📄 **PDF экспорт** | С поддержкой кириллицы |
| 🖥️ **Два интерфейса** | Modern (Qt) и Standard (Tkinter) |

---

## 📦 Версии приложения

| Версия | GUI | Описание | Файл запуска |
|--------|-----|----------|--------------|
| **Modern Edition** | PySide6 (Qt) | Современный дизайн, тёмная тема | `app_qt.py` |
| **Standard Edition** | Tkinter | Классический, легковесный | `app.py` |

> Обе версии используют одну базу данных и логику сортировки.

---

## 🤖 AI Интеграция с TelegramHelper

BOMCategorizer интегрируется с **TelegramHelper API** для AI-поиска информации о компонентах.

### Как работает

```
BOMCategorizer → HTTP (+ AES-256) → TelegramHelper (VPS) → Claude/GPT → Ответ
```

### Режимы передачи

| Режим | Описание | Когда использовать |
|-------|----------|-------------------|
| **Plain** | Обычный JSON | Локальная сеть |
| **Encrypted** | AES-256-GCM | Интернет, публичные сети |

API автоматически определяет режим по содержимому запроса.

### Быстрая настройка

```bash
# 1. Синхронизировать API ключ с сервера
python tools/sync_telegram_api.py --fetch

# 2. Проверить соединение
python tools/sync_telegram_api.py --test

# 3. AI поиск компонента
python tools/ai_search.py "NE555"
```

### Настройка через GUI

1. Получить ключи в Telegram боте:
   - `/api` — API ключ для авторизации
   - `/encryption_key` — ключ шифрования
2. BOMCategorizer → режим **Expert** → секция "API ключи"
3. Заполнить **Telegram URL**, **Telegram Key**, **Encryption Key**
4. Сохранить настройки

### Преимущества

- ✅ Не нужны собственные API ключи Anthropic/OpenAI
- ✅ Централизованное управление
- ✅ Шифрование данных (AES-256-GCM)
- ✅ Работает на любом ПК с интернетом

> **Подробнее:** [docs/AI_INTEGRATION_GUIDE.md](docs/AI_INTEGRATION_GUIDE.md)

---

## 💻 CLI Команды

### Обработка BOM файлов

```bash
python tools/split_bom.py --inputs "bom.docx" --xlsx "result.xlsx" --combine
```

### AI поиск компонентов

```bash
# Описание компонента
python tools/ai_search.py "TPS54302"

# Поиск аналогов
python tools/ai_search.py "LM2596" --prompt analogs

# JSON вывод
python tools/ai_search.py "NE555" --json

# Список промптов
python tools/ai_search.py --list-prompts
```

### Управление API

```bash
# Синхронизировать ключ с сервера
python tools/sync_telegram_api.py --fetch

# Показать настройки
python tools/sync_telegram_api.py --show

# Тест соединения
python tools/sync_telegram_api.py --test
```

### Управление версиями

```bash
# Увеличить patch версию (только Modern Edition)
./scripts/bump_version.py --bump patch

# Увеличить minor версию обеих редакций
./scripts/bump_version.py --bump minor --edition both

# Установить конкретную версию
./scripts/bump_version.py --version 5.1.0
```

> **Подробнее:** [docs/CLI_USAGE.md](docs/CLI_USAGE.md)

---

## 📖 Документация

### Для пользователей

| Документ | Описание |
|----------|----------|
| [LAUNCHER_GUIDE.md](LAUNCHER_GUIDE.md) | Руководство по запуску |
| [docs/USER_MANUAL.md](docs/USER_MANUAL.md) | Полное руководство |
| [docs/INTERACTIVE_MODE_GUIDE.md](docs/INTERACTIVE_MODE_GUIDE.md) | Обучение классификатора |

### Для разработчиков

| Документ | Описание |
|----------|----------|
| [SETUP.md](SETUP.md) | Настройка окружения |
| [BUILD.md](BUILD.md) | Сборка инсталляторов |
| [ANALYSIS_PROJECT.md](ANALYSIS_PROJECT.md) | Архитектура проекта |
| [docs/VERSION_MANAGEMENT.md](docs/VERSION_MANAGEMENT.md) | Управление версиями |
| [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Тестирование |

### AI и API

| Документ | Описание |
|----------|----------|
| [docs/AI_INTEGRATION_GUIDE.md](docs/AI_INTEGRATION_GUIDE.md) | Интеграция с TelegramHelper |
| [docs/CLI_USAGE.md](docs/CLI_USAGE.md) | Командная строка |

---

## 🔧 Устранение проблем

| Проблема | Решение |
|----------|---------|
| **Module not found** | Активируйте venv: `source venv/bin/activate` |
| **Access Denied (PowerShell)** | `Set-ExecutionPolicy Bypass -Scope Process` |
| **AI не отвечает** | `python tools/sync_telegram_api.py --test` |
| **Неверный API ключ** | `python tools/sync_telegram_api.py --fetch` |
| **Кодировка Windows** | `chcp 65001` перед запуском |

---

## 📊 Структура проекта

```
BOMCategorizer/
├── app_qt.py              # Modern Edition
├── app.py                 # Standard Edition
├── bom_categorizer/       # Ядро приложения
│   ├── encryption.py      # 🔐 AES-256-GCM
│   └── gui/               # Modern GUI модули
├── scripts/
│   └── bump_version.py    # Управление версиями
├── tools/                 # CLI утилиты
│   ├── ai_search.py       # AI поиск компонентов
│   └── split_bom.py       # Обработка BOM
├── config_qt.json         # Конфигурация Modern
├── config.json            # Конфигурация Standard
└── docs/                  # Документация
```

> **Подробнее:** [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

---

**Разработчик:** Куреин М.Н.  
**Лицензия:** Proprietary  
**Обновлено:** 28.11.2025
