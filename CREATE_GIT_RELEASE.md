# Создание GitHub релиза

Это руководство объясняет, как создать релиз на GitHub и загрузить установочные файлы:
- **Windows:** `BOMCategorizerModernSetup.exe` с помощью скрипта `create_release.ps1`
- **macOS:** `BOMCategorizer-{version}-macOS-Modern.dmg` с помощью GitHub CLI или скрипта

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
   - **Windows:** Убедитесь, что файл `BOMCategorizerModernSetup.exe` находится в корне проекта
   - **macOS:** Убедитесь, что файл `BOMCategorizer-{version}-macOS-Modern.dmg` находится в корне проекта

3. **Git тег**
   - Тег версии должен быть создан и отправлен на GitHub
   - Например: `v4.4.2`

---

## Windows: Использование PowerShell скрипта

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

### Что делает скрипт (Windows)

1. ✅ Проверяет наличие файла установщика
2. ✅ Показывает размер файла
3. ✅ Создает релиз на GitHub через API
4. ✅ Загружает файл `BOMCategorizerModernSetup.exe` как asset релиза
5. ✅ Выводит ссылку на созданный релиз

---

## macOS: Использование GitHub CLI (рекомендуется)

### Предварительная установка GitHub CLI

Если GitHub CLI не установлен:

```bash
# Установка через Homebrew
brew install gh

# Авторизация (первый раз)
gh auth login
```

### Создание релиза через GitHub CLI

**Стандартное использование:**
```bash
gh release create v4.4.2 \
  --title "BOM Categorizer Modern Edition 4.4.2" \
  --notes "## Улучшения

- Увеличена ширина окна поиска PDF на 30%
- Добавлен двойной клик на путь папки для открытия в проводнике
- Простой режим теперь доступен без PIN сразу при запуске
- Переход на расширенный/экспертный режимы требует PIN" \
  BOMCategorizer-4.4.2-macOS-Modern.dmg
```

**С указанием версии (переменная):**
```bash
VERSION="4.4.2"
gh release create v${VERSION} \
  --title "BOM Categorizer Modern Edition ${VERSION}" \
  --notes "Release ${VERSION}" \
  BOMCategorizer-${VERSION}-macOS-Modern.dmg
```

**Если релиз уже существует (обновление):**
```bash
# Сначала удалите старый asset (если нужно) через веб-интерфейс
# Затем загрузите новый файл:
gh release upload v4.4.2 BOMCategorizer-4.4.2-macOS-Modern.dmg --clobber
```

### Что делает GitHub CLI

1. ✅ Проверяет наличие файла установщика
2. ✅ Создает релиз на GitHub (или обновляет существующий)
3. ✅ Загружает файл `.dmg` как asset релиза
4. ✅ Выводит ссылку на созданный релиз

### Альтернатива: Использование bash-скрипта

Если GitHub CLI недоступен, можно использовать bash-скрипт `create_release.sh`:

**Примечание:** Скрипт использует `jq` для правильного форматирования JSON (рекомендуется). Если `jq` не установлен, скрипт будет работать, но с упрощенным описанием релиза.

**Установка jq (если нужно):**
```bash
brew install jq
```

#### Базовое использование

```bash
./create_release.sh -t "ваш_github_token_здесь"
```

#### Параметры

- **`-t, --token TOKEN`** (обязательный) — GitHub Personal Access Token
- **`-v, --version VERSION`** (опционально) — версия релиза (по умолчанию: `4.4.2`)
- **`-r, --repo REPO`** (опционально) — репозиторий в формате `owner/repo` (по умолчанию: `kureinmaxim/BOMCategorizer`)
- **`-f, --file FILE`** (опционально) — имя DMG файла (по умолчанию: `BOMCategorizer-{VERSION}-macOS-Modern.dmg`)
- **`-h, --help`** — показать справку

#### Примеры

**Стандартное использование:**
```bash
./create_release.sh -t "ghp_xxxxxxxxxxxxxxxxxxxx"
```

**С указанием версии:**
```bash
./create_release.sh -t "ghp_xxxxxxxxxxxxxxxxxxxx" -v "4.4.2"
```

**С указанием файла:**
```bash
./create_release.sh -t "ghp_xxxxxxxxxxxxxxxxxxxx" -v "4.4.2" -f "custom.dmg"
```

