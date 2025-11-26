# 🚀 Настройка проекта после клонирования с GitHub

Этот файл содержит инструкции по первоначальной настройке проекта **BOM Categorizer** после клонирования с GitHub.

**Версии:** Standard 3.3.0 | Modern 4.5.1

---

## 📋 Что происходит при клонировании

При клонировании репозитория с GitHub вы получаете:

✅ **Есть в репозитории:**
- Исходный код (Python модули)
- Template файлы конфигурации в `config/`:
  - `config/config.json.template` (Standard Edition)
  - `config/config_qt.json.template` (Modern Edition)
- Шаблон базы данных: `data/component_database_template.json`
- Документация в `docs/`
- Скрипты сборки в `deployment/`, утилиты в `tools/`, скрипты запуска в `scripts/`

❌ **НЕТ в репозитории** (они в `.gitignore`):
- `config.json` - локальный config Standard Edition
- `config_qt.json` - локальный config Modern Edition
- `venv/` или `.venv/` - виртуальное окружение Python
- `component_database.json` - ваша персональная база данных компонентов
- `*.exe`, `*.dmg` - установочные файлы

---

## 🔧 Быстрая настройка (автоматически)

### Шаг 1: Клонируйте репозиторий

```bash
git clone https://github.com/kureinmaxim/BOMCategorizer.git
cd BOMCategorizer
```

### Шаг 2: Запустите скрипт инициализации

**Windows:**
```powershell
python tools/init_project.py
```

**macOS/Linux:**
```bash
python3 tools/init_project.py
```

**Что делает скрипт:**
1. ✅ Создает `config.json` из `config/config.json.template`
2. ✅ Создает `config_qt.json` из `config/config_qt.json.template`
3. ✅ Проверяет наличие виртуального окружения
4. ✅ Показывает инструкции по дальнейшим действиям

### Шаг 3: Создайте виртуальное окружение

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Шаг 4: Установите зависимости

```bash
pip install -r requirements.txt
```

### Шаг 5: Запустите приложение

**Standard Edition (Tkinter):**
```bash
python app.py
```

**Modern Edition (PySide6):**
```bash
python app_qt.py
```

---

## 🛠️ Ручная настройка (если скрипт не работает)

### 1. Создайте config файлы вручную

**Windows PowerShell:**
```powershell
# Standard Edition
Copy-Item config/config.json.template config.json

# Modern Edition
Copy-Item config/config_qt.json.template config_qt.json
```

**macOS/Linux (bash):**
```bash
# Standard Edition
cp config/config.json.template config.json

# Modern Edition
cp config/config_qt.json.template config_qt.json
```

### 2. Создайте виртуальное окружение

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Проверьте версии

```bash
python tools/update_version.py status
```

Должно показать:
```
Standard Edition: v3.3.0
Modern Edition: v4.5.1
```

---

## 📂 Структура config файлов

### `config.json` (Standard Edition)

```json
{
  "app_info": {
    "version": "3.3.0",
    "edition": "Standard",
    "release_date": "11.11.2025"
  },
  "security": {
    "pin": "1234",
    "require_pin": true
  },
  "window": {
    "width": 750,
    "height": 1110,
    "remember_size": true
  }
}
```

### `config_qt.json` (Modern Edition)

```json
{
  "app_info": {
    "version": "4.5.1",
    "edition": "Modern Edition",
    "release_date": "26.11.2025"
  },
  "security": {
    "pin": "1234",
    "require_pin": true
  },
  "window": {
    "remember_size": true,
    "sizes_by_mode": {
      "simple": {"width": 730, "height": 560},
      "advanced": {"width": 730, "height": 790},
      "expert": {"width": 730, "height": 1160}
    }
  },
  "ui": {
    "theme": "dark",
    "scale_factor": 1.0,
    "view_mode": "simple"
  },
  "api_keys": {
    "telegram_url": "http://YOUR_SERVER:8000/ai_query",
    "telegram_key": "",
    "anthropic": "",
    "openai": ""
  },
  "ai_provider": "telegram",
  "pdf_search": {
    "custom_directories": []
  }
}
```

**Важно:** Файлы `config.json` и `config_qt.json` находятся в `.gitignore` и не попадают в Git. Это сделано специально, чтобы сохранить ваши персональные настройки (PIN, размеры окна, тему, API ключи и т.д.)

---

## 🔄 Синхронизация версий

После обновления проекта (git pull) синхронизируйте версии:

```bash
python tools/update_version.py sync
```

**Что делает sync:**
- ✅ Обновляет версию в локальных config файлах
- ✅ Синхронизирует файлы сборки (.iss)
- ✅ Обновляет захардкоженные версии в Python коде
- ⚠️ **НЕ затрагивает** ваши персональные настройки (theme, scale_factor, window sizes)

