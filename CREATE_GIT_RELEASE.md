# 🚀 Создание GitHub Релиза: Полное Руководство

Это пошаговое руководство по созданию релизов BOM Categorizer.

---

## 📋 Общий процесс (Workflow)

1.  **Сборка:** Собрать `.exe` или `.dmg` файл.
2.  **Git Tag:** Создать и отправить тег версии.
3.  **Релиз:** Запустить скрипт создания релиза и загрузки файлов.

---

## 🏷️ ШАГ 1: Создание Git Тега (ОБЯЗАТЕЛЬНО)

GitHub создает релизы **только** на основе тегов. Без тега скрипты работать не будут или создадут "черновик" без привязки к версии.

### 1. Проверка текущих тегов
```bash
git tag
# Вывод: v4.4.0, v4.4.1...
```

### 2. Создание нового тега
Используйте семантическое версионирование (например, `v4.5.0`).

```bash
# Создать локальный тег с описанием
git tag -a v4.5.0 -m "Release 4.5.0: Fix parser bugs and update UI"

# ОТПРАВИТЬ тег на сервер (Критически важно!)
git push origin v4.5.0
```

> **Примечание:** Если вы ошиблись, удалите тег:
> `git tag -d v4.5.0` и `git push --delete origin v4.5.0`

---

## 📦 ШАГ 2: Сборка Инсталлятора

Перед загрузкой убедитесь, что у вас есть свежий файл инсталлятора.

**Windows:**
```bash
python deployment/build_installer.py
```
*Ожидаемый файл:* `BOMCategorizerModernSetup.exe` (в корне проекта).

---

## 🚀 ШАГ 3: Создание Релиза и Загрузка Файлов

### 🪟 Для Windows (PowerShell)

У нас есть два скрипта:
1.  `create_release.ps1` — создает новый релиз и загружает файл.
2.  `upload_to_existing_release.ps1` — только загружает файл в уже созданный релиз.

#### Вариант А: Создать новый релиз (Полный цикл)

```powershell
# 1. Задайте токен (чтобы не вводить каждый раз)
$Token = "ghp_ВАШ_ТОКЕН_ЗДЕСЬ"

# 2. Запустите скрипт
# Укажите версию БЕЗ 'v', если скрипт добавляет её сам, или как в теге.
# Скрипт ожидает, что тег v4.5.0 уже существует на GitHub.
.\deployment\create_release.ps1 -Token $Token -Version "4.5.0"
```

#### Вариант Б: Обновить существующий релиз (Если релиз уже создан)

Если вы исправили баг и пересобрали `.exe`, но версия осталась той же:

```powershell
$Token = "ghp_ВАШ_ТОКЕН_ЗДЕСЬ"

# Скрипт сам найдет последний релиз и загрузит в него BOMCategorizerModernSetup.exe
.\deployment\upload_to_existing_release.ps1 -Token $Token
```

#### Если есть ошибка "Execution of scripts is disabled on this system"

Запускайте с флагом обхода политики:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\create_release.ps1 -Token "ghp_..." -Version "4.5.0"
```

---

### 🍎 Для macOS (Terminal)

#### Вариант А: Использование GitHub CLI (Рекомендуется)
Это самый надежный способ. Требует `brew install gh`.

```bash
# 1. Авторизация (один раз)
gh auth login

# 2. Создание релиза и загрузка файла
gh release create v4.5.0 \
    BOMCategorizer-4.5.0-macOS-Modern.dmg \
    --title "v4.5.0" \
    --notes "Список изменений..."
```

#### Вариант Б: Bash скрипты
Если `gh` не установлен.

```bash
# Создание
./deployment/create_release.sh -t "ghp_TOKEN" -v "4.5.0"

# Обновление (только загрузка файла)
./deployment/upload_to_existing_release.sh -t "ghp_TOKEN"
```

---

## 🛠 Где взять токен (PAT)?

1.  Зайдите на GitHub: [Settings -> Developer settings -> Personal access tokens -> Tokens (classic)](https://github.com/settings/tokens).
2.  Нажмите **Generate new token (classic)**.
3.  Выберите scopes (права):
    *   ✅ **repo** (Full control of private repositories) — этого достаточно.
4.  Скопируйте токен (он начинается на `ghp_`).

---

## ❓ Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `Tag not found` | Вы забыли сделать `git push origin v4.5.0`. Скрипт не может создать релиз для несуществующего тега. |
| `Release already exists` | Релиз для этого тега уже создан. Используйте скрипт `upload_to_existing...` или удалите релиз вручную на сайте. |
| `Asset already exists` | Файл с таким именем уже есть в релизе. Скрипты обычно пытаются его заменить, но иногда нужно удалить старый файл вручную через браузер. |
| `File not found` | Скрипт не видит `.exe` файл. Убедитесь, что вы запустили `build_installer.py` и файл лежит в корне проекта. |
