# 🏗 Архитектура проекта BOM Categorizer

**BOM Categorizer** — десктопное приложение для автоматической классификации электронных компонентов из спецификаций (BOM).

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v4.5.0 (PySide6)  
> **Язык:** Python 3.13+  
> **Архитектура:** Модульный пайплайн + AI интеграция

---

## 📋 Содержание

1. [Основные идеи и принципы](#-основные-идеи-и-принципы)
2. [Технологический стек](#-технологический-стек)
3. [Ключевые модули системы](#-ключевые-модули-системы)
4. [AI интеграция](#-ai-интеграция)
5. [Структура файлов проекта](#-структура-файлов-проекта)

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

### Вывод (Output)

| Модуль | Описание |
|--------|----------|
| `excel_writer.py` | Excel отчёты (.xlsx) |
| `txt_writer.py` | Текстовые отчёты |
| `pdf_exporter.py` | PDF с кириллицей |

---

## 🤖 AI интеграция

BOM Categorizer интегрируется с **TelegramHelper** для AI-поиска информации о компонентах.

### Архитектура

```
┌─────────────────────┐     HTTP/HTTPS      ┌─────────────────────┐
│   BOM Categorizer   │ ←──────────────────→ │   TelegramHelper    │
│   (Desktop App)     │     API Request      │   (VPS Server)      │
└─────────────────────┘                      └─────────────────────┘
         │                                            │
         │ config_qt.json                             │ .env
         │ - telegram_url                             │ - API_SECRET_KEY
         │ - telegram_key                             │ - ANTHROPIC_API_KEY
         └────────────────────────────────────────────┘
```

### Возможности

- **Описание компонента** — характеристики, корпус, применение
- **Поиск аналогов** — совместимые замены
- **IVP описание** — входящий контроль
- **Поиск по PDF** — даташиты онлайн

### Получение API ключа

В Telegram боте (для админов):
```
/api
```

### Конфигурация

`config_qt.json`:
```json
{
  "telegram_url": "http://IP:8000/ai_query",
  "telegram_key": "YOUR_API_KEY"
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
│   ├── interactive_classify.py      # 🎓 Обучение классификатора
│   ├── interactive_classify_improved.py # 🎓 Улучшенное обучение
│   ├── preview_unclassified.py      # 👁 Предпросмотр
│   ├── merge_component_database.py  # 🔀 Слияние БД
│   ├── update_version.py            # 🔄 Синхронизация версий
│   ├── sync_installer_versions.py   # 🔄 Версии инсталляторов
│   ├── create_icons.py              # 🎨 Создание иконок
│   ├── check_pdf_fonts.py           # 🔤 Проверка шрифтов
│   └── init_project.py              # 🚀 Инициализация
│
├── 📁 deployment/                   # 📦 Сборка и развёртывание
│   ├── build_installer.py           # 🔨 Windows инсталлятор
│   ├── build_macos.sh               # 🍎 macOS сборка
│   ├── build_macos_simple.sh        # 🍎 Упрощённая сборка
│   ├── setup_macos.py               # 🍎 py2app конфиг
│   ├── installer_clean.iss          # 📄 Inno Setup (Standard)
│   ├── installer_qt.iss             # 📄 Inno Setup (Modern)
│   ├── create_release.ps1           # 📦 Релиз (Windows)
│   ├── create_release.sh            # 📦 Релиз (Unix)
│   ├── upload_to_existing_release.ps1 # ⬆️ Публикация (Win)
│   └── upload_to_existing_release.sh  # ⬆️ Публикация (Unix)
│
├── 📁 scripts/                      # 🖥 BAT/PS1 скрипты
│   ├── run_app.bat                  # ▶️ Запуск
│   ├── run_modern_debug.bat         # 🐞 Debug Modern
│   ├── run_standard_debug.bat       # 🐞 Debug Standard
│   ├── run_tests.bat                # 🧪 Тесты
│   ├── test_examples.bat            # 🧪 Тесты на файлах
│   ├── post_install.ps1             # 🔧 Пост-установка
│   ├── repair_install.ps1           # 🔧 Восстановление
│   ├── rebuild_venv.ps1             # 🔄 Пересборка venv
│   ├── database_backup.bat          # 💾 Бэкап БД
│   ├── database_export.bat          # 📤 Экспорт БД
│   ├── database_stats.bat           # 📊 Статистика БД
│   ├── manage_database.bat          # 🗄️ Управление БД
│   ├── split_bom.bat                # 💻 CLI обработка
│   ├── check_pdf_fonts.bat          # 🔤 Проверка шрифтов
│   └── download_fonts.bat/ps1       # 📥 Загрузка шрифтов
│
├── 📁 config/                       # ⚙️ Конфигурация
│   ├── config.json.template         # Шаблон Standard
│   ├── config_qt.json.template      # Шаблон Modern
│   └── rules.json                   # Правила классификации
│
├── 📁 data/                         # 💾 Данные
│   ├── component_database_template.json # Шаблон БД
│   └── component_database.json      # Рабочая БД
│
├── 📁 assets/                       # 🎨 Ресурсы
│   ├── icon.png                     # Иконка (PNG)
│   ├── icon.ico                     # Иконка (Windows)
│   └── icon.icns                    # Иконка (macOS)
│
├── 📁 fonts/                        # 🔤 Шрифты для PDF
│   ├── DejaVuSans.ttf
│   └── DejaVuSans-Bold.ttf
│
├── 📁 docs/                         # 📚 Документация
│   ├── AI_INTEGRATION_GUIDE.md      # 🤖 AI интеграция
│   ├── AI_CLASSIFIER_README.md      # 🤖 AI классификатор
│   ├── CLI_USAGE.md                 # 💻 CLI использование
│   ├── TESTING_GUIDE.md             # 🧪 Тестирование
│   ├── USER_MANUAL.md               # 📖 Руководство
│   ├── DATABASE_GUIDE.md            # 💾 Работа с БД
│   ├── DATABASE_ARCHITECTURE.md     # 💾 Архитектура БД
│   ├── CLASSIFICATION_RULES.md      # 📋 Правила классификации
│   ├── INTERACTIVE_MODE_GUIDE.md    # 💬 Интерактивный режим
│   ├── PDF_SEARCH_GUIDE.md          # 🔍 Поиск компонентов
│   ├── DRAG_DROP_README.md          # 📎 Drag & Drop
│   ├── DISPLAY_FIXES.md             # 🖥 Исправления отображения
│   ├── OFFLINE_INSTALLATION_GUIDE.md # 📦 Офлайн установка
│   ├── PLATFORM_COMPARISON.md       # ⚖️ Сравнение версий
│   ├── VERSION_MANAGEMENT.md        # 🔄 Управление версиями
│   ├── BAT_FILES_GUIDE.md           # 🖥 BAT файлы
│   ├── FONT_SETUP_QUICK.md          # 🔤 Настройка шрифтов
│   ├── ICONS_SETUP.md               # 🎨 Иконки
│   ├── PDF_COLUMN_WIDTH_GUIDE.md    # 📄 Ширина колонок PDF
│   ├── TXT_EXPORT_GUIDE.md          # 📝 TXT экспорт
│   └── PROJECT_STRUCTURE.md         # 📂 Структура проекта
│
├── 📁 tests/                        # 🧪 Тесты
│   ├── conftest.py                  # Фикстуры pytest
│   ├── test_classifiers.py          # Тесты классификации
│   ├── test_formatters.py           # Тесты форматирования
│   ├── test_database.py             # Тесты БД
│   └── test_integration.py          # Интеграционные тесты
│
├── 📝 Документация (корень):
│   ├── README.md                    # 📖 Главная страница
│   ├── ANALYSIS_PROJECT.md          # 🏗 Архитектура (этот файл)
│   ├── CHANGELOG.md                 # 🕒 История изменений
│   ├── BUILD.md                     # 🛠 Сборка инсталляторов
│   ├── SETUP.md                     # ⚙️ Настройка окружения
│   ├── LAUNCHER_GUIDE.md            # 🚀 Инструкция по запуску
│   └── CREATE_GIT_RELEASE.md        # 📦 Создание релизов
│
└── ⚙️ Конфигурация проекта:
    ├── requirements.txt             # Основные зависимости
    ├── requirements_install.txt     # Зависимости установки
    ├── config.json                  # Конфиг Standard
    ├── config_qt.json               # Конфиг Modern
    ├── run_tests.py                 # Запуск тестов
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

---

**Разработчик:** Куреин М.Н.  
**Обновлено:** 25.11.2025
