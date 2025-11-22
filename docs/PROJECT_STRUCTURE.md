# 📁 Структура проекта BOM Categorizer

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v4.4.5 (PySide6)

## 🗂️ Организация файлов

### Корневая директория

```
BOMCategorizer/
├── 📄 README.md                          # Главная документация
├── 📄 BUILD.md                           # Инструкция по сборке
├── 📄 ANALYSIS_PROJECT.md                # Архитектура проекта
├── 📄 CHANGELOG.md                       # История изменений
├── 📄 LAUNCHER_GUIDE.md                  # Руководство по запуску
├── 📄 SETUP.md                           # Настройка окружения
├── 📄 TESTING_README.md                  # Руководство по тестированию
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
│   ├── excel_writer.py                   # Генерация Excel отчетов
│   ├── txt_writer.py                     # Генерация текстовых отчетов
│   ├── pdf_exporter.py                   # Экспорт в PDF
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
│       └── ai_classifier.py              # AI классификация
│
├── 📁 config/                            # ⚙️ Конфигурационные файлы
│   ├── config.json.template              # Шаблон Standard Edition
│   ├── config_qt.json.template           # Шаблон Modern Edition
│   └── rules.json                        # Правила классификации
│
├── 📁 data/                              # 💾 Данные приложения
│   └── component_database_template.json # Шаблон базы данных
│
├── 📁 scripts/                           # 🔨 Скрипты запуска и обслуживания
│   ├── run_app.bat                       # Универсальный запуск (Windows)
│   ├── run_modern_debug.bat              # Отладка Modern Edition
│   ├── run_standard_debug.bat            # Отладка Standard Edition
│   ├── run_tests.bat                     # Запуск тестов
│   ├── post_install.ps1                  # Пост-установка (PowerShell)
│   ├── repair_install.ps1                # Восстановление установки
│   ├── manage_database.bat               # Управление БД
│   ├── database_backup.bat               # Резервное копирование БД
│   ├── database_export.bat               # Экспорт БД в Excel
│   ├── database_stats.bat                # Статистика БД
│   ├── split_bom.bat                     # CLI обработка
│   ├── check_pdf_fonts.bat               # Проверка шрифтов
│   └── download_fonts.bat                # Загрузка шрифтов
│
├── 📁 tools/                             # 🐍 Python утилиты
│   ├── update_version.py                 # Управление версиями
│   ├── sync_installer_versions.py        # Синхронизация версий
│   ├── manage_database.py                # Управление БД (CLI)
│   ├── split_bom.py                      # CLI обработка файлов
│   ├── init_project.py                   # Инициализация проекта
│   ├── create_icons.py                   # Создание иконок
│   ├── check_pdf_fonts.py                # Проверка PDF шрифтов
│   ├── interactive_classify.py           # Интерактивная классификация
│   ├── interactive_classify_improved.py  # Улучшенная классификация
│   └── merge_component_database.py       # Слияние баз данных
│
├── 📁 deployment/                        # 📦 Сборка и развертывание
│   ├── build_installer.py                # Сборка Windows инсталлятора
│   ├── build_macos.sh                    # Сборка macOS DMG
│   ├── setup_macos.py                    # Конфигурация py2app
│   ├── installer_clean.iss               # Inno Setup: Standard
│   ├── installer_qt.iss                  # Inno Setup: Modern
│   ├── create_release.ps1                # Создание релиза (Windows)
│   ├── create_release.sh                 # Создание релиза (macOS/Linux)
│   ├── upload_to_existing_release.ps1    # Загрузка в релиз (Windows)
│   └── upload_to_existing_release.sh     # Загрузка в релиз (macOS/Linux)
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
│   ├── VERSION_MANAGEMENT.md             # Управление версиями
│   ├── TESTING_GUIDE.md                  # Руководство по тестированию
│   ├── OFFLINE_INSTALLATION_GUIDE.md     # Офлайн установка
│   ├── BAT_FILES_GUIDE.md                # Руководство по BAT файлам
│   ├── PROJECT_STRUCTURE.md              # Структура проекта (этот файл)
│   └── ...                               # Другие документы
│
├── 📁 fonts/                             # 🔤 Шрифты для PDF
│   ├── DejaVuSans.ttf                    # Основной шрифт
│   └── DejaVuSans-Bold.ttf               # Жирный шрифт
│
└── 📄 Конфигурация проекта:
    ├── requirements.txt                  # Основные зависимости
    ├── requirements_install.txt          # Зависимости для установки
    ├── requirements_macos.txt            # Зависимости для macOS
    ├── .gitignore                        # Исключения Git
    └── .venv/                            # Виртуальное окружение (не в Git)
```

