# 🚀 Создание GitHub Релиза: Полное Руководство

Это пошаговое руководство по созданию релизов BOM Categorizer.

---

## 📋 Общий процесс (Workflow)

1. **Обновить версию:** Изменить `__version__` в `bom_categorizer/__init__.py`
2. **Коммит изменений:** Закоммитить и запушить все изменения
3. **Сборка:** Собрать `.exe` или `.dmg` файл
4. **Релиз:** Создать релиз и загрузить файлы через GitHub CLI

---

## 🔢 ШАГ 1: Обновление Версии

### 1. Обновить версию в коде

Версия приложения хранится в файле `bom_categorizer/__init__.py`:

```python
__version__ = "5.1.3"  # Измените на нужную версию
```

### 2. Закоммитить изменения

```bash
# Добавить все изменения
git add .

# Коммит с описанием
git commit -m "feat: Enhanced UI/UX with hotkeys, custom prompts, and improved settings dialog

### New Features
- Added keyboard shortcuts (Cmd+1/2/3, Cmd+F/P/A)
- Enhanced Custom Prompt functionality
- Set Telegram Bot as default AI provider

### Bug Fixes
- Fixed persistent stuck tooltip issue
- Fixed port saving bug
- Fixed Cmd+F hotkey

Version: 5.1.3"

# Отправить на GitHub
git push origin feature/custom-encryption  # или main/master
```

### 3. Создать и отправить тег версии

```bash
# Создать тег
git tag -a v5.1.3 -m "Release 5.1.3"

# Отправить тег на сервер
git push origin v5.1.3
```

> **Важно:** Номер тега должен совпадать с версией в `__init__.py`!

---

## 📦 ШАГ 2: Сборка Инсталлятора

### 🍎 macOS

```bash
cd deployment
bash build_macos.sh
```

Скрипт предложит выбрать версию для сборки:
- `[1]` Standard (Tkinter)
- `[2]` Modern Edition (PySide6) ← **Выбирайте это для современной версии**

*Ожидаемый файл:* `BOMCategorizer-5.1.3-macOS-Modern.dmg` (в корне проекта)

### 🪟 Windows

```powershell
python deployment/build_installer.py
```

*Ожидаемый файл:* `BOMCategorizerModernSetup.exe`

---

## 🚀 ШАГ 3: Создание Релиза и Загрузка Файлов

### 🍎 Для macOS (Рекомендуется: GitHub CLI)

#### Установка GitHub CLI (если еще не установлен)
```bash
brew install gh
```

#### Авторизация (один раз)
```bash
gh auth login
```

#### Создание релиза и загрузка файла

```bash
# Убедитесь что вы в корне проекта
cd /Users/olgazaharova/Project/ProjectPython/BOMCategorizer

# Создать релиз и загрузить DMG
gh release create v5.1.3 \
    BOMCategorizer-5.1.3-macOS-Modern.dmg \
    --title "BOM Categorizer Modern Edition 5.1.3" \
    --notes "См. список изменений в CHANGELOG или release notes"
```

#### Загрузка файла в существующий релиз

Если релиз уже создан и нужно только обновить файл:

```bash
gh release upload v5.1.3 BOMCategorizer-5.1.3-macOS-Modern.dmg --clobber
```

Флаг `--clobber` заменит существующий файл.

#### Открыть релиз в браузере

```bash
gh release view v5.1.3 --web
```

---

### Альтернатива: Bash скрипты (если GitHub CLI недоступен)

#### Получение GitHub Token

1. Зайдите на GitHub: [Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Нажмите **Generate new token (classic)**
3. Выберите scope: ✅ **repo**
4. Скопируйте токен (начинается на `ghp_`)

#### Создание релиза

```bash
cd /Users/olgazaharova/Project/ProjectPython/BOMCategorizer
bash deployment/create_release.sh -t "ghp_YOUR_TOKEN" -v "5.1.3"
```

**Важно:** Скрипт должен запускаться из корня проекта, где находится DMG файл!

---

### 🪟 Для Windows (PowerShell)

#### Вариант А: Создать новый релиз

```powershell
$Token = "ghp_ВАШ_ТОКЕН_ЗДЕСЬ"

.\deployment\create_release.ps1 -Token $Token -Version "5.1.3"
```

#### Вариант Б: Обновить существующий релиз

```powershell
$Token = "ghp_ВАШ_ТОКЕН_ЗДЕСЬ"

.\deployment\upload_to_existing_release.ps1 -Token $Token
```

#### Если есть ошибка выполнения скриптов

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\create_release.ps1 -Token "ghp_..." -Version "5.1.3"
```

---

## ✅ Проверка Релиза

После создания релиза проверьте:

1. ✅ Релиз виден на https://github.com/kureinmaxim/BOMCategorizer/releases
2. ✅ DMG/EXE файл прикреплен и доступен для скачивания
3. ✅ Версия в релизе совпадает с версией в `__init__.py`
4. ✅ Тег версии создан и виден в GitHub

---

## 🛠 Где взять токен (PAT)?

1. Зайдите на GitHub: [Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Нажмите **Generate new token (classic)**
3. Выберите scopes (права):
   * ✅ **repo** (Full control of repositories)
4. Скопируйте токен (начинается на `ghp_`)

---

## ❓ Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `Tag not found` | Забыли `git push origin v5.1.3`. Отправьте тег на GitHub. |
| `Release already exists` | Релиз уже создан. Используйте `gh release upload ... --clobber` для обновления файла. |
| `File not found` | DMG/EXE файл не в корне проекта. Проверьте путь или запустите скрипт из корня. |
| `curl: option : blank argument` | Ошибка в bash скрипте. Используйте GitHub CLI (`gh`) вместо bash скрипта. |
| Версия не обновилась | Забыли изменить `__version__` в `bom_categorizer/__init__.py` и закоммитить. |

---

## 📝 Пример полного цикла релиза v5.1.3

```bash
# 1. Обновить версию
vim bom_categorizer/__init__.py  # Изменить на "5.1.3"

# 2. Коммит
git add .
git commit -m "chore: bump version to 5.1.3"
git push origin feature/custom-encryption

# 3. Тег
git tag -a v5.1.3 -m "Release 5.1.3"
git push origin v5.1.3

# 4. Сборка (было сделано ранее вручную)
cd deployment && bash build_macos.sh
# Выбрать [2] Modern Edition

# 5. Релиз через GitHub CLI
cd ..
gh release create v5.1.3 \
    BOMCategorizer-5.1.3-macOS-Modern.dmg \
    --title "BOM Categorizer Modern Edition 5.1.3" \
    --notes "Release notes here"

# 6. Проверка
gh release view v5.1.3 --web
```

**Готово!** 🎉
