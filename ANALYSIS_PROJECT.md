# 🏗 Архитектура проекта BOM Categorizer

**BOM Categorizer** — десктопное приложение для автоматической классификации электронных компонентов из спецификаций (BOM).

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v5.4.12 (PySide6)  
> **Язык:** Python 3.13+  
> **Архитектура:** Модульный пайплайн + AI интеграция + Шифрование

---

## 📋 Содержание

1. [Основные идеи и принципы](#-основные-идеи-и-принципы)
2. [Технологический стек](#-технологический-стек)
3. [Ключевые модули системы](#-ключевые-модули-системы)
4. [AI интеграция](#-ai-интеграция)
5. [Шифрование данных](#-шифрование-данных)
6. [Структура файлов проекта](#-структура-файлов-проекта)

---

## 💡 Основные идеи и принципы

### 1. Модульный пайплайн (Pipeline Processing)

Обработка данных идёт линейно:

```
Чтение → Нормализация → Классификация → Обогащение → Вывод
```

Это позволяет добавлять новые шаги (AI-классификацию) без переписывания всего кода.

### 2. Гибридная архитектура (Dual GUI)

Ядро (`bom_categorizer/`) отделено от интерфейса:
- **Standard Edition** — Tkinter (легковесный)
- **Modern Edition** — PySide6 (современный)
- **CLI режим** — для автоматизации

### 3. Двухуровневая база знаний

| Уровень | Описание | Расположение |
|---------|----------|--------------|
| **Static** | Шаблон БД (Read-only) | `data/component_database_template.json` |
| **Dynamic** | Пользовательская БД | `%APPDATA%/BOMCategorizer/` |

Обновление приложения не теряет накопленный опыт.

### 4. Каскадная классификация

```
1. Точное совпадение (База данных)
      ↓ не найдено
2. Regex паттерны (Технические характеристики)
      ↓ не найдено
3. Пользовательские правила (rules.json)
      ↓ не найдено
4. AI классификация (TelegramHelper API)
```

---

## 🛠 Технологический стек

| Область | Технологии | Назначение |
|---------|------------|------------|
| **Core** | Python 3.13+ | Основной язык |
| **Data** | Pandas | DataFrame, фильтрация, сортировка |
| **GUI (Modern)** | PySide6 (Qt) | Современный интерфейс, QThread |
| **GUI (Standard)** | Tkinter | Легковесный интерфейс |
| **IO** | OpenPyXL, python-docx | Excel и Word файлы |
| **PDF** | ReportLab | Экспорт в PDF с кириллицей |
| **AI** | HTTP API | Интеграция с TelegramHelper |
| **Crypto** | cryptography | AES-256-GCM шифрование |
| **Build** | Inno Setup, py2app | Инсталляторы Win/macOS |
| **QA** | pytest | Тестирование |

---

## 🔑 Ключевые модули системы

### Ядро (Core)

| Модуль | Роль | Описание |
|--------|------|----------|
| `main.py` | 🧠 Оркестратор | Запускает пайплайн обработки |
| `classifiers.py` | 🔍 Мозг | Regex и эвристики классификации |
| `component_database.py` | 💾 Память | Управление базой знаний |
| `formatters.py` | 🧹 Инструменты | Очистка данных, извлечение номиналов |
| `parsers.py` | 📥 Ввод | Чтение .docx, .xlsx, .txt |
| `config_manager.py` | ⚙️ Конфиг | Управление настройками |
| `encryption.py` | 🔐 Безопасность | AES-256-GCM шифрование |
| `tru_merger.py` | 🔄 TRU Merger | Слияние BOM с данными ТРУ/РКМ |
| `tru_rkm_processor.py` | 📦 RKM Logic | Обработка справочников ТРУ |

### GUI Modern Edition (`gui/`)

| Модуль | Описание |
|--------|----------|
| `main_window.py` | Главное окно |
| `dialogs.py` | Диалоговые окна |
| `sections.py` | Виджеты и секции |
| `menu.py` | Главное меню |
| `scaling.py` | Масштабирование и темы |
| `search.py` | Глобальный поиск |
| `search_methods.py` | Методы поиска |
| `workers.py` | Фоновые потоки (QThread) |
| `drag_drop.py` | Drag & Drop файлов |
| `ai_classifier.py` | AI классификация |
| `pdf_search.py` | Поиск компонентов |
| `pdf_search_dialogs.py` | Диалоги AI поиска |
| `processing_handlers.py` | Обработка BOM/ТРУ |
| `database_handlers.py` | Работа с БД в GUI |
| `file_handlers.py` | Обработка файлов |

### Вывод (Output)

| Модуль | Описание |
|--------|----------|
| `excel_writer.py` | Excel отчёты (горизонтальные SOURCES, текст ERP) |
| `txt_writer.py` | Текстовые отчёты |
| `pdf_exporter.py` | PDF (авто-ориентация, источники блоком) |

---

## 🤖 AI интеграция

BOM Categorizer интегрируется с **TelegramHelper** для AI-поиска информации о компонентах.

### Архитектура

```
┌─────────────────────┐                         ┌─────────────────────┐
│   BOM Categorizer   │      HTTP + AES-256     │   TelegramHelper    │
│   (Desktop App)     │ ◄─────────────────────► │   (VPS Server)      │
└─────────────────────┘                         └─────────────────────┘
         │                                               │
         │ config_qt.json                                │ .env
         │ - telegram_url                                │ - API_SECRET_KEY
         │ - telegram_key                                │ - ENCRYPTION_KEY
         │ - encryption_key                              │ - ANTHROPIC_API_KEY
         └───────────────────────────────────────────────┘
```

### Возможности

- **Описание компонента** — характеристики, корпус, применение
- **Поиск аналогов** — совместимые замены
- **IVP описание** — входящий контроль
- **Поиск по PDF** — даташиты онлайн

### Режимы передачи данных

| Режим | Описание | Когда использовать |
|-------|----------|-------------------|
| **Plain** | Обычный JSON | Локальная сеть, доверенное соединение |
| **Encrypted** | AES-256-GCM + Base64 | Интернет, публичные сети |

API автоматически определяет режим по содержимому запроса.

### Получение ключей

В Telegram боте (для админов):
```
/api              — API ключ для авторизации
/encryption_key   — Ключ шифрования (или fallback на API ключ)
/gen_encryption_key — Сгенерировать новый ключ шифрования
```

### Конфигурация

`config_qt.json`:
```json
{
  "api_keys": {
    "telegram_url": "http://IP:8000/ai_query",
    "telegram_key": "YOUR_API_KEY",
    "encryption_key": "YOUR_ENCRYPTION_KEY"
  }
}
```

### CLI использование

```bash
# AI поиск компонента
python tools/ai_search.py "TPS54302"

# Поиск аналогов
python tools/ai_search.py "LM2596" --prompt analogs

# JSON вывод
python tools/ai_search.py "NE555" --json
```

---

## 🔐 Шифрование данных

### Алгоритм: AES-256-GCM

| Характеристика | Описание |
|----------------|----------|
| **Алгоритм** | AES-256-GCM (Galois/Counter Mode) |
| **Ключ** | 256 бит (32 байта) |
| **Nonce** | 12 байт (уникальный для каждого сообщения) |
| **Auth Tag** | 16 байт (проверка целостности) |

### Преимущества

- **AEAD** — шифрование + аутентификация в одном
- **Zero Trust** — защита даже при компрометации TLS
- **Автоопределение** — один endpoint для обоих режимов

### Структура зашифрованного пакета

```
┌─────────┬──────────┬─────────────┬─────────────────┬──────────┐
│ Version │  Key ID  │    Nonce    │   Ciphertext    │   Tag    │
│  1 byte │ 4 bytes  │  12 bytes   │    N bytes      │ 16 bytes │
└─────────┴──────────┴─────────────┴─────────────────┴──────────┘
```

### Пример запроса

**Обычный (Plain):**
```json
{"prompt": "Опиши компонент TPS54302", "provider": "anthropic"}
```

**Зашифрованный (Encrypted):**
```json
{"data": "AQAAAAEAAACnK8x2...base64..."}
```

---

## 📂 Структура файлов проекта

```
BOMCategorizer/
├── 📦 bom_categorizer/              # Основной пакет (бизнес-логика)
│   ├── __init__.py
│   ├── main.py                      # 🧠 Оркестратор пайплайна
│   ├── classifiers.py               # 🔍 Логика классификации
│   ├── parsers.py                   # 📥 Чтение файлов
│   ├── formatters.py                # 🧹 Очистка данных
│   ├── component_database.py        # 💾 База знаний (JSON)
│   ├── config_manager.py            # ⚙️ Управление конфигурацией
│   ├── encryption.py                # 🔐 AES-256-GCM шифрование
│   ├── excel_writer.py              # 📊 Excel отчёты
│   ├── txt_writer.py                # 📝 Текстовые отчёты
│   ├── pdf_exporter.py              # 📄 PDF экспорт
│   ├── podborka_extractor.py        # 📋 Извлечение подборки
│   ├── utils.py                     # 🛠 Утилиты
│   ├── cli_interactive.py           # 💬 Интерактивная консоль
│   ├── styles.py                    # 🎨 Стили GUI
│   │
│   ├── 📁 gui/                      # ✨ Modern Edition (PySide6)
│   │   ├── __init__.py
│   │   ├── main_window.py           # Главное окно
│   │   ├── dialogs.py               # Диалоги
│   │   ├── sections.py              # Виджеты
│   │   ├── menu.py                  # Меню
│   │   ├── scaling.py               # Масштабирование
│   │   ├── search.py                # Поиск
│   │   ├── search_methods.py        # Методы поиска
│   │   ├── workers.py               # QThread
│   │   ├── drag_drop.py             # Drag & Drop
│   │   ├── ai_classifier.py         # AI классификация
│   │   ├── pdf_search.py            # Поиск компонентов
│   │   └── pdf_search_dialogs.py    # AI диалоги
│   │
│   └── gui.py                       # ✅ Standard Edition (Tkinter)
│
├── 🚀 Точки входа:
│   ├── app_qt.py                    # ▶️ Modern Edition
│   └── app.py                       # ▶️ Standard Edition
│
├── 📁 tools/                        # 🛠 CLI утилиты
│   ├── ai_search.py                 # 🤖 AI поиск компонентов
│   ├── split_bom.py                 # 💻 CLI обработка BOM
│   ├── manage_database.py           # 🗄️ Управление БД
│   ├── update_version.py            # 🔄 Синхронизация версий
│   └── ...                          # Другие утилиты
│
├── 📁 scripts/                      # 🖥 Скрипты
│   └── bump_version.py              # 🔄 Управление версиями
│
├── 📁 deployment/                   # 📦 Сборка и развёртывание
│   ├── build_macos.sh               # 🍎 macOS сборка
│   ├── installer_qt.iss             # 📄 Inno Setup (Modern)
│   └── ...                          # Другие скрипты сборки
│
├── 📁 config/                       # ⚙️ Конфигурация
│   ├── config.json.template         # Шаблон Standard
│   ├── config_qt.json.template      # Шаблон Modern
│   └── rules.json                   # Правила классификации
│
├── 📁 data/                         # 💾 Данные
│   └── component_database_template.json # Шаблон БД
│
├── 📁 docs/                         # 📚 Документация
│   ├── VERSION_MANAGEMENT.md        # 🔄 Управление версиями
│   ├── AI_INTEGRATION_GUIDE.md      # 🤖 AI интеграция
│   └── ...                          # Другие документы
│
├── 📁 tests/                        # 🧪 Тесты
│   └── ...
│
└── ⚙️ Конфигурация проекта:
    ├── requirements.txt             # Зависимости
    ├── config_qt.json               # Конфиг Modern (локальный)
    └── .gitignore                   # Исключения Git
```

---

## 📊 Статистика проекта

| Метрика | Значение |
|---------|----------|
| Файлов Python | ~50 |
| Строк кода | ~15,000 |
| Документов | 21 |
| Тестов | 4 модуля |
| Поддерживаемых форматов | .doc, .docx, .xlsx, .txt |
| Категорий компонентов | 20+ |
| Шифрование | AES-256-GCM |

---

**Разработчик:** Куреин М.Н.  
**Обновлено:** 24.12.2025