**С указанием репозитория:**
```bash
./create_release.sh -t "ghp_xxxxxxxxxxxxxxxxxxxx" -v "4.4.2" -r "owner/repo"
```

**Справка:**
```bash
./create_release.sh -h
```

#### Что делает скрипт (macOS)

1. ✅ Проверяет наличие файла установщика
2. ✅ Показывает размер файла
3. ✅ Создает релиз на GitHub через API
4. ✅ Загружает файл `.dmg` как asset релиза
5. ✅ Выводит ссылку на созданный релиз

---

## Общие инструкции

## Создание тега версии

Перед созданием релиза убедитесь, что тег версии создан и отправлен:

```powershell
# Создать тег
git tag -a v4.4.2 -m "Release version 4.4.2"

# Отправить тег на GitHub
git push origin v4.4.2
```

## Альтернативный способ (через веб-интерфейс)

Если скрипты не работают, можно создать релиз вручную:

1. Перейдите на https://github.com/kureinmaxim/BOMCategorizer/releases/new
2. Выберите тег `v4.4.2` (или создайте новый)
3. Заполните название: `Release 4.4.2`
4. Добавьте описание (опционально)
5. Перетащите файл установщика в область "Attach binaries":
   - **Windows:** `BOMCategorizerModernSetup.exe`
   - **macOS:** `BOMCategorizer-4.4.2-macOS-Modern.dmg`
6. Нажмите "Publish release"

## Загрузка файла в существующий релиз

### Windows

Если релиз уже существует, используйте скрипт `upload_to_existing_release.ps1`:

```powershell
.\upload_to_existing_release.ps1 -Token "ваш_токен"
```

Этот скрипт:
- Найдёт существующий релиз
- Удалит старый файл установщика (если есть)
- Загрузит новый файл `BOMCategorizerModernSetup.exe`

### macOS

**Вариант 1: Использование GitHub CLI (рекомендуется)**

```bash
# Загрузить новый файл (заменит существующий с тем же именем)
gh release upload v4.4.2 BOMCategorizer-4.4.2-macOS-Modern.dmg --clobber

# Или загрузить как новый файл (если имя отличается)
gh release upload v4.4.2 BOMCategorizer-4.4.2-macOS-Modern.dmg
```

**Вариант 2: Использование bash-скрипта**

Если релиз уже существует, используйте скрипт `upload_to_existing_release.sh`:

```bash
# Автоматическое определение файлов (ищет .dmg и .exe)
./upload_to_existing_release.sh -t "ваш_токен" -v "4.4.5"
```

Этот скрипт:
- Найдёт существующий релиз
- Автоматически определит файлы `.dmg` и `.exe` для указанной версии (или используйте `-f` для указания файлов вручную)
- Удалит старые файлы установщика (если есть)
- Загрузит новые файлы

**Параметры скрипта:**
- **`-t, --token TOKEN`** (обязательный) — GitHub Personal Access Token
- **`-v, --version VERSION`** (опционально) — версия релиза (по умолчанию: `4.4.2`)
- **`-r, --repo REPO`** (опционально) — репозиторий (по умолчанию: `kureinmaxim/BOMCategorizer`)
- **`-f, --file FILE`** (опционально) — файл для загрузки (можно использовать несколько раз: `-f file1.dmg -f file2.exe`)
- **`-a, --auto`** — включить автоопределение файлов (по умолчанию: включено)
- **`--no-auto`** — отключить автоопределение файлов

**Примеры:**

```bash
# Автоматически загрузить оба файла (.dmg и .exe) для версии 4.4.5
./upload_to_existing_release.sh -t "ваш_токен" -v "4.4.5"

# Загрузить только указанные файлы
./upload_to_existing_release.sh -t "ваш_токен" -v "4.4.5" -f "file1.dmg" -f "file2.exe"

# Загрузить только один файл (без автоопределения)
./upload_to_existing_release.sh -t "ваш_токен" -v "4.4.5" -f "custom.dmg" --no-auto
```

## Устранение проблем

### Ошибка: "File not found"
- **Windows:** Убедитесь, что файл `BOMCategorizerModernSetup.exe` находится в текущей директории
- **macOS:** Убедитесь, что файл `BOMCategorizer-{version}-macOS-Modern.dmg` находится в текущей директории
- Проверьте правильность имени файла

