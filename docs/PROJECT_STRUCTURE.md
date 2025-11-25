# 📁 Структура проекта BOM Categorizer

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v4.5.0 (PySide6)  
> **Обновлено:** 25.11.2025

---

## 📋 Содержание

1. [Организация файлов](#️-организация-файлов)
2. [Путеводитель по документации](#-путеводитель-по-документации)
3. [Ключевые компоненты](#-ключевые-компоненты)
4. [Рабочий процесс](#-рабочий-процесс)

---

## 🗂️ Организация файлов

```
BOMCategorizer/
├── 📄 README.md                          # Главная документация
├── 📄 ANALYSIS_PROJECT.md                # Архитектура проекта
├── 📄 BUILD.md                           # Инструкция по сборке
├── 📄 CHANGELOG.md                       # История изменений
├── 📄 LAUNCHER_GUIDE.md                  # Руководство по запуску
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
│   ├── excel_writer.py                   # Генерация Excel отчётов
│   ├── txt_writer.py                     # Генерация текстовых отчётов
│   ├── pdf_exporter.py                   # Экспорт в PDF
│   ├── podborka_extractor.py             # Извлечение подборки
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
├── 📁 scripts/                           # 🔨 Скрипты запуска (BAT/PS1)
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
│   ├── CLASSIFICATION_RULES.md           # 📋 Правила классификации
│   ├── INTERACTIVE_MODE_GUIDE.md         # 💬 Интерактивный режим
│   ├── PDF_SEARCH_GUIDE.md               # 🔍 Поиск компонентов
│   ├── DRAG_DROP_README.md               # 📎 Drag & Drop
│   ├── DISPLAY_FIXES.md                  # 🖥 Исправления отображения
│   ├── OFFLINE_INSTALLATION_GUIDE.md     # 📦 Офлайн установка
│   ├── PLATFORM_COMPARISON.md            # ⚖️ Сравнение версий
│   ├── VERSION_MANAGEMENT.md             # 🔄 Управление версиями
│   ├── BAT_FILES_GUIDE.md                # 🖥 BAT файлы
│   ├── PROJECT_STRUCTURE.md              # 📂 Структура (этот файл)
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

## 📚 Путеводитель по документации

### 🟢 Для пользователей

| Документ | Описание |
|----------|----------|
| [README.md](../README.md) | Главная страница, обзор возможностей |
| [LAUNCHER_GUIDE.md](../LAUNCHER_GUIDE.md) | Руководство по запуску |
| [docs/USER_MANUAL.md](USER_MANUAL.md) | Полное руководство пользователя |
| [docs/OFFLINE_INSTALLATION_GUIDE.md](OFFLINE_INSTALLATION_GUIDE.md) | Установка без интернета |

### 🔵 Для разработчиков

| Документ | Описание |
|----------|----------|
| [ANALYSIS_PROJECT.md](../ANALYSIS_PROJECT.md) | Архитектура и технологии |
| [BUILD.md](../BUILD.md) | Сборка инсталляторов |
| [SETUP.md](../SETUP.md) | Настройка окружения |
| [docs/VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) | Управление версиями |
| [docs/TESTING_GUIDE.md](TESTING_GUIDE.md) | Тестирование |

### 🟡 AI и автоматизация

| Документ | Описание |
|----------|----------|
| [docs/AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md) | Интеграция с TelegramHelper |
| [docs/CLI_USAGE.md](CLI_USAGE.md) | Командная строка и скрипты |
| [docs/INTERACTIVE_MODE_GUIDE.md](INTERACTIVE_MODE_GUIDE.md) | Обучение классификатора |

### 🟣 Справочная информация

| Документ | Описание |
|----------|----------|
| [CHANGELOG.md](../CHANGELOG.md) | История изменений |
| [docs/BAT_FILES_GUIDE.md](BAT_FILES_GUIDE.md) | BAT файлы и скрипты |
| [CREATE_GIT_RELEASE.md](../CREATE_GIT_RELEASE.md) | Создание релизов |

---

## 📦 Ключевые компоненты

### 1. Двойной GUI

| Версия | Файлы | Технология |
|--------|-------|------------|
| **Standard** | `app.py` + `gui.py` | Tkinter |
| **Modern** | `app_qt.py` + `gui/` | PySide6 (Qt) |

Modern Edition разделён на модули для лучшей поддерживаемости.

### 2. AI интеграция

- **`gui/ai_classifier.py`** — AI классификация компонентов
- **`gui/pdf_search.py`** — поиск информации о компонентах
- **`gui/pdf_search_dialogs.py`** — диалоги AI запросов
- **`tools/ai_search.py`** — CLI для AI поиска

Подключается к **TelegramHelper API** для получения информации.

### 3. База данных компонентов

| Уровень | Файл | Доступ |
|---------|------|--------|
| Static | `data/component_database_template.json` | Read-only |
| Dynamic | `%APPDATA%/BOMCategorizer/` | Read-write |

### 4. Организация директорий

| Директория | Назначение | Для кого |
|------------|------------|----------|
| `scripts/` | BAT/PS1 скрипты запуска | Пользователи |
| `tools/` | Python CLI утилиты | Разработчики |
| `deployment/` | Сборка инсталляторов | Разработчики |
| `config/` | Шаблоны конфигурации | Все |
| `data/` | Данные приложения | Все |

---

## 🔄 Рабочий процесс

### Для пользователей

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

### Для разработчиков

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

# 5. Обновление версии
python tools/update_version.py set modern 4.5.1

# 6. Сборка
python deployment/build_installer.py  # Windows
./deployment/build_macos.sh           # macOS
```

---

## ✅ Преимущества структуры

| Аспект | Описание |
|--------|----------|
| **Разделение** | Скрипты пользователя отделены от инструментов разработчика |
| **Модульность** | GUI разделён на логические компоненты |
| **AI Ready** | Встроенная интеграция с TelegramHelper |
| **Масштабируемость** | Легко добавлять новые модули |
| **Документация** | 21 документ охватывает все аспекты |

---

*Версия документа: 2.1*  
*Автор: Куреин М.Н.*
