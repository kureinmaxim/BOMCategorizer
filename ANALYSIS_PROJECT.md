# 🏗 Архитектура проекта BOM Categorizer

**BOM Categorizer** — десктопное приложение для автоматической классификации электронных компонентов из спецификаций (BOM).

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v5.5.1 (PySide6)  
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
7. [Структура проекта (подробно)](#-структура-проекта-подробно)

---

## 💡 Основные идеи и принципы

### 1. Модульный пайплайн (Pipeline Processing)

Обработка данных идёт линейно:

```
Чтение → Нормализация → Классификация → Обогащение → Вывод
```

Это позволяет добавлять новые шаги (AI-классификацию) без переписывания всего кода.

Дополнительно поддерживается режим **BOM + ТРУ (merge)**:
- перенос данных из ТРУ в BOM (№ ТРУ, стоимость, корректировка количества)
- формирование отчётов **`*_ostatki`** / **`*_zapas`** (и PDF версии для печати)

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

## 📁 Структура проекта (подробно)

> Объединено из `docs/PROJECT_STRUCTURE.md` (файл удалён после объединения).

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v5.4.12 (PySide6)  
> **Обновлено:** 24.12.2025

---

### 📋 Содержание

1. [Организация файлов](#️-организация-файлов)
2. [Путеводитель по документации](#-путеводитель-по-документации)
3. [Ключевые компоненты](#-ключевые-компоненты)
4. [Рабочий процесс](#-рабочий-процесс)

---

### 🗂️ Организация файлов

```
BOMCategorizer/
├── 📄 README.md                          # Главная документация
├── 📄 ANALYSIS_PROJECT.md                # Архитектура проекта
├── 📄 BUILD.md                           # Инструкция по сборке
├── 📄 CHANGELOG.md                       # История изменений
├── 📄 GUIDE.md                           # Руководство пользователя (режимы, BOM/ТРУ/merge)
├── 📄 SETUP.md                           # Настройка окружения
├── 📄 CREATE_GIT_RELEASE.md              # Создание релизов
│
├── 🚀 Точки входа:
│   ├── app.py                            # Standard Edition (Tkinter)
│   ├── app_qt.py                         # Modern Edition (PySide6)
│   └── run_tests.py                      # Запуск тестов
│
├── 📦 bom_categorizer/                   # Ядро (Бизнес-логика)
│   ├── __init__.py                       # Инициализация пакета
│   ├── main.py                           # Оркестратор пайплайна
│   ├── classifiers.py                    # Логика классификации
│   ├── parsers.py                        # Парсеры (DOCX, XLSX, TXT)
│   ├── formatters.py                     # Форматирование и очистка
│   ├── component_database.py             # Управление базой знаний
│   ├── config_manager.py                 # Управление конфигурацией
│   ├── encryption.py                     # 🔐 AES-256-GCM шифрование
│   ├── excel_writer.py                   # Генерация Excel отчётов
│   ├── txt_writer.py                     # Генерация текстовых отчётов
│   ├── pdf_exporter.py                   # Экспорт в PDF
│   ├── podborka_extractor.py             # Извлечение подборки
│   ├── tru_merger.py                     # 🔄 Слияние данных ТРУ
│   ├── tru_rkm_processor.py              # Обработка данных РКМ
│   ├── utils.py                          # Вспомогательные утилиты
│   ├── cli_interactive.py                # Интерактивная консоль
│   ├── styles.py                         # Стили для GUI
│   ├── gui.py                            # GUI Standard Edition
│   │
│   └── gui/                              # 📁 Modern Edition GUI (пакет)
│       ├── __init__.py                   # Инициализация GUI пакета
│       ├── main_window.py                # Главное окно приложения
│       ├── dialogs.py                    # Диалоговые окна
│       ├── sections.py                   # Виджеты и секции
│       ├── menu.py                       # Главное меню
│       ├── scaling.py                    # Масштабирование и темы
│       ├── search.py                     # Глобальный поиск
│       ├── search_methods.py             # Методы поиска
│       ├── workers.py                    # Фоновые потоки (QThread)
│       ├── drag_drop.py                  # Drag & Drop
│       ├── file_handlers.py              # Обработка файлов
│       ├── database_handlers.py          # Работа с БД в GUI
│       ├── processing_handlers.py        # Обработка BOM/ТРУ
│       ├── help_dialogs.py               # Окна помощи
│       ├── ai_classifier.py              # AI классификация
│       ├── pdf_search.py                 # Поиск компонентов
│       └── pdf_search_dialogs.py         # Диалоги AI поиска
│
├── 📁 config/                            # ⚙️ Конфигурационные файлы
│   ├── config.json.template              # Шаблон Standard Edition
│   ├── config_qt.json.template           # Шаблон Modern Edition
│   └── rules.json                        # Правила классификации
│
├── 📁 data/                              # 💾 Данные приложения
│   ├── component_database_template.json  # Шаблон базы данных
│   └── component_database.json           # Рабочая база данных
│
├── 📁 assets/                            # 🎨 Ресурсы
│   ├── icon.png                          # Иконка (PNG)
│   ├── icon.ico                          # Иконка (Windows)
│   └── icon.icns                         # Иконка (macOS)
│
├── 📁 scripts/                           # 🔨 Скрипты
│   ├── bump_version.py                   # 🔄 Управление версиями
│   ├── run_app.bat                       # Универсальный запуск
│   ├── run_modern_debug.bat              # Отладка Modern Edition
│   ├── run_standard_debug.bat            # Отладка Standard Edition
│   ├── run_tests.bat                     # Запуск тестов
│   ├── test_examples.bat                 # Тесты на реальных файлах
│   ├── post_install.ps1                  # Пост-установка
│   ├── repair_install.ps1                # Восстановление установки
│   ├── rebuild_venv.ps1                  # Пересборка venv
│   ├── manage_database.bat               # Управление БД
│   ├── database_backup.bat               # Резервное копирование БД
│   ├── database_export.bat               # Экспорт БД в Excel
│   ├── database_stats.bat                # Статистика БД
│   ├── split_bom.bat                     # CLI обработка
│   ├── check_pdf_fonts.bat               # Проверка шрифтов
│   └── download_fonts.bat/ps1            # Загрузка шрифтов
│
├── 📁 tools/                             # 🐍 Python утилиты
│   ├── ai_search.py                      # 🤖 AI поиск компонентов
│   ├── split_bom.py                      # CLI обработка файлов
│   ├── manage_database.py                # Управление БД (CLI)
│   ├── interactive_classify.py           # Интерактивная классификация
│   ├── interactive_classify_improved.py  # Улучшенная классификация
│   ├── preview_unclassified.py           # Предпросмотр неклассифицированных
│   ├── merge_component_database.py       # Слияние баз данных
│   ├── update_version.py                 # Управление версиями
│   ├── sync_installer_versions.py        # Синхронизация версий
│   ├── sync_telegram_api.py              # Синхронизация API ключей
│   ├── create_icons.py                   # Создание иконок
│   ├── check_pdf_fonts.py                # Проверка PDF шрифтов
│   └── init_project.py                   # Инициализация проекта
│
├── 📁 deployment/                        # 📦 Сборка и развёртывание
│   ├── build_installer.py                # Сборка Windows инсталлятора
│   ├── build_macos.sh                    # Сборка macOS DMG
│   ├── build_macos_simple.sh             # Упрощённая сборка macOS
│   ├── setup_macos.py                    # Конфигурация py2app
│   ├── installer_clean.iss               # Inno Setup: Standard
│   ├── installer_qt.iss                  # Inno Setup: Modern
│   ├── create_release.ps1                # Создание релиза (Windows)
│   ├── create_release.sh                 # Создание релиза (Unix)
│   ├── upload_to_existing_release.ps1    # Загрузка в релиз (Win)
│   └── upload_to_existing_release.sh     # Загрузка в релиз (Unix)
│
├── 📁 tests/                             # 🧪 Автоматические тесты
│   ├── __init__.py                       # Инициализация тестов
│   ├── conftest.py                       # Фикстуры pytest
│   ├── test_classifiers.py               # Тесты классификации
│   ├── test_database.py                  # Тесты базы данных
│   ├── test_formatters.py                # Тесты форматирования
│   └── test_integration.py               # Интеграционные тесты
│
├── 📁 docs/                              # 📚 Документация
│   ├── AI_INTEGRATION_GUIDE.md           # 🤖 AI интеграция
│   ├── AI_CLASSIFIER_README.md           # 🤖 AI классификатор
│   ├── CLI_USAGE.md                      # 💻 CLI использование
│   ├── TESTING_GUIDE.md                  # 🧪 Тестирование
│   ├── USER_MANUAL.md                    # 📖 Руководство пользователя
│   ├── DATABASE_GUIDE.md                 # 💾 Работа с БД
│   ├── DATABASE_ARCHITECTURE.md          # 💾 Архитектура БД
│   ├── (merged into STATE_DIAGRAMS.md)   # 📋 Правила классификации (бывш. CLASSIFICATION_RULES.md)
│   ├── INTERACTIVE_MODE_GUIDE.md         # 💬 Интерактивный режим
│   ├── PDF_SEARCH_GUIDE.md               # 🔍 Поиск компонентов
│   ├── DRAG_DROP_README.md               # 📎 Drag & Drop
│   ├── VERSION_MANAGEMENT.md             # 🔄 Управление версиями
│   └── ...                               # Другие документы
│
├── 📁 fonts/                             # 🔤 Шрифты для PDF
│   ├── DejaVuSans.ttf                    # Основной шрифт
│   └── DejaVuSans-Bold.ttf               # Жирный шрифт
│
└── 📄 Конфигурация проекта:
    ├── requirements.txt                  # Основные зависимости
    ├── requirements_install.txt          # Зависимости для установки
    ├── config.json                       # Конфиг Standard Edition
    ├── config_qt.json                    # Конфиг Modern Edition
    ├── .gitignore                        # Исключения Git
    └── venv/                             # Виртуальное окружение
```

---

### 📚 Путеводитель по документации

#### 🟢 Для пользователей

| Документ | Описание |
|----------|----------|
| [README.md](README.md) | Главная страница, обзор возможностей |
| [GUIDE.md](GUIDE.md) | Руководство пользователя (режимы, BOM/ТРУ/merge) |
| [docs/USER_MANUAL.md](docs/USER_MANUAL.md) | Полное руководство пользователя |
| [docs/OFFLINE_INSTALLATION_GUIDE.md](docs/OFFLINE_INSTALLATION_GUIDE.md) | Установка без интернета |

#### 🔵 Для разработчиков

| Документ | Описание |
|----------|----------|
| [ANALYSIS_PROJECT.md](ANALYSIS_PROJECT.md) | Архитектура и технологии |
| [BUILD.md](BUILD.md) | Сборка инсталляторов |
| [SETUP.md](SETUP.md) | Настройка окружения |
| [VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) | Управление версиями |
| [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Тестирование |

#### 🟡 AI и автоматизация

| Документ | Описание |
|----------|----------|
| [docs/AI_INTEGRATION_GUIDE.md](docs/AI_INTEGRATION_GUIDE.md) | Интеграция с TelegramHelper |
| [docs/CLI_USAGE.md](docs/CLI_USAGE.md) | Командная строка и скрипты |
| [docs/INTERACTIVE_MODE_GUIDE.md](docs/INTERACTIVE_MODE_GUIDE.md) | Обучение классификатора |

#### 🟣 Справочная информация

| Документ | Описание |
|----------|----------|
| [CHANGELOG.md](CHANGELOG.md) | История изменений |
| [docs/BAT_FILES_GUIDE.md](docs/BAT_FILES_GUIDE.md) | BAT файлы и скрипты |
| [CREATE_GIT_RELEASE.md](CREATE_GIT_RELEASE.md) | Создание релизов |

---

### 📦 Ключевые компоненты

#### 1. Двойной GUI

| Версия | Файлы | Технология |
|--------|-------|------------|
| **Standard** | `app.py` + `gui.py` | Tkinter |
| **Modern** | `app_qt.py` + `gui/` | PySide6 (Qt) |

Modern Edition разделён на модули для лучшей поддерживаемости.

#### 2. AI интеграция

- **`gui/ai_classifier.py`** — AI классификация компонентов
- **`gui/pdf_search.py`** — поиск информации о компонентах
- **`gui/pdf_search_dialogs.py`** — диалоги AI запросов
- **`tools/ai_search.py`** — CLI для AI поиска

Подключается к **TelegramHelper API** для получения информации.

#### 3. Шифрование данных

| Компонент | Описание |
|-----------|----------|
| **`encryption.py`** | AES-256-GCM шифрование |
| **Автоопределение** | API сам определяет режим (plain/encrypted) |
| **Ключи** | `/encryption_key` и `/gen_encryption_key` в боте |

#### 4. База данных компонентов

| Уровень | Файл | Доступ |
|---------|------|--------|
| Static | `data/component_database_template.json` | Read-only |
| Dynamic | `%APPDATA%/BOMCategorizer/` | Read-write |

#### 5. Организация директорий

| Директория | Назначение | Для кого |
|------------|------------|----------|
| `scripts/` | BAT/PS1 скрипты + bump_version.py | Все |
| `tools/` | Python CLI утилиты | Разработчики |
| `deployment/` | Сборка инсталляторов | Разработчики |
| `config/` | Шаблоны конфигурации | Все |
| `data/` | Данные приложения | Все |

---

### 🔄 Рабочий процесс

#### Для пользователей

```bash
# 1. Установка
# Запустить инсталлятор или:
scripts/post_install.ps1

# 2. Запуск
scripts/run_app.bat

# 3. Управление БД
scripts/manage_database.bat

# 4. Резервное копирование
scripts/database_backup.bat
```

#### Для разработчиков

```bash
# 1. Клонирование и настройка
git clone <repo>
python tools/init_project.py

# 2. Разработка
scripts/run_modern_debug.bat    # Modern Edition
scripts/run_standard_debug.bat  # Standard Edition

# 3. Тестирование
scripts/run_tests.bat

# 4. AI поиск (CLI)
python tools/ai_search.py "TPS54302"

# 5. Обновление версии (только Modern по умолчанию)
./scripts/bump_version.py --bump patch
./scripts/bump_version.py --bump minor --edition both  # Обе редакции

# 6. Сборка
python deployment/build_installer.py  # Windows
./deployment/build_macos.sh           # macOS
```

---

### ✅ Преимущества структуры

| Аспект | Описание |
|--------|----------|
| **Разделение** | Скрипты пользователя отделены от инструментов разработчика |
| **Модульность** | GUI разделён на логические компоненты |
| **AI Ready** | Встроенная интеграция с TelegramHelper |
| **Шифрование** | AES-256-GCM для защиты данных |
| **Масштабируемость** | Легко добавлять новые модули |
| **Документация** | Полный набор документов охватывает все аспекты |

---

*Версия документа: 4.0*  
*Автор: Куреин М.Н.*

---

## 📊 Статистика проекта

| Метрика | Значение |
|---------|----------|
| Файлов Python | ~55 |
| Строк кода | ~18,000 |
| Документов | 22 |
| Тестов | 4 модуля |
| Поддерживаемых форматов | .doc, .docx, .xlsx, .txt |
| Категорий компонентов | 20+ |
| Шифрование | AES-256-GCM |

---

**Разработчик:** Куреин М.Н.  
**Обновлено:** 14.01.2026
