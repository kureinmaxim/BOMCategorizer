# 🚀 Создание GitHub релиза

Это руководство поможет вам создать релиз на GitHub и загрузить установочные файлы для Windows и macOS.

---

## ⚡️ Быстрая справка (Cheatsheet)

### 🏷 1. Создание тега (Обязательно)
Перед созданием релиза всегда создавайте тег:
```bash
git tag -a v4.4.2 -m "Release 4.4.2"
git push origin v4.4.2
```

### 🪟 2. Windows (PowerShell)
```powershell
# Создать новый релиз
.\deployment\create_release.ps1 -Token "ваш_токен" -Version "4.4.2"

# Обновить существующий (загрузить файлы)
.\deployment\upload_to_existing_release.ps1 -Token "ваш_токен"
```

### 🍎 3. macOS (Terminal)
```bash
# Создать релиз (GitHub CLI)
gh release create v4.4.2 --title "v4.4.2" --notes "Notes" BOMCategorizer-4.4.2-macOS-Modern.dmg

# Обновить существующий (Bash скрипт)
./deployment/upload_to_existing_release.sh -t "ваш_токен" -v "4.4.2"
```

---

## 📋 Предварительные требования

1.  **GitHub Personal Access Token (PAT)**
    *   Где взять: [GitHub Settings -> Tokens (Classic)](https://github.com/settings/tokens)
    *   Права: **`repo`** (Full control of private repositories)
    *   **Важно:** Скопируйте токен сразу после создания!

2.  **Файлы установщика** (должны лежать в корне проекта)
    *   Windows: `BOMCategorizerModernSetup.exe`
    *   macOS: `BOMCategorizer-{version}-macOS-Modern.dmg`

3.  **Git тег**
    *   Версия должна быть затегана и отправлена на сервер (см. "Быстрая справка").

---

## 🪟 Windows: Инструкции

### Создание нового релиза
Используйте скрипт `deployment/create_release.ps1`.

**Синтаксис:**
```powershell
.\deployment\create_release.ps1 -Token "ghp_xxx" [-Version "4.4.2"] [-Repo "owner/repo"]
```

**Примеры:**
```powershell
# Стандартный запуск
.\deployment\create_release.ps1 -Token "ghp_mytoken123"

# Если ExecutionPolicy блокирует запуск:
powershell.exe -ExecutionPolicy Bypass -File .\deployment\create_release.ps1 -Token "ghp_mytoken123"
```

### Загрузка в существующий релиз
Используйте скрипт `deployment/upload_to_existing_release.ps1`.

```powershell
.\deployment\upload_to_existing_release.ps1 -Token "ghp_mytoken123"
```
*Скрипт автоматически найдет последний релиз и обновит файл `BOMCategorizerModernSetup.exe`.*

---

## 🍎 macOS: Инструкции

### Вариант 1: GitHub CLI (Рекомендуется)
Требуется установленный `gh` (`brew install gh`).

**Создание релиза:**
```bash
gh release create v4.4.2 \
  --title "BOM Categorizer Modern Edition 4.4.2" \
  --notes "Описание изменений" \
  BOMCategorizer-4.4.2-macOS-Modern.dmg
```

**Обновление файла в релизе:**
```bash
gh release upload v4.4.2 BOMCategorizer-4.4.2-macOS-Modern.dmg --clobber
```

### Вариант 2: Bash скрипты
Если CLI недоступен, используйте скрипты из `deployment/`.
*Рекомендуется установить `jq` (`brew install jq`) для корректной работы с JSON.*

**Создание релиза:**
```bash
./deployment/create_release.sh -t "ghp_xxx" -v "4.4.2"
```

**Обновление релиза:**
```bash
# Автоматически найдет .dmg и .exe и загрузит их в существующий релиз
./deployment/upload_to_existing_release.sh -t "ghp_xxx" -v "4.4.2"
```

---

## 🛠 Устранение проблем

| Проблема | Возможная причина и решение |
|----------|-----------------------------|
| **File not found** | Проверьте, что файлы `.exe` или `.dmg` находятся в корне проекта и их имена совпадают с ожидаемыми. |
| **Unauthorized** | Неверный токен или отсутствуют права `repo`. Токен мог истечь. |
| **Release already exists** | Релиз с таким тегом уже существует. Используйте скрипты `upload_to_existing...` или удалите релиз вручную. |
| **Tag not found** | Тег не найден на GitHub. Выполните `git push origin vX.X.X`. |
| **Problems parsing JSON** | (macOS) Установите `jq`: `brew install jq`. |

## 🔐 Безопасность
*   ⚠️ **Никогда не коммитьте токены в репозиторий!**
*   Используйте переменные окружения для безопасности:
    *   PowerShell: `$env:GITHUB_TOKEN = "..."`
    *   Bash: `export GITHUB_TOKEN="..."`

## 🌐 Полезные ссылки
*   [GitHub Releases (Web UI)](https://github.com/kureinmaxim/BOMCategorizer/releases)
*   [GitHub CLI Manual](https://cli.github.com/manual/gh_release)