### Ошибка: "Unauthorized" или "Bad credentials"
- Проверьте правильность токена
- Убедитесь, что токен имеет права `repo`
- Токен мог истечь — создайте новый

### Ошибка: "Release already exists" (422 Unprocessable Entity)
- Релиз с таким тегом уже существует на GitHub
- **Windows - Решение 1:** Используйте скрипт `upload_to_existing_release.ps1` для загрузки файла в существующий релиз
- **macOS - Решение 1:** Используйте `gh release upload v4.4.2 файл.dmg --clobber` для обновления файла
- **macOS - Решение 2:** Используйте скрипт `upload_to_existing_release.sh` для загрузки файла в существующий релиз
- **Решение 3:** Удалите старый релиз на https://github.com/kureinmaxim/BOMCategorizer/releases и создайте новый
- **Решение 4:** Обновите релиз вручную через веб-интерфейс (см. "Альтернативный способ" выше)

### Ошибка: "Tag not found"
- Создайте и отправьте тег на GitHub перед созданием релиза:
  ```bash
  # Создать тег (Windows/macOS одинаково)
  git tag -a v4.4.2 -m "Release version 4.4.2"
  git push origin v4.4.2
  ```

### Проблемы с кодировкой (Windows)
- Скрипт использует английский язык для избежания проблем с кодировкой
- Если возникают проблемы, запустите PowerShell с кодировкой UTF-8:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  .\create_release.ps1 -Token "ваш_токен"
  ```

### GitHub CLI не установлен (macOS)
- Установите через Homebrew: `brew install gh`
- Или используйте bash-скрипт `create_release.sh`
- Или используйте альтернативный способ через веб-интерфейс

### Скрипт не исполняемый (macOS)
- Сделайте скрипт исполняемым: `chmod +x create_release.sh`

### Ошибка: "Problems parsing JSON" (HTTP 400)
- Установите `jq` для правильного форматирования JSON: `brew install jq`
- Или используйте GitHub CLI вместо скрипта: `gh release create ...`

## Безопасность

⚠️ **ВАЖНО:** Никогда не коммитьте токен в репозиторий!

- Храните токен в безопасном месте
- **Windows:** Используйте переменные окружения для токена (опционально):
  ```powershell
  $env:GITHUB_TOKEN = "ваш_токен"
  .\create_release.ps1 -Token $env:GITHUB_TOKEN
  ```
- **macOS:** GitHub CLI хранит токен безопасно после `gh auth login`, но можно использовать переменную окружения:
  ```bash
  # Для GitHub CLI
  export GITHUB_TOKEN="ваш_токен"
  gh release create v4.4.2 ...
  
  # Для bash-скрипта
  export GITHUB_TOKEN="ваш_токен"
  ./create_release.sh -t "$GITHUB_TOKEN" -v "4.4.2"
  ```
- Если токен скомпрометирован, немедленно удалите его на GitHub и создайте новый

## Дополнительная информация

- GitHub API документация: https://docs.github.com/en/rest/releases/releases
- GitHub CLI документация: https://cli.github.com/manual/gh_release
- Ограничения размера файла: до 2 GB на релиз
- Рекомендуется использовать токены с ограниченным сроком действия

## Быстрая справка по командам

### Windows
```powershell
# Создать тег и отправить
git tag -a v4.4.2 -m "Release 4.4.2"
git push origin v4.4.2

# Создать релиз
.\create_release.ps1 -Token "ваш_токен" -Version "4.4.2"
```

### macOS
```bash
# Создать тег и отправить
git tag -a v4.4.2 -m "Release 4.4.2"
git push origin v4.4.2

# Создать релиз через GitHub CLI (рекомендуется)
gh release create v4.4.2 \
  --title "BOM Categorizer Modern Edition 4.4.2" \
  --notes "Описание изменений" \
  BOMCategorizer-4.4.2-macOS-Modern.dmg

# Или через bash-скрипт
./create_release.sh -t "ваш_токен" -v "4.4.2"

# Если релиз уже существует, обновить файлы (автоматически загрузит .dmg и .exe):
./upload_to_existing_release.sh -t "ваш_токен" -v "4.4.5"
```

