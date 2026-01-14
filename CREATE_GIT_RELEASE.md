# 🚀 Создание GitHub релиза (BOM Categorizer) — чек‑лист

Цель: выпустить **git tag** + **GitHub Release** + приложить артефакты (**Windows .exe**, **macOS .dmg**).

> **Важно:** версии в проекте хранятся **не** в `__init__.py`, а в шаблонах: `config/*.template`.  
> Подробно — `VERSION_MANAGEMENT.md`.

---

## 📌 Источник версии (однозначно)

- **Modern Edition**: `config/config_qt.json.template`
- **Standard Edition**: `config/config.json.template`

Тег релиза **vX.Y.Z** должен соответствовать версии в соответствующем шаблоне.

---

## ✅ Быстрый путь (90% случаев): Modern Edition

### 1) Поднять версию

```bash
# macOS/Linux
python3 scripts/bump_version.py --bump patch

# Windows
python scripts/bump_version.py --bump patch
```

### 2) Синхронизировать перед сборкой

```bash
# macOS/Linux
python3 tools/update_version.py sync

# Windows
python tools/update_version.py sync
```

### 3) Проверить версии

```bash
# macOS/Linux
python3 tools/update_version.py status

# Windows
python tools/update_version.py status
```

### 4) Коммит и тег

```bash
git add config/ deployment/ tools/ bom_categorizer/
git commit -m "Release: vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

### 5) Сборка

- **Windows**:

```powershell
python deployment/build_installer.py
```

- **macOS**:

```bash
make build-macos
# или напрямую:
./deployment/build_macos.sh
```

---

## 🔢 Обновление версии (Modern / Standard / Both)

### Вариант A (рекомендуется): `scripts/bump_version.py`

```bash
# Modern (по умолчанию)
python3 scripts/bump_version.py --bump patch

# Standard
python3 scripts/bump_version.py --bump patch --edition standard

# Both
python3 scripts/bump_version.py --bump patch --edition both
```

### Вариант B: `tools/update_version.py set`

```bash
# Modern
python3 tools/update_version.py set modern X.Y.Z

# Standard
python3 tools/update_version.py set standard X.Y.Z

# Both
python3 tools/update_version.py set both X.Y.Z
```

---

## 🔄 Что делает `sync` (и почему его надо запускать)

Команда:

```bash
python3 tools/update_version.py sync
```

Делает:
- приводит **локальные** `config.json` / `config_qt.json` к шаблонам (только `app_info` / `app_id`, ваши настройки не трогает)
- синхронизирует `deployment/installer_clean.iss` и `deployment/installer_qt.iss`
- генерирует `bom_categorizer/_build_meta.json` (git/время сборки для UI, **не коммитится**)

---

## 📦 Сборка артефактов

### 🪟 Windows

```powershell
python deployment/build_installer.py
```

Ожидаемые файлы:
- `BOMCategorizerModernSetup.exe` (Modern)
- `BOMCategorizerSetup.exe` (Standard)

### 🍎 macOS

```bash
make build-macos
```

Скрипт предложит выбрать редакцию (1/2).  
Ожидаемый файл (пример): `BOMCategorizer-X.Y.Z-macOS-Modern.dmg`

---

## 🚀 GitHub Release (рекомендуется: GitHub CLI `gh`)

### Установка и авторизация

```bash
gh --version
gh auth login
```

### Создать релиз и загрузить файл

```bash
gh release create vX.Y.Z \
  "BOMCategorizer-X.Y.Z-macOS-Modern.dmg" \
  --title "BOM Categorizer Modern Edition X.Y.Z" \
  --notes "Release notes here"
```

### Обновить файл в существующем релизе

```bash
gh release upload vX.Y.Z "BOMCategorizer-X.Y.Z-macOS-Modern.dmg" --clobber
```

### Открыть релиз в браузере

```bash
gh release view vX.Y.Z --web
```

---

## 🧰 Fallback без `gh` (через токен и скрипты)

> Лучше использовать `gh`. Скрипты оставлены как запасной вариант.

### GitHub Token (PAT)

1. Откройте: [Tokens (classic)](https://github.com/settings/tokens)
2. Создайте токен со scope: **repo**
3. Не храните токен в репозитории и не вставляйте в логи

### Windows PowerShell

```powershell
$Token = "ghp_..."
.\deployment\create_release.ps1 -Token $Token -Version "X.Y.Z"
```

### macOS/Linux bash

```bash
bash deployment/create_release.sh -t "ghp_..." -v "X.Y.Z"
```

---

## ✅ Проверка релиза

- Релиз появился в GitHub Releases
- Tag `vX.Y.Z` существует (и запушен)
- Артефакты (`.exe`/`.dmg`) прикреплены и скачиваются
- В приложении в футере / “О приложении” отображается версия **X.Y.Z** и корректная информация

---

## ❓ Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `Tag not found` | Проверьте `git push --tags`. |
| `Release already exists` | Используйте `gh release upload ... --clobber`. |
| `File not found` | Запускайте команды из корня проекта; проверьте имя файла артефакта. |
| Версия “не та” | Проверьте версию в `config/*.template`, затем `python tools/update_version.py sync`, затем пересоберите артефакт. |