---

## 🤖 Настройка AI интеграции

Modern Edition поддерживает AI поиск информации о компонентах. 

### Способ 1: Через Telegram Bot (рекомендуется)

Не требует собственных API ключей Anthropic/OpenAI!

1. **Получите API ключ:**
   - Отправьте команду `/api` боту в Telegram (только для админа)
   - Скопируйте URL и Key

2. **Синхронизируйте ключ:**
   ```bash
   # Автоматически с сервера
   python tools/sync_telegram_api.py --fetch
   
   # Или вручную
   python tools/sync_telegram_api.py --key "ваш_ключ"
   ```

3. **Проверьте подключение:**
   ```bash
   python tools/sync_telegram_api.py --test
   ```

### Способ 2: Напрямую через Anthropic/OpenAI

Если у вас есть собственные API ключи:

1. Откройте `config_qt.json`
2. Добавьте ключи в секцию `api_keys`:
   ```json
   {
     "api_keys": {
       "anthropic": "sk-ant-api03-...",
       "openai": "sk-proj-..."
     }
   }
   ```

### Встроенные CLI команды для AI

В интерактивном CLI (кнопка 💻 CLI):

| Команда | Описание |
|---------|----------|
| `ai` | Показать все настройки AI |
| `aiprovider anthropic` | Сменить провайдера |
| `aimodel claude-opus-4-5-20251101` | Сменить модель |
| `aimodels` | Список доступных моделей |
| `apitest` | Проверить подключение |

> 📖 Подробнее: `docs/AI_INTEGRATION_GUIDE.md`

---

## 🗄️ База данных компонентов

После первого запуска приложение создаст:

**Standard Edition:**
```
%APPDATA%\BOMCategorizer\Data\component_database.json
```

**Modern Edition:**
```
%APPDATA%\BOMCategorizerModern\Data\component_database.json
```

**Важно:** 
- База данных **НЕ в Git** (в `.gitignore`)
- Каждая установка имеет свою локальную базу
- Базы можно экспортировать/импортировать через GUI

---

## 🧪 Проверка установки

### 1. Проверьте что config файлы созданы:

```powershell
# Windows PowerShell
Test-Path config.json
Test-Path config_qt.json
```

```bash
# macOS/Linux
ls -la config.json config_qt.json
```

### 2. Проверьте версии:

```bash
python tools/update_version.py status
```

### 3. Запустите тесты (опционально):

```bash
pytest tests/
```

---

## ❓ FAQ

### Q: Почему нет `config.json` и `config_qt.json` в Git?

**A:** Эти файлы содержат локальные настройки пользователя (PIN, тему, размеры окна). Если бы они были в Git, при каждом `git pull` ваши персональные настройки перезаписывались бы. Вместо этого мы используем template файлы.

### Q: Что делать если забыл запустить `init_project.py`?

**A:** Ничего страшного! Приложение создаст config автоматически при первом запуске с настройками по умолчанию. Но лучше запустить скрипт, чтобы получить актуальную версию из template.

### Q: Можно ли вручную изменить config файлы?

**A:** Да! `config.json` и `config_qt.json` — это обычные JSON файлы. Вы можете редактировать их в любом текстовом редакторе. Но будьте осторожны с синтаксисом JSON.

### Q: Что делать после `git pull`?

**A:** Запустите `python tools/update_version.py sync` для синхронизации версий. Скрипт обновит только секцию `app_info`, сохранив ваши персональные настройки.

### Q: Как обновить структуру config при добавлении новых полей?

**A:** Вручную добавьте новые поля из `config_qt.json.template` в ваш локальный `config_qt.json`. Или удалите локальный config и создайте заново из template.

---

## 📚 Дополнительная информация

| Документ | Описание |
|----------|----------|
| `BUILD.md` | Сборка инсталлятора |
| `ANALYSIS_PROJECT.md` | Структура проекта |
| `CHANGELOG.md` | История изменений |
| `docs/CLI_USAGE.md` | Использование CLI |
| `docs/AI_INTEGRATION_GUIDE.md` | Настройка AI интеграции |
| `docs/API_MANAGEMENT.md` | Управление API ключами |

### Полезные команды

```bash
# Проверить версии
python tools/update_version.py status

# Синхронизировать версии
python tools/update_version.py sync

# Синхронизировать API ключ
python tools/sync_telegram_api.py --fetch

# AI поиск компонента
python tools/ai_search.py "TPS54302"
```

---

**Дата создания:** 20.11.2025  
**Обновлено:** 26.11.2025  
**Автор:** Куреин М.Н. / Kurein M.N.  
**Версия документа:** 1.1

