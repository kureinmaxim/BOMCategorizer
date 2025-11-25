# 🖥️ Использование CLI (командная строка) v1.9.0

## 📋 Содержание

1. [Интерактивный CLI режим](#-интерактивный-cli-режим-в-приложении)
2. [Обработка BOM файлов](#-обработка-bom-файлов-split_bompy)
3. [AI поиск компонентов](#-ai-поиск-компонентов-ai_searchpy)
4. [Управление версиями](#-управление-версиями-update_versionpy)
5. [Синхронизация API](#-синхронизация-api-ключа-telegramhelper)
6. [Решение проблем](#-решение-проблем)

---

## 💻 Интерактивный CLI режим (в приложении)

Встроенная командная строка доступна через кнопку **💻 CLI** в интерфейсе приложения.

### Возможности

- 🔄 **Автодополнение команд** (Tab)
- 📜 **История команд** (↑↓)
- 🎨 **Цветной вывод**
- ⚡ **Быстрый доступ ко всем функциям**

### Все доступные команды

#### 🔹 Общие команды

| Команда | Алиас | Описание |
|---------|-------|----------|
| `help` | `?` | Показать список всех команд |
| `help <cmd>` | | Подробная справка по команде |
| `clear` | `cls` | Очистить экран консоли |
| `exit` | `quit` | Закрыть CLI консоль |
| `history` | | Показать историю команд (последние 20) |

#### 🔹 Команды работы с файлами

| Команда | Алиас | Описание |
|---------|-------|----------|
| `list` | `ls` | Показать список входных файлов |
| `add <путь>` | | Добавить файл в список обработки |
| `remove <индекс\|путь>` | `rm` | Удалить файл из списка |
| `process` | `run` | Запустить обработку всех файлов |

#### 🔹 Команды базы данных

| Команда | Алиас | Описание |
|---------|-------|----------|
| `dbstats` | | Статистика базы данных |
| `dbsearch <название>` | `search` | Поиск компонента в БД |
| `dbexport` | | Экспорт БД в Excel |
| `dbbackup` | | Создать резервную копию БД |

#### 🔹 Системные команды

| Команда | Алиас | Описание |
|---------|-------|----------|
| `status` | | Показать статус приложения |
| `config` | | Показать всю конфигурацию |
| `config <param>` | | Показать конкретный параметр |
| `theme [dark\|light]` | | Переключить/показать тему |
| `scale <0.7-1.25>` | | Изменить масштаб интерфейса |

#### 🔹 Команды синхронизации (НОВОЕ!)

| Команда | Алиас | Описание |
|---------|-------|----------|
| `version` | `ver` | Показать текущие версии |
| `vsync` | | Синхронизировать версии из шаблонов |
| `vset <X.Y.Z>` | | Установить новую версию Modern Edition |
| `api` | | Показать настройки Telegram API |
| `apisync` | | Получить API ключ с сервера |
| `apitest` | | Проверить подключение к API |

### Примеры использования

```
>>> help
📚 Доступные команды:
============================================================

🔹 Общие:
  • help (?) - Показывает список всех доступных команд
  • clear (cls) - Очищает экран консоли
  ...

>>> list
📁 Входные файлы:
  1. БЗ_Плата.xlsx (x1)
     /Users/user/Documents/БЗ_Плата.xlsx

>>> add /path/to/file.xlsx
✅ Файл добавлен: file.xlsx

>>> dbsearch LM358
🔍 Результаты поиска 'LM358':
==================================================
1. LM358 - Микросхемы
2. LM358N - Микросхемы
...

>>> status
📋 Статус приложения:
==================================================
Версия: 4.5.0
Тема: dark
Масштаб: 100%
Режим работы: expert
Входных файлов: 3
База данных: подключена

>>> process
🚀 Запущена обработка 3 файлов...

>>> version
📋 Версии приложения:
==================================================
Текущая версия: 4.5.0
Edition: Modern Edition
Дата релиза: 25.11.2025
...

>>> vset 4.6.0
✅ Версия обновлена до 4.6.0

>>> api
🔐 Настройки Telegram API:
==================================================
URL: http://138.124.19.67:8000/ai_query
Key: 754c7afb2b146882...
Длина ключа: 64 символов

>>> apisync
🔄 Подключение к серверу...
✅ API ключ синхронизирован!

>>> apitest
🔄 Проверка http://138.124.19.67:8000/health...
✅ API доступен!
Статус: 200
```

### Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| `Enter` | Выполнить команду |
| `↑` / `↓` | Навигация по истории |
| `Tab` | Автодополнение |
| `Esc` | Закрыть CLI (в некоторых режимах) |

---

## 📦 Обработка BOM файлов (split_bom.py)

### ❌ Частая ошибка

**НЕ правильно:**
```bash
split_bom --inputs file.xlsx  # Ошибка: команда не найдена
```

## ✅ Правильные способы запуска

### Windows (с активированным venv):
```powershell
# 1. Активировать окружение
.\.venv\Scripts\Activate.ps1

# 2. Запустить скрипт
python split_bom.py --inputs D:/path/to/file.xlsx --xlsx output.xlsx
```

### Windows (без активации venv):
```powershell
# Прямой запуск через venv Python
.\.venv\Scripts\python.exe split_bom.py --inputs D:/path/to/file.xlsx --xlsx output.xlsx --txt-dir D:/output --combine
```

### macOS/Linux:
```bash
# С активацией
source venv/bin/activate
python3 split_bom.py --inputs file.xlsx --xlsx output.xlsx

# Без активации
venv/bin/python3 split_bom.py --inputs file.xlsx --xlsx output.xlsx
```

---

## 📋 Пример команды

### Ваш случай (исправленная команда):

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "D:/!ШСК_М/Project/Plata_Preobrz.xlsx" `
  --xlsx "D:/!ШСК_М/Project/categorized.xlsx" `
  --txt-dir "D:/!ШСК_М/Project/1_txt" `
  --combine
```

или с активированным окружением:

```powershell
# Активировать
.\.venv\Scripts\Activate.ps1

# Запустить
python split_bom.py `
  --inputs "D:/!ШСК_М/Project/Plata_Preobrz.xlsx" `
  --xlsx "D:/!ШСК_М/Project/categorized.xlsx" `
  --txt-dir "D:/!ШСК_М/Project/1_txt" `
  --combine
```

---

## 🎯 Все опции CLI

```
python split_bom.py [опции]

Обязательные:
  --inputs FILE [FILE ...]    Входные файлы (XLSX/DOCX/DOC/TXT)
  --xlsx OUTPUT.xlsx          Выходной Excel файл

Опциональные:
  --sheets N[,M,...]          Номера листов XLSX (например: 3,4)
  --txt-dir PATH              Папка для TXT файлов по категориям
  --combine                   Добавить лист SUMMARY с суммарными данными
  --merge-into SHEET          Имя листа для объединения (по умолчанию: categorized)
  --loose                     Разрешить свободный формат текста
  --assign-json rules.json    Файл с правилами автоклассификации
  --interactive               Интерактивная классификация в консоли
  --no-interactive            Отключить автоматический интерактивный режим
```

> 💡 **Совет:** Для интерактивной классификации используйте GUI (`app.py`) - там удобный визуальный интерфейс!

---

## 📝 Примеры использования

### 1. Простая обработка одного файла:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "example/БЗ.doc" `
  --xlsx "output.xlsx"
```

### 2. Несколько файлов с суммарными данными:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "file1.xlsx" "file2.doc" "file3.txt" `
  --xlsx "combined.xlsx" `
  --combine
```

### 3. С экспортом в TXT:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "БЗ.doc" `
  --xlsx "output.xlsx" `
  --txt-dir "output_txt" `
  --combine
```

### 4. Выбор конкретных листов из Excel:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "workbook.xlsx" `
  --sheets 3,4,5 `
  --xlsx "output.xlsx"
```

### 5. С автоклассификацией по правилам:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "БЗ.doc" `
  --xlsx "output.xlsx" `
  --assign-json rules.json `
  --combine
```

---

## 🤖 AI поиск компонентов (ai_search.py)

Поиск информации о компонентах через AI (Telegram Bot API, Anthropic, OpenAI).

### Быстрый старт

```bash
# macOS/Linux
source venv/bin/activate
python3 tools/ai_search.py "TPS54302"

# Windows
.\.venv\Scripts\python.exe tools\ai_search.py "TPS54302"
```

### Все опции

```
python tools/ai_search.py [компонент] [опции]

Аргументы:
  компонент               Название компонента для поиска

Опции:
  --provider, -p          AI провайдер: telegram, anthropic, openai
                          (по умолчанию: telegram)
  --prompt, -t            Тип промпта: info, ivp_short, ivp_full, analogs, compare
                          (по умолчанию: info)
  --list-prompts, -l      Показать все доступные типы промптов
  --raw, -r               Использовать текст как сырой промпт
  --output, -o FILE       Сохранить результат в файл
  --json, -j              Вывод в формате JSON
```

### Типы промптов

| Тип | Описание |
|-----|----------|
| `info` | Общая информация о компоненте |
| `ivp_short` | Краткое описание ИВП (150-200 слов) |
| `ivp_full` | Полное описание ИВП (200-400 слов) |
| `analogs` | Поиск аналогов (pin-to-pin, функциональные, бюджетные) |
| `compare` | Сравнительный анализ с конкурентами |

### Примеры использования

#### 1. Простой поиск информации:
```bash
python3 tools/ai_search.py "LM2596"
```

#### 2. Поиск аналогов:
```bash
python3 tools/ai_search.py "STM32F103" --prompt analogs
```

#### 3. Краткое описание ИВП для документации:
```bash
python3 tools/ai_search.py "TPS54302DDCR" --prompt ivp_short
```

#### 4. Использование Anthropic напрямую:
```bash
python3 tools/ai_search.py "LM358" --provider anthropic
```

#### 5. Сохранение результата в файл:
```bash
python3 tools/ai_search.py "MAX232" --output info_max232.txt
```

#### 6. JSON вывод для скриптов:
```bash
python3 tools/ai_search.py "NE555" --json > result.json
```

#### 7. Свой промпт:
```bash
python3 tools/ai_search.py "Какие есть DC-DC преобразователи с Vin 12V, Vout 5V, Iout 3A?" --raw
```

### Настройка

Для работы AI поиска нужно настроить ключи в `config_qt.json`:

```json
{
  "api_keys": {
    "telegram_url": "http://ВАШ_СЕРВЕР:8000/ai_query",
    "telegram_key": "ваш_ключ_из_команды_/api",
    "anthropic": "sk-ant-...",
    "openai": "sk-proj-..."
  }
}
```

> 💡 **Совет:** Используйте провайдер `telegram` — не нужны собственные ключи Anthropic/OpenAI!

---

## 🔧 Управление версиями (update_version.py)

Центральная утилита для управления версиями проекта. Единственный источник правды — шаблоны config.

### Быстрый старт

```bash
# Показать текущие версии во всех файлах
python tools/update_version.py status

# Синхронизировать все файлы с шаблонами
python tools/update_version.py sync
```

### Все команды

| Команда | Описание |
|---------|----------|
| `status` | Показать текущие версии (шаблоны, локальные, установленные) |
| `set standard X.X.X` | Обновить версию Standard Edition |
| `set modern X.X.X` | Обновить версию Modern Edition |
| `set both X.X.X` | Обновить обе версии одновременно |
| `sync` | Синхронизировать все файлы с шаблонами |

### Примеры использования

#### 1. Проверить текущие версии:
```bash
python tools/update_version.py status
```

Вывод покажет:
- Версии в шаблонах (`config.json.template`, `config_qt.json.template`)
- Версии в локальных файлах (`config.json`, `config_qt.json`)
- Версии в установленном приложении (User config)
- Предупреждения о расхождениях

#### 2. Обновить версию Modern Edition:
```bash
python tools/update_version.py set modern 4.6.0
```

Автоматически обновит:
- `config/config_qt.json.template` (шаблон)
- `config_qt.json` (локальный)
- `deployment/installer_qt.iss` (установщик Windows)
- Захардкоженные версии в Python файлах

#### 3. Синхронизировать после ручных изменений:
```bash
python tools/update_version.py sync
```

### Рабочий процесс релиза

```bash
# 1. Обновить версию
python tools/update_version.py set modern 4.6.0

# 2. Проверить статус
python tools/update_version.py status

# 3. Собрать приложение
# macOS:
./deployment/build_macos.sh

# Windows:
python deployment/build_installer.py
```

### Архитектура версий

```
config/config_qt.json.template  ← ИСТОЧНИК ПРАВДЫ
        ↓
   sync / set
        ↓
┌───────────────────────────────────────────────┐
│ config_qt.json (локальный)                    │
│ deployment/installer_qt.iss                   │
│ bom_categorizer/gui_qt.py (fallback)          │
│ bom_categorizer/config_manager.py (default)   │
│ ~/Library/.../config_qt.json (user config)    │
└───────────────────────────────────────────────┘
```

---

## 🔄 Синхронизация API ключа TelegramHelper

### Ошибка: "wrong # args: should be .!frame.!text insert..."
**Причина:** Запущен неправильный скрипт (возможно, app.py вместо split_bom.py)

**Решение:** Используйте полный путь:
```powershell
.\.venv\Scripts\python.exe split_bom.py --inputs file.xlsx --xlsx output.xlsx
```

### Ошибка: "python не является внутренней командой"
**Причина:** Python не в PATH или venv не активирован

**Решение:** Используйте полный путь к python.exe:
```powershell
.\.venv\Scripts\python.exe split_bom.py ...
```

### Ошибка: "ModuleNotFoundError: No module named 'pandas'"
**Причина:** Зависимости не установлены или venv не активирован

**Решение:**
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

---

## 🔄 Синхронизация API ключа TelegramHelper

Скрипт `tools/sync_telegram_api.py` автоматически синхронизирует API ключ между сервером TelegramHelper и BOMCategorizer.

### Быстрый старт

```bash
# Получить ключ с сервера и синхронизировать
python tools/sync_telegram_api.py --fetch

# Показать текущие настройки
python tools/sync_telegram_api.py --show
```

### Все опции

| Опция | Описание |
|-------|----------|
| (без опций) | Интерактивный режим |
| `--fetch` | Получить ключ с сервера через SSH |
| `--key KEY` | Установить конкретный ключ вручную |
| `--show` | Показать текущие настройки API |
| `--test` | Проверить подключение к API |

### Примеры использования

#### 1. Получить ключ с сервера:
```bash
python tools/sync_telegram_api.py --fetch
```

Скрипт подключится к серверу через SSH и получит `API_SECRET_KEY` из `.env`.

#### 2. Показать текущие настройки:
```bash
python tools/sync_telegram_api.py --show
```

Вывод:
```
📋 Текущие настройки API

📁 Проект: /path/to/BOMCategorizer/config_qt.json
   URL: http://138.124.19.67:8000/ai_query
   Key: 754c7afb2b14...

📁 Установленное приложение: ~/Library/.../config_qt.json
   URL: http://138.124.19.67:8000/ai_query
   Key: 754c7afb2b14...
```

#### 3. Установить ключ вручную:
```bash
python tools/sync_telegram_api.py --key "ваш_api_ключ_из_команды_/api"
```

#### 4. Проверить работу API:
```bash
python tools/sync_telegram_api.py --test
```

### Что обновляет скрипт

```
Сервер TelegramHelper
  └── .env (API_SECRET_KEY)
        │
        ▼ --fetch
┌────────────────────────────────────────────────────┐
│ config_qt.json (проект)                            │
│ ~/Library/.../BOMCategorizerModern/config_qt.json │
└────────────────────────────────────────────────────┘
```

### Конфигурация сервера

```
SERVER_SSH = "root@138.124.19.67"
SERVER_PORT = "22542"
API_URL = "http://138.124.19.67:8000/ai_query"
```

### Альтернативный способ

Если SSH недоступен, получите ключ через Telegram:
1. Отправьте команду `/api` боту (только для админа)
2. Скопируйте ключ
3. Установите вручную:
```bash
python tools/sync_telegram_api.py --key "скопированный_ключ"
```

После синхронизации перезапустите BOMCategorizer.

---

## 💡 Советы

1. **Используйте обратные кавычки `` ` `` в PowerShell** для многострочных команд
2. **Заключайте пути с пробелами в кавычки**: `"D:/My Files/file.xlsx"`
3. **Проверяйте пути**: используйте `Test-Path "путь"` для проверки существования файла
4. **Относительные пути**: работают относительно текущей директории в терминале

---

## 📊 Сводка всех CLI команд

### Внешние скрипты (терминал)

| Скрипт | Назначение | Пример |
|--------|------------|--------|
| `split_bom.py` | Обработка BOM файлов | `python split_bom.py --inputs file.xlsx --xlsx out.xlsx` |
| `tools/ai_search.py` | AI поиск компонентов | `python tools/ai_search.py "TPS54302"` |
| `tools/update_version.py` | Управление версиями | `python tools/update_version.py status` |
| `tools/sync_telegram_api.py` | Синхронизация API | `python tools/sync_telegram_api.py --fetch` |
| `tools/sync_installer_versions.py` | Синхронизация .iss | `python tools/sync_installer_versions.py` |

### Встроенный CLI (в приложении, кнопка 💻 CLI)

| Команда | Описание |
|---------|----------|
| `help` | Список всех команд |
| `list` / `ls` | Показать входные файлы |
| `add <путь>` | Добавить файл |
| `process` / `run` | Запустить обработку |
| `dbstats` | Статистика БД |
| `dbsearch <название>` | Поиск в БД |
| `status` | Статус приложения |
| `config` | Конфигурация |
| **`version`** | **Показать версии** |
| **`vsync`** | **Синхронизировать версии** |
| **`vset <X.Y.Z>`** | **Установить версию** |
| **`api`** | **Показать API настройки** |
| **`apisync`** | **Синхронизировать API с сервера** |
| **`apitest`** | **Проверить API подключение** |

### Типичный рабочий процесс разработки

```bash
# 1. Проверить текущее состояние
python tools/update_version.py status

# 2. Синхронизировать API ключи (если нужно)
python tools/sync_telegram_api.py --show
python tools/sync_telegram_api.py --fetch

# 3. Перед релизом обновить версию
python tools/update_version.py set modern 4.6.0

# 4. Собрать приложение
./deployment/build_macos.sh
```

---

*Создано: 06.10.2025 | Обновлено: 25.11.2025*

