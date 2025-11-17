# Создание GitHub релиза

Это руководство объясняет, как создать релиз на GitHub и загрузить установочный файл `BOMCategorizerModernSetup.exe` с помощью скрипта `create_release.ps1`.

## Предварительные требования

1. **GitHub Personal Access Token (PAT)**
   - Перейдите на https://github.com/settings/tokens
   - Нажмите "Generate new token" → "Generate new token (classic)"
   - Укажите имя токена (например, "BOMCategorizer Release")
   - Выберите срок действия
   - Отметьте права: **`repo`** (полный доступ к репозиториям)
   - Нажмите "Generate token"
   - **ВАЖНО:** Скопируйте токен сразу — он показывается только один раз!

2. **Файл установщика**
   - Убедитесь, что файл `BOMCategorizerModernSetup.exe` находится в корне проекта

3. **Git тег**
   - Тег версии должен быть создан и отправлен на GitHub
   - Например: `v4.4.2`

## Использование скрипта

### Базовое использование

```powershell
.\create_release.ps1 -Token "ваш_github_token_здесь"
```

### Параметры

- **`-Token`** (обязательный) — GitHub Personal Access Token
- **`-Version`** (опционально) — версия релиза (по умолчанию: `4.4.2`)
- **`-Repo`** (опционально) — репозиторий в формате `owner/repo` (по умолчанию: `kureinmaxim/BOMCategorizer`)
- **`-SetupFile`** (опционально) — имя файла установщика (по умолчанию: `BOMCategorizerModernSetup.exe`)

### Примеры

**Стандартное использование:**
```powershell
.\create_release.ps1 -Token "ghp_xxxxxxxxxxxxxxxxxxxx"
```

**С указанием версии:**
```powershell
.\create_release.ps1 -Token "ghp_xxxxxxxxxxxxxxxxxxxx" -Version "4.4.2"
```

**Если ExecutionPolicy блокирует выполнение:**
```powershell
powershell.exe -ExecutionPolicy Bypass -File .\create_release.ps1 -Token "ghp_xxxxxxxxxxxxxxxxxxxx"
```

## Что делает скрипт

1. ✅ Проверяет наличие файла установщика
2. ✅ Показывает размер файла
3. ✅ Создает релиз на GitHub через API
4. ✅ Загружает файл `BOMCategorizerModernSetup.exe` как asset релиза
5. ✅ Выводит ссылку на созданный релиз

## Создание тега версии

Перед созданием релиза убедитесь, что тег версии создан и отправлен:

```powershell
# Создать тег
git tag -a v4.4.2 -m "Release version 4.4.2"

# Отправить тег на GitHub
git push origin v4.4.2
```

## Альтернативный способ (через веб-интерфейс)

Если скрипт не работает, можно создать релиз вручную:

1. Перейдите на https://github.com/kureinmaxim/BOMCategorizer/releases/new
2. Выберите тег `v4.4.2` (или создайте новый)
3. Заполните название: `Release 4.4.2`
4. Добавьте описание (опционально)
5. Перетащите файл `BOMCategorizerModernSetup.exe` в область "Attach binaries"
6. Нажмите "Publish release"

## Устранение проблем

### Ошибка: "File not found"
- Убедитесь, что файл `BOMCategorizerModernSetup.exe` находится в текущей директории
- Проверьте правильность имени файла

### Ошибка: "Unauthorized" или "Bad credentials"
- Проверьте правильность токена
- Убедитесь, что токен имеет права `repo`
- Токен мог истечь — создайте новый

### Ошибка: "Release already exists"
- Релиз с таким тегом уже существует
- Удалите старый релиз на GitHub или используйте другую версию

### Ошибка: "Tag not found"
- Создайте и отправьте тег на GitHub перед созданием релиза:
  ```powershell
  git tag -a v4.4.2 -m "Release version 4.4.2"
  git push origin v4.4.2
  ```

### Проблемы с кодировкой
- Скрипт использует английский язык для избежания проблем с кодировкой
- Если возникают проблемы, запустите PowerShell с кодировкой UTF-8:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  .\create_release.ps1 -Token "ваш_токен"
  ```

## Безопасность

⚠️ **ВАЖНО:** Никогда не коммитьте токен в репозиторий!

- Храните токен в безопасном месте
- Используйте переменные окружения для токена (опционально):
  ```powershell
  $env:GITHUB_TOKEN = "ваш_токен"
  .\create_release.ps1 -Token $env:GITHUB_TOKEN
  ```
- Если токен скомпрометирован, немедленно удалите его на GitHub и создайте новый

## Дополнительная информация

- GitHub API документация: https://docs.github.com/en/rest/releases/releases
- Ограничения размера файла: до 2 GB на релиз
- Рекомендуется использовать токены с ограниченным сроком действия

