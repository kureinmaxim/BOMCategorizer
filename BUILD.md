# ⚙️ Сборка и релиз (BOM Categorizer)

Этот документ — **практический чек‑лист**: как поднять версию, синхронизировать файлы и собрать инсталляторы под Windows/macOS.

> Подробная теория версионирования: `VERSION_MANAGEMENT.md`  
> Создание GitHub релиза: `CREATE_GIT_RELEASE.md`

---

## ✅ Быстрый старт

### Через Makefile (если доступен)

```bash
make help              # показать команды
make version-status    # проверить версии
make version-sync      # sync (локальные config/iss/build meta)
make build-macos       # собрать macOS DMG
make run-qt            # запустить Modern Edition (из репозитория)
```

### Без Makefile

- **Windows**: `python deployment/build_installer.py`
- **macOS**: `./deployment/build_macos.sh` (важно именно `./`, не `/deployment/...`)
- **Версии**: `python tools/update_version.py status` / `python3 tools/update_version.py status`

> ⚠️ **macOS:** используйте `python3` вместо `python`.

---

## 🔄 1) Управление версиями (Versioning)

### Источник правды

Версии хранятся **только** в шаблонах:
- **Standard Edition**: `config/config.json.template`
- **Modern Edition**: `config/config_qt.json.template`

> ⚠️ Не меняйте версию вручную в `config.json` / `config_qt.json` / `*.iss`.  
> Используйте `scripts/bump_version.py` или `tools/update_version.py`.

---

### Проверить статус версий

```bash
# Windows
python tools/update_version.py status

# macOS/Linux
python3 tools/update_version.py status
```

---

### Поднять/установить версию

#### Вариант A (рекомендуется): `bump_version.py`

```bash
# macOS/Linux
python3 scripts/bump_version.py --bump patch

# Windows
python scripts/bump_version.py --bump patch
```

#### Вариант B: `update_version.py set`

```bash
# Modern Edition
python3 tools/update_version.py set modern 5.5.3

# Standard Edition
python3 tools/update_version.py set standard 3.3.0

# обе редакции
python3 tools/update_version.py set both 5.0.0
```

---

### Синхронизировать файлы перед сборкой

Команда:

```bash
# Windows
python tools/update_version.py sync

# macOS/Linux
python3 tools/update_version.py sync
```

Что делает `sync`:
- обновляет **локальные** `config.json` / `config_qt.json` (только `app_info` / `app_id`, личные настройки не трогает)
- обновляет `deployment/installer_clean.iss` и `deployment/installer_qt.iss`
- обновляет захардкоженные fallback‑версии в коде (где применимо)
- генерирует `bom_categorizer/_build_meta.json` (git/время сборки для UI “О приложении”, **не коммитится**)

---

## 📦 2) Сборка инсталляторов (Build)

### 🪟 Windows (Inno Setup)

Запуск:

```powershell
python deployment/build_installer.py
```

Что происходит:
- выбор редакции (Standard / Modern)
- сбор временной папки `temp_installer`
- запуск Inno Setup Compiler
- готовый `.exe` появляется в корне проекта

Результат:
- `BOMCategorizerModernSetup.exe` или `BOMCategorizerSetup.exe`

---

### 🍎 macOS (DMG + py2app)

Рекомендуемый запуск:

```bash
make build-macos
```

Или напрямую:

```bash
./deployment/build_macos.sh
```

> ⚠️ Не используйте `/deployment/build_macos.sh` — это другой путь.

Что происходит:
- выполняется `tools/update_version.py sync`
- выбор редакции (Standard / Modern)
- сборка `.app` через `py2app`
- упаковка `.app` в `.dmg`

Результат (пример):
- `BOMCategorizer-X.Y.Z-macOS-Modern.dmg`

---

## 🚀 3) Релиз (GitHub)

Рекомендуемый порядок:

1) **Проверка**

```bash
python3 tools/update_version.py status
```

2) **Поднять версию** (`bump_version.py` или `update_version.py set`)

3) **Синхронизация**

```bash
python3 tools/update_version.py sync
```

4) **Коммит + тег**

```bash
git add config/ deployment/ tools/ bom_categorizer/
git commit -m "Release: vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

5) **Сборка артефактов** (`.exe` / `.dmg`) и загрузка в GitHub Release  
См. `CREATE_GIT_RELEASE.md`.

---

## 🐛 Устранение неполадок

### ❌ Inno Setup не найден

По умолчанию ожидается:
- `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`

Если путь другой — настройте его в `deployment/build_installer.py`.

---

### ❌ Inno Setup: `EndUpdateResource failed (110)`

Антивирус (Windows Defender) блокирует запись в `.exe` во время сборки.

**Решение:**

```powershell
# 1. Добавить исключение в Windows Defender
Add-MpPreference -ExclusionPath "C:\Project\BOMCategorizer"

# 2. Удалить старый .exe перед повторной сборкой
Remove-Item "BOMCategorizerModernSetup.exe" -Force -ErrorAction SilentlyContinue

# 3. Повторить сборку
python deployment/build_installer.py
```

> ⚠️ Исключение нужно добавить один раз (от имени администратора). После этого пересборки работают без ошибок.

---

### ❌ Ошибка с PySide6 / offline_packages

Если сборка Modern Edition ругается на зависимости:
- удалите `offline_packages`
- повторите сборку (скрипт попробует скачать пакеты)

Ручная загрузка (пример для Windows):

```powershell
pip download PySide6 -d offline_packages --platform win_amd64 --python-version 313 --only-binary=:all:
```

---

### ❌ Версии “разъехались”

```bash
python3 tools/update_version.py status
python3 tools/update_version.py sync
```

---

### ❌ Windows: `pip` не распознаётся

Если `pip` не в PATH, используйте:

```powershell
python -m pip install <пакет>
# или
py -m pip install <пакет>
```

---

### ❌ macOS: `command not found: python`

На macOS используйте `python3`.

