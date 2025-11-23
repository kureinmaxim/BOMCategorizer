# 📦 BOM Categorizer

**Автоматическая сортировка электронных компонентов из спецификаций (BOM) по категориям.**
Загружаете файл → Получаете Excel с разделением на: Резисторы, Конденсаторы, Микросхемы и др.

---

## ⚡️ Быстрая справка (Cheatsheet)

### 🚀 Запуск (Windows)
*   **Modern Edition (Красивый):** `scripts\run_modern_debug.bat` (или `python app_qt.py`)
*   **Standard Edition (Классика):** `scripts\run_standard_debug.bat` (или `python app.py`)

### 🚀 Запуск (macOS / Linux)
```bash
source venv/bin/activate
python3 app_qt.py
```

### 🛠 Установка (Первый раз)
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
*   **📂 Все форматы:** Читает Excel (.xlsx), Word (.doc/.docx), Text (.txt).
*   **🤖 Авто-сортировка:** 14 категорий (Резисторы, Конденсаторы, Микросхемы, Разъемы и др.).
*   **🧠 Умный парсинг:** Извлекает номиналы, допуски, корпуса и ТУ.
*   **💾 База данных:** Запоминает ваш выбор для будущих файлов.
*   **🖥️ Два интерфейса:** Современный (PySide6) и Классический (Tkinter).

---

## 📦 Версии приложения

| Версия | GUI | Описание | Статус |
|--------|-----|----------|--------|
| **Modern Edition** | PySide6 (Qt) | Современный дизайн, темная тема, анимации. **Рекомендуется.** | ✅ Stable |
| **Standard Edition** | Tkinter | Классический системный интерфейс. Легковесный. | ✅ Stable |

> **Примечание:** Обе версии используют одну и ту же базу данных и логику сортировки.

---

## 📖 Документация

*   **[🚀 Руководство по запуску (LAUNCHER_GUIDE.md)](LAUNCHER_GUIDE.md)** — подробнее о .bat файлах и запуске.
*   **[📦 Создание релиза (CREATE_GIT_RELEASE.md)](CREATE_GIT_RELEASE.md)** — инструкция для разработчиков по выпуску версий.
*   **[🛠 Настройка окружения (SETUP.md)](SETUP.md)** — полная инструкция по установке.
*   **[🤖 Интерактивный режим (docs/INTERACTIVE_MODE_GUIDE.md)](docs/INTERACTIVE_MODE_GUIDE.md)** — как обучать программу.

---

## 💻 CLI Режим (Командная строка)

Можно использовать без графического интерфейса для автоматизации:

```bash
# Обработать файл и создать Excel + TXT файлы по категориям
python tools/split_bom.py --inputs "bom.docx" --xlsx "result.xlsx" --txt-dir "result_txt" --combine
```

**Ключевые опции:**
*   `--inputs`: Входные файлы.
*   `--xlsx`: Имя выходного Excel файла.
*   `--txt-dir`: Папка для сохранения текстовых списков по категориям.
*   `--combine`: Добавить лист "SUMMARY" с общим списком.

---

## 🔧 Устранение проблем

| Проблема | Решение |
|----------|---------|
| **Module not found** | Не активировано виртуальное окружение или не установлены зависимости (`pip install -r ...`). |
| **Access Denied (PowerShell)** | Выполните `Set-ExecutionPolicy Bypass -Scope Process` перед активацией. |
| **Ошибка кодировки** | В Windows консоли используйте `chcp 65001` перед запуском, если есть проблемы с кириллицей. |

---

**Разработчик:** Куреин М.Н. | **Лицензия:** Proprietary
