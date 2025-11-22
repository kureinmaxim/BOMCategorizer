# 📁 Структура проекта BOM Categorizer

> **Версии:** Standard v3.3.0 (Tkinter) / Modern Edition v4.4.1 (PySide6)

## 🗂️ Организация файлов

### Корневая директория

```
ProjectSnabjenie/
├── 📄 README.md                          # Главная документация
├── 📄 BUILD.md                           # Инструкция по сборке
├── 📄 ANALYSIS_PROJECT.md                # Архитектура проекта
├── 📄 CHANGELOG.md                       # История изменений
│
├── 🚀 Точки входа:
│   ├── app.py                            # Standard Edition (Tkinter)
│   ├── app_qt.py                         # Modern Edition (PySide6)
│   ├── split_bom.py                      # CLI утилита
│   └── manage_database.py                # Управление БД
│
├── 📦 bom_categorizer/                   # Ядро (Бизнес-логика)
│   ├── main.py                           # Оркестратор
│   ├── classifiers.py                    # Логика классификации
│   ├── parsers.py                        # Парсеры (DOCX, XLSX, TXT)
│   ├── formatters.py                     # Форматирование и очистка
│   ├── component_database.py             # Управление базой знаний
│   ├── gui.py                            # GUI Standard
│   └── gui_qt.py                         # GUI Modern
│
├── ⚙️ Конфигурация:
│   ├── config.json.template              # Шаблон Standard
│   ├── config_qt.json.template           # Шаблон Modern
│   ├── rules.json                        # Правила классификации
│   └── requirements.txt                  # Зависимости
│
├── 🔧 Скрипты и утилиты:
│   ├── build_installer.py                # Сборка инсталлятора (Windows)
│   ├── build_macos.sh                    # Сборка DMG (macOS)
│   ├── update_version.py                 # Управление версиями
│   └── sync_installer_versions.py        # Синхронизация версий
│
└── 📚 docs/                              # Документация
    ├── QUICK_START.md                    # Быстрый старт
    ├── OFFLINE_INSTALLATION_GUIDE.md     # Офлайн установка
    ├── VERSION_MANAGEMENT.md             # Управление версиями
    └── ...
```

---

## 📚 Путеводитель по документации

### 🟢 Для пользователей
*   **[README.md](../README.md)** — Главная страница, обзор возможностей.
*   **[docs/QUICK_START.md](QUICK_START.md)** — Подробное руководство для начала работы.
*   **[docs/OFFLINE_INSTALLATION_GUIDE.md](OFFLINE_INSTALLATION_GUIDE.md)** — Как установить без интернета.

### 🔵 Для разработчиков
*   **[ANALYSIS_PROJECT.md](../ANALYSIS_PROJECT.md)** — Архитектура, описание модулей и технологий.
*   **[BUILD.md](../BUILD.md)** — Как собрать инсталлятор (Windows/macOS).
*   **[docs/VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md)** — Как обновлять версии и делать релизы.

### 🟡 Справочная информация
*   **[CHANGELOG.md](../CHANGELOG.md)** — История всех изменений.
*   **[docs/PLATFORM_COMPARISON.md](PLATFORM_COMPARISON.md)** — Различия между Windows и macOS версиями.

---

## 📦 Ключевые компоненты

### 1. Две версии GUI
Проект содержит два независимых интерфейса, использующих общее ядро:
*   **Standard Edition (`app.py`):** Классический интерфейс на Tkinter. Легкий, работает везде.
*   **Modern Edition (`app_qt.py`):** Современный интерфейс на PySide6. Поддерживает темы, анимации, Drag&Drop.

### 2. Централизованное управление версиями
Версии хранятся только в шаблонах (`.template`). Утилита `update_version.py` синхронизирует их по всему проекту.

### 3. База данных компонентов
Двухуровневая система хранения знаний о компонентах:
*   **Static:** Встроенная база (read-only).
*   **Dynamic:** Пользовательская база в `%APPDATA%` (накапливает опыт).

---

*Документ обновлен: 16.11.2025*