---

## 📚 Путеводитель по документации

### 🟢 Для пользователей
*   **[README.md](../README.md)** — Главная страница, обзор возможностей.
*   **[LAUNCHER_GUIDE.md](../LAUNCHER_GUIDE.md)** — Подробное руководство по запуску.
*   **[docs/OFFLINE_INSTALLATION_GUIDE.md](OFFLINE_INSTALLATION_GUIDE.md)** — Как установить без интернета.

### 🔵 Для разработчиков
*   **[ANALYSIS_PROJECT.md](../ANALYSIS_PROJECT.md)** — Архитектура, описание модулей и технологий.
*   **[BUILD.md](../BUILD.md)** — Как собрать инсталлятор (Windows/macOS).
*   **[docs/VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md)** — Как обновлять версии и делать релизы.
*   **[SETUP.md](../SETUP.md)** — Настройка окружения после клонирования.
*   **[TESTING_README.md](../TESTING_README.md)** — Руководство по тестированию.

### 🟡 Справочная информация
*   **[CHANGELOG.md](../CHANGELOG.md)** — История всех изменений.
*   **[docs/BAT_FILES_GUIDE.md](BAT_FILES_GUIDE.md)** — Руководство по BAT файлам и скриптам.
*   **[CREATE_GIT_RELEASE.md](../CREATE_GIT_RELEASE.md)** — Создание релизов на GitHub.

---

## 📦 Ключевые компоненты

### 1. Модульная структура GUI
Проект использует модульную архитектуру для Modern Edition:
*   **Standard Edition (`app.py` + `bom_categorizer/gui.py`):** Классический интерфейс на Tkinter. Легкий, работает везде.
*   **Modern Edition (`app_qt.py` + `bom_categorizer/gui/`):** Современный модульный интерфейс на PySide6. Разделен на отдельные модули для лучшей поддерживаемости.

### 2. Централизованное управление версиями
Версии хранятся только в шаблонах (`config/*.template`). Утилита `tools/update_version.py` синхронизирует их по всему проекту.

### 3. База данных компонентов
Двухуровневая система хранения знаний о компонентах:
*   **Static:** Встроенная база из `data/component_database_template.json` (read-only).
*   **Dynamic:** Пользовательская база в `%APPDATA%` (накапливает опыт).

### 4. Организация по директориям
*   **`scripts/`** — Скрипты запуска и обслуживания для пользователей
*   **`tools/`** — Python утилиты для разработчиков и администрирования
*   **`deployment/`** — Скрипты сборки инсталляторов и релизов
*   **`config/`** — Конфигурационные файлы и шаблоны
*   **`data/`** — Шаблоны данных приложения

---

## 🔄 Рабочий процесс

### Для пользователей
1. **Установка:** Запустить инсталлятор или использовать `scripts/post_install.ps1`
2. **Запуск:** Использовать `scripts/run_app.bat` или ярлык из меню Пуск
3. **Управление БД:** `scripts/manage_database.bat`
4. **Резервное копирование:** `scripts/database_backup.bat`

### Для разработчиков
1. **Клонирование:** `git clone` + `python tools/init_project.py`
2. **Разработка:** Использовать `scripts/run_modern_debug.bat` или `scripts/run_standard_debug.bat`
3. **Тестирование:** `scripts/run_tests.bat`
4. **Обновление версии:** `python tools/update_version.py set modern 4.5.0`
5. **Сборка:** `python deployment/build_installer.py` (Windows) или `./deployment/build_macos.sh` (macOS)

---

## 🎯 Преимущества новой структуры

✅ **Четкое разделение ответственности:**
- Скрипты пользователя в `scripts/`
- Инструменты разработчика в `tools/`
- Конфигурация в `config/`
- Данные в `data/`

✅ **Модульный GUI:**
- `bom_categorizer/gui/` разделен на логические модули
- Легче поддерживать и расширять
- Четкое разделение ответственности между компонентами

✅ **Упрощенная навигация:**
- Меньше файлов в корне проекта
- Логическая группировка по назначению
- Проще найти нужный файл

✅ **Лучшая масштабируемость:**
- Легко добавлять новые скрипты и утилиты
- Простая интеграция новых модулей GUI
- Удобное управление конфигурацией

---

*Документ обновлен: 22.11.2025*  
*Версия документа: 2.0*  
*Автор: Куреин М.Н.*
