# Управление версиями проекта BOM Categorizer

## 📋 Содержание

1. [Обзор системы](#обзор-системы)
2. [Схема версионирования](#схема-версионирования)
3. [Источник правды](#источник-правды)
4. [Инструмент bump_version.py](#инструмент-bump_versionpy)
5. [Инструмент update_version.py](#инструмент-update_versionpy)
6. [Создание локальных config файлов](#создание-локальных-config-файлов)
7. [Синхронизация файлов сборки](#синхронизация-файлов-сборки)
8. [Чек-лист релиза](#чек-лист-релиза)
9. [Рабочие сценарии](#рабочие-сценарии)
10. [FAQ](#faq)

---

## Обзор системы

В проекте BOM Categorizer версии управляются **централизованно** через шаблоны конфигурационных файлов:

✅ **Единый источник правды** — версия хранится только в шаблонах  
✅ **Две редакции** — Modern Edition (v5+) и Standard Edition (v3)  
✅ **Автоматическая синхронизация** — скрипты сборки читают из шаблонов  
✅ **Защита локальных настроек** — рабочие config файлы в `.gitignore`  

---

## Схема версионирования

Используется [Semantic Versioning](https://semver.org/) в формате **MAJOR.MINOR.PATCH**:

| Часть | Когда увеличивать | Пример |
|-------|-------------------|--------|
| **MAJOR** | Критические изменения, новая редакция | `4.5.2` → `5.0.0` |
| **MINOR** | Новые функции (обратная совместимость) | `5.0.0` → `5.1.0` |
| **PATCH** | Исправление ошибок | `5.1.0` → `5.1.1` |

**Текущие версии:**
- **Modern Edition** — v5.x.x (PySide6, актуальная)
- **Standard Edition** — v3.x.x (Tkinter, legacy)

---

## Источник правды

### Где хранятся версии

```
config/config_qt.json.template   → Modern Edition (PySide6) — ОСНОВНАЯ
config/config.json.template      → Standard Edition (Tkinter)
```

Эти файлы:
- ✅ Хранятся в Git
- ✅ Используются всеми скриптами сборки
- ✅ Содержат версию, дату релиза, имя разработчика

### Ключевые поля (секция `app_info`)

```json
{
  "app_info": {
    "version": "5.0.0",
    "release_date": "28.11.2025",
    "last_updated": "2025-11-28",
    "developer": "Куреин М.Н."
  }
}
```

### Что НЕ является источником правды

❌ `config.json` — локальный файл (не в Git)  
❌ `config_qt.json` — локальный файл (не в Git)  
❌ `installer_qt.iss` — генерируется автоматически  

---

## Инструмент bump_version.py

Основной скрипт для управления версиями. **По умолчанию обновляет только Modern Edition**.

### Расположение
```
scripts/bump_version.py
```

### Основные команды

> Все команды работают одинаково на Windows, macOS и Linux.
> ⚠️ **macOS/Linux:** Используйте `python3` вместо `python`.

#### 🐛 Исправление бага (Patch)
```bash
python3 scripts/bump_version.py --bump patch
# 5.0.0 → 5.0.1
```

#### ✨ Новая функция (Minor)
```bash
python3 scripts/bump_version.py --bump minor
# 5.0.0 → 5.1.0
```

#### 💥 Критические изменения (Major)
```bash
python3 scripts/bump_version.py --bump major
# 5.0.0 → 6.0.0
```

### Выбор редакции

```bash
# Modern Edition (по умолчанию)
python3 scripts/bump_version.py --bump patch

# Standard Edition
python3 scripts/bump_version.py --bump patch --edition standard

# Обе редакции
python3 scripts/bump_version.py --bump patch --edition both
```

### Установка конкретной версии

```bash
# Modern Edition
python3 scripts/bump_version.py --version 5.2.0

# Standard Edition
python3 scripts/bump_version.py --version 3.4.0 --edition standard
```

### Дополнительные опции

```bash
# Без обновления даты релиза
python3 scripts/bump_version.py --bump patch --no-release-date

# С конкретной датой релиза
python3 scripts/bump_version.py --version 5.5.0 --release-date 31.12.2025

# Изменить разработчика
python3 scripts/bump_version.py --developer "Иванов И.И."

# Тестовый запуск (без записи)
python3 scripts/bump_version.py --bump patch --dry-run
```

---

## Инструмент update_version.py

Альтернативный инструмент с расширенными возможностями.

### Расположение
```
tools/update_version.py
```

### Команды

```bash
# Показать текущие версии
python3 tools/update_version.py status

# Обновить Modern Edition
python3 tools/update_version.py set modern 5.1.0

# Обновить Standard Edition
python3 tools/update_version.py set standard 3.4.0

# Обновить обе редакции
python3 tools/update_version.py set both 5.0.0

# Синхронизировать файлы сборки
python3 tools/update_version.py sync
```

### Пример вывода `status`

```
[STATUS] ТЕКУЩИЕ ВЕРСИИ

ℹ️ Modern Edition (PySide6)
  Шаблон:
    Версия:      5.0.0
    Дата релиза: 28.11.2025
  Локальный:
    Версия:      5.0.0
    ✅ Синхронизировано

ℹ️ Standard Edition (Tkinter)
  Шаблон:
    Версия:      3.3.0
```

---

## Создание локальных config файлов

Локальные `config.json` и `config_qt.json` **не хранятся в Git**. Они создаются из шаблонов.

### Автоматически при запуске

```bash
python3 app_qt.py    # Создаст config_qt.json из шаблона
python3 app.py       # Создаст config.json из шаблона
```

### Вручную

```bash
# Windows (PowerShell)
Copy-Item config/config_qt.json.template config_qt.json

# macOS / Linux
cp config/config_qt.json.template config_qt.json
```

### Разделение настроек

| Параметр | Где хранится | Кто управляет |
|----------|--------------|---------------|
| version, release_date | `*.template` | Разработчик (Git) |
| scale_factor, theme | локальный `*.json` | Пользователь |
| window width/height | локальный `*.json` | Пользователь |

---

## Синхронизация файлов сборки

### Что синхронизируется

| Файл/Секция | Как синхронизируется |
|-------------|---------------------|
| `config_qt.json` (секция `app_info`) | `update_version.py sync` |
| `config_qt.json` (APP_ID в `telegram_security` и `api_keys`) | `update_version.py sync` |
| `bom_categorizer/gui_qt.py` (захардкоженная версия) | `update_version.py sync` |
| `bom_categorizer/config_manager.py` (захардкоженная версия) | `update_version.py sync` |
| `installer_qt.iss` | `sync_installer_versions.py` (вызывается из `sync`) |
| `build_macos.sh` | Читает из шаблона автоматически |

### Команда синхронизации

```bash
python3 tools/update_version.py sync
```

**Что делает:**
1. ✅ Синхронизирует секцию `app_info` в локальных config с шаблонами (версия, дата релиза, разработчик)
2. ✅ Синхронизирует `APP_ID` в секциях `telegram_security` и `api_keys` между шаблоном и локальным config
3. ✅ Синхронизирует захардкоженные версии в Python файлах (`gui_qt.py`, `config_manager.py`)
4. ✅ Синхронизирует `.iss` файлы с шаблонами
5. ✅ **Сохраняет** личные настройки (scale_factor, window size, theme, api_keys и т.д.)

---

## Чек-лист релиза

### Modern Edition

```bash
# 1. Обновить версию
python3 scripts/bump_version.py --bump minor

# 2. Синхронизировать файлы сборки
python3 tools/update_version.py sync

# 3. Проверить
python3 tools/update_version.py status

# 4. Закоммитить
git add config/ deployment/
git commit -m "Release: Modern Edition v5.1.0"

# 5. Создать тег (опционально)
git tag v5.1.0

# 6. Собрать инсталлятор
# Windows:
python deployment/build_installer.py

# macOS:
./deployment/build_macos.sh
```

### Standard Edition (если нужно)

```bash
python3 scripts/bump_version.py --bump patch --edition standard
```

### Синхронизация APP_ID с TelegramHelper

При обновлении MAJOR версии (например, с v5 на v6) необходимо обновить `APP_ID` в шаблоне и синхронизировать его с сервером TelegramHelper.

> [!NOTE]
> Команда `update_version.py sync` автоматически синхронизирует `APP_ID` из шаблона в локальный config. Но если вы изменили `APP_ID` в шаблоне (например, с `bomcategorizer-v5` на `bomcategorizer-v6`), необходимо также обновить его на сервере TelegramHelper.

#### Шаг 1: Обновить APP_ID в BOMCategorizer

```bash
# Вручную отредактировать config/config_qt.json.template
# Изменить в секции "telegram_security":
"app_id": "bomcategorizer-v6"

# Или в секции "api_keys" (для совместимости):
"app_id": "bomcategorizer-v6"

# Проверить синхронизацию
python3 tools/update_version.py status

# Синхронизировать локальный config с шаблоном (APP_ID будет синхронизирован автоматически)
python3 tools/update_version.py sync
```

> [!NOTE]
> Команда `sync` автоматически синхронизирует `APP_ID` из шаблона в локальный config в обеих секциях (`telegram_security` и `api_keys`).

> [!NOTE]
> Команда `update_version.py status` автоматически проверяет APP_ID и предупреждает о расхождениях между шаблоном и локальным config. Команда `sync` автоматически синхронизирует APP_ID в обеих секциях (`telegram_security` и `api_keys`) для совместимости.


#### Шаг 2: Добавить APP_ID в whitelist на сервере

Подключитесь к серверу и отредактируйте `security.py`:

```bash
ssh -p 22542 root@<server-ip>
cd /opt/TelegramHelper
nano security.py
```

Добавьте новый APP_ID в словарь `ALLOWED_APPS`:

```python
ALLOWED_APPS: Dict[str, dict] = {
    "bomcategorizer-v6": {
        "name": "BOM Categorizer Modern Edition v6",
        "version": "6.x",
        "allowed_endpoints": ["/ai_query", "/prompt_templates", "/prompt_categories"],
        "rate_limit_per_minute": 60,
        "rate_limit_per_day": 1000
    },
    # ... остальные версии
}
```

Сохраните файл (`Ctrl+O`, `Enter`, `Ctrl+X`).

#### Шаг 3: Пересобрать сервер

```bash
./scripts/change_token.sh
```

Выберите опцию `r` (перезапуск без смены токена).

#### Чек-лист синхронизации версий

- [ ] Обновлена версия в `config/config_qt.json.template`
- [ ] Обновлен `app_id` в том же файле
- [ ] Новый `app_id` добавлен в `TelegramHelper/security.py` на сервере
- [ ] Сервер TelegramHelper перезапущен
- [ ] Проверена работа кнопки "Проверить соединение"


---

## Рабочие сценарии

### 🎯 Сценарий 1: Релиз новой версии Modern Edition

```bash
# 1. Обновить версию
python3 scripts/bump_version.py --bump minor

# 2. Синхронизировать и проверить
python3 tools/update_version.py sync
python3 tools/update_version.py status

# 3. Закоммитить
git add config/ deployment/
git commit -m "Release: Modern Edition v5.1.0"

# 4. Собрать инсталлятор
python deployment/build_installer.py       # Windows (python или py)
./deployment/build_macos.sh                # macOS
```

### 🎯 Сценарий 2: Работа на новой машине

```bash
git clone <repo-url>
cd BOMCategorizer
python3 tools/update_version.py status
python3 tools/update_version.py sync
python app_qt.py
```

### 🎯 Сценарий 3: После git pull

```bash
python3 tools/update_version.py status
python3 tools/update_version.py sync
```

---

## FAQ

### ❓ Как узнать текущую версию?
```bash
python3 tools/update_version.py status
```

### ❓ Как обновить только Modern Edition?
```bash
python3 scripts/bump_version.py --bump patch
```
По умолчанию обновляется только Modern Edition.

### ❓ Как обновить Standard Edition?
```bash
python3 scripts/bump_version.py --bump patch --edition standard
```

### ❓ Версии рассинхронизировались, что делать?
```bash
python3 tools/update_version.py sync
```

### ❓ Команда sync затронет мои настройки UI?

**Нет!** Синхронизируется только:
- Секция `app_info` (версия, дата релиза, разработчик)
- `APP_ID` в секциях `telegram_security` и `api_keys`

Ваши личные настройки (`scale_factor`, размер окна, тема, API ключи и т.д.) останутся без изменений.

### ❓ Почему config.json в .gitignore?

Чтобы локальные настройки пользователя не попадали в Git. Каждая машина может иметь свои настройки UI, но версия проекта одна для всех.

### ❓ Installer собирается со старой версией?

Выполните перед сборкой:
```bash
python3 tools/update_version.py sync
```

---

## Файловая структура

```
BOMCategorizer/
├── config/
│   ├── config_qt.json.template  ← ИСТОЧНИК ПРАВДЫ (Modern)
│   ├── config.json.template     ← ИСТОЧНИК ПРАВДЫ (Standard)
│   └── rules.json
│
├── config_qt.json               (локальный, не в Git)
├── config.json                  (локальный, не в Git)
│
├── scripts/
│   └── bump_version.py          ← Основной инструмент
│
├── tools/
│   ├── update_version.py        ← Расширенный инструмент
│   └── sync_installer_versions.py
│
└── deployment/
    ├── build_installer.py       ← Сборка Windows (Inno Setup)
    ├── build_macos.sh           ← Сборка macOS (DMG)
    ├── installer_qt.iss         (синхронизируется)
    └── installer_clean.iss      (синхронизируется)
```

---

**Последнее обновление:** 29.11.2025  
**Автор:** Куреин М.Н.

