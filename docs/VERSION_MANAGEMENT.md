# Управление версиями проекта

## 📋 Содержание

1. [Обзор системы](#обзор-системы)
2. [Создание локальных config файлов](#создание-локальных-config-файлов)
3. [Источник правды](#источник-правды)
4. [Как обновить версию](#как-обновить-версию)
5. [Синхронизация файлов сборки](#синхронизация-файлов-сборки)
6. [Автоматизация](#автоматизация)
7. [Файловая структура](#файловая-структура)
8. [Роль локальных config файлов](#роль-локальных-config-файлов)
9. [Рабочий процесс](#рабочий-процесс)
10. [FAQ](#faq)

---

## Обзор системы

В проекте BOM Categorizer версии управляются **централизованно** через шаблоны конфигурационных файлов. Это обеспечивает:

✅ **Единый источник правды** - версия хранится только в шаблонах  
✅ **Автоматическая синхронизация** - все скрипты сборки читают из шаблонов  
✅ **Защита локальных настроек** - рабочие config файлы в `.gitignore`  
✅ **Простота обновления** - одна команда обновляет все файлы  

---

## Создание локальных config файлов

Локальные файлы `config.json` и `config_qt.json` не хранятся в Git. Они создаются из шаблонов и содержат личные настройки. Если после клонирования репозитория или `git pull` этих файлов нет, создайте их одним из способов:

1. **Автоматически при запуске приложения**  
   ```bash
   # Standard Edition
   python app.py

   # Modern Edition (Qt)
   python app_qt.py
   ```
   При первом запуске `config_manager.py` скопирует соответствующий шаблон (`config*.json.template`) в рабочий файл.

2. **Вручную из шаблонов**  
   ```powershell
   # Windows / PowerShell
   Copy-Item config.json.template config.json
   Copy-Item config_qt.json.template config_qt.json
   ```
   ```bash
   # macOS / Linux
   cp config/config.json.template config.json
   cp config/config_qt.json.template config_qt.json
   ```

3. **Через Python (если PowerShell недоступен)**  
   ```bash
   python -c "import shutil; shutil.copy('config/config.json.template', 'config.json')"
   python -c "import shutil; shutil.copy('config/config_qt.json.template', 'config_qt.json')"
   ```

> ⚠️ Не редактируйте шаблоны при настройке локального окружения. Все персональные параметры (размер окна, масштаб UI, PIN и т.д.) изменяйте в рабочих файлах `config.json` и `config_qt.json`, которые находятся в `.gitignore`.

---

## Источник правды

### Где хранятся версии:

**Единственное место хранения версий:**

```
config/config.json.template       → Standard Edition (Tkinter)
config/config_qt.json.template    → Modern Edition (PySide6)
```

Эти файлы:
- ✅ Хранятся в Git
- ✅ Клонируются на все машины
- ✅ Используются всеми скриптами сборки

### Что НЕ является источником правды:

❌ `config.json` - локальный файл (не в Git)  
❌ `config_qt.json` - локальный файл (не в Git)  
❌ `installer_qt.iss` - генерируется автоматически  
❌ `installer_clean.iss` - генерируется автоматически  

---

## Как обновить версию

### Вариант 1: Используя утилиту (рекомендуется)

```bash
# Показать текущие версии (шаблоны и локальные)
python tools/update_version.py status

# Обновить Standard Edition
python tools/update_version.py set standard 3.4.0

# Обновить Modern Edition
python tools/update_version.py set modern 4.4.7

# Обновить обе версии одновременно
python tools/update_version.py set both 5.0.0
```

**Команда `status` показывает:**
- ✅ Версии в шаблонах (`config*.json.template`) — источник правды
- ✅ Версии в локальных файлах (`config*.json`) — если они существуют
- ✅ Сравнение версий и предупреждение, если они отличаются
- ✅ Рекомендацию выполнить `sync`, если обнаружены расхождения

**Пример вывода `status` (когда версии синхронизированы):**
```
[STATUS] ТЕКУЩИЕ ВЕРСИИ

ℹ️ Modern Edition (PySide6)
  Шаблон:
    Версия:      4.3.1
    Дата релиза: 13.11.2025
  Локальный:
    Версия:      4.3.1
    Дата релиза: 13.11.2025

✅ Все версии синхронизированы
```

**Пример вывода `status` (когда версии отличаются):**
```
[STATUS] ТЕКУЩИЕ ВЕРСИИ

ℹ️ Modern Edition (PySide6)
  Шаблон:
    Версия:      4.3.1
  Локальный:
    Версия:      4.2.3
    ⚠️ Версии отличаются!

⚠️ ОБНАРУЖЕНЫ РАСХОЖДЕНИЯ В ВЕРСИЯХ!
   Выполните синхронизацию:
   python update_version.py sync
```

**⚠️ Если версии отличаются:**
Если после `python update_version.py status` вы видите предупреждение о расхождении версий, выполните:
```bash
python tools/update_version.py sync
```
Это синхронизирует локальные config файлы с шаблонами (обновит только секцию `app_info`, сохранив ваши личные настройки).

После выполнения команды `set` обновляется:
- шаблон (`config*.json.template`) — источник правды для сборок;
- локальный `config*.json` (если существует) — синхронизируется только блок `app_info`, а разделы `security`, `window`, `ui` остаются без изменений.

**Что происходит автоматически:**
1. ✅ Обновляется версия в шаблоне
2. ✅ Обновляется дата релиза
3. ✅ Синхронизируются `.iss` файлы
4. ✅ Выводится отчет

### Вариант 2: Вручную

1. **Откройте шаблон:**
   ```bash
   nano config/config_qt.json.template  # для Modern Edition
   # или
   nano config/config.json.template     # для Standard Edition
   ```

2. **Измените версию:**
   ```json
   {
     "app_info": {
       "version": "4.3.0",           ← Измените здесь
       "release_date": "12.11.2025", ← И здесь (опционально)
       ...
     }
   }
   ```

3. **Синхронизируйте файлы сборки:**
   ```bash
   python update_version.py sync
   ```

---

## Синхронизация файлов сборки

### Что синхронизируется:

| Файл | Откуда читает | Как синхронизируется |
|------|---------------|---------------------|
| `config.json` (локальный) | `config.json.template` | Через `update_version.py sync` |
| `config_qt.json` (локальный) | `config_qt.json.template` | Через `update_version.py sync` |
| `build_macos.sh` | `*.template` | Автоматически при запуске |
| `installer_clean.iss` | `*.template` | Через `sync_installer_versions.py` |
| `installer_qt.iss` | `*.template` | Через `sync_installer_versions.py` |

### Команды синхронизации:

```bash
# Синхронизировать все файлы (локальные config + файлы сборки)
python tools/update_version.py sync

# Или напрямую только файлы сборки
python tools/sync_installer_versions.py
```

**Что делает `python update_version.py sync`:**
1. ✅ Синхронизирует локальные `config.json` и `config_qt.json` с шаблонами
   - Обновляет только секцию `app_info` (version, release_date, last_updated)
   - **Сохраняет** все личные настройки (scale_factor, window size, theme и т.д.)
2. ✅ Синхронизирует файлы сборки `.iss` с шаблонами

**Пример вывода `sync`:**
```
🔄 СИНХРОНИЗАЦИЯ ФАЙЛОВ СБОРКИ И ЛОКАЛЬНЫХ CONFIG

ℹ️ Синхронизация локальных config файлов:
  config_qt.json: 4.2.3 → 4.3.1
   → Обновлен локальный файл: config_qt.json

ℹ️ Синхронизация файлов сборки:
✅ Обновлен: installer_qt.iss -> v4.3.1 (Modern Edition)

✅ Синхронизация завершена.
ℹ️ Локальные config обновлены (только секция app_info, личные настройки сохранены)
```

**Когда нужно синхронизировать:**
- ✅ После обновления версии в шаблоне
- ✅ После клонирования репозитория
- ✅ После переключения веток в Git
- ✅ Перед созданием installer'а
- ✅ Если `python update_version.py status` показывает расхождения версий

---

## Автоматизация

### build_macos.sh (macOS)

Скрипт **автоматически читает** версии из шаблонов:

```bash
# Читает версию из config/config_qt.json.template
MODERN_VERSION=$(python3 -c "import json; print(json.load(open('config/config_qt.json.template'))['app_info']['version'])")

# Использует эту версию при сборке DMG
./deployment/build_macos.sh
```

✅ **Никакой ручной синхронизации не требуется**

### Windows Installer (.iss)

Скрипты Inno Setup **НЕ могут** читать JSON напрямую, поэтому:

1. Версии в `.iss` файлах обновляются через `sync_installer_versions.py`
2. Перед сборкой installer'а запустите:
   ```bash
   python update_version.py sync
   ```

---

## Файловая структура

```
BOMCategorizer/
│
├── 📁 config/                      # Конфигурационные файлы
│   ├── 📄 config.json.template     ← ИСТОЧНИК ПРАВДЫ для Standard
│   ├── 📄 config_qt.json.template  ← ИСТОЧНИК ПРАВДЫ для Modern
│   └── 📄 rules.json               # Правила классификации
│
├── 📄 config.json                  (локальный, не в Git)
├── 📄 config_qt.json               (локальный, не в Git)
│
├── 📁 tools/                       # Утилиты проекта
│   ├── 🔧 update_version.py        ← Главная утилита управления
│   └── 🔧 sync_installer_versions.py  ← Синхронизация .iss файлов
│
├── 📁 deployment/                  # Скрипты сборки
│   ├── 📦 build_macos.sh           (читает из config/)
│   ├── 📦 installer_clean.iss      (обновляется автоматически)
│   └── 📦 installer_qt.iss         (обновляется автоматически)
│
└── bom_categorizer/
    └── config_manager.py           (создает config из шаблонов)
```

---

## Роль локальных config файлов

### Зачем нужны config.json и config_qt.json?

**Шаблоны** (`*.template`) и **рабочие файлы** имеют **разные роли**:

```
config_qt.json.template    →  Шаблон (в Git, версия проекта)
         ↓ копируется при первом запуске
config_qt.json            →  Рабочий файл (НЕ в Git, личные настройки)
```

### 🎯 Как это работает:

**1. При первом запуске приложения:**

```python
# В config_manager.py
def initialize_config_from_template(config_name="config.json"):
    config_path = "config.json"
    template_path = "config/config.json.template"
    
    # Если config.json НЕ существует
    if not os.path.exists(config_path):
        # Копируем template → config.json
        shutil.copy2(template_path, config_path)
        print(f"✅ Создан конфиг из шаблона")
```

**2. Приложение работает с локальным config:**

```python
# В gui_qt.py
def load_config() -> dict:
    # Читает config_qt.json (НЕ template!)
    with open("config_qt.json", "r") as f:
        return json.load(f)
```

**3. Приложение сохраняет ЛИЧНЫЕ настройки:**

```python
# Когда пользователь меняет UI
config['ui']['scale_factor'] = 1.25  # Настройка для macOS
config['window']['width'] = 800      # Размер окна

# Сохраняется в config_qt.json (локальный)
with open("config_qt.json", "w") as f:
    json.dump(config, f)
```

### 📊 Разделение ответственности:

| Параметр | Где хранится | Кто управляет |
|----------|--------------|---------------|
| **Версия проекта** | `*.template` | Разработчик (Git) |
| **Edition** | `*.template` | Разработчик (Git) |
| **Дата релиза** | `*.template` | Разработчик (Git) |
| **PIN-код по умолчанию** | `*.template` | Разработчик (Git) |
| | | |
| **scale_factor** | локальный `*.json` | Пользователь (локально) |
| **window width/height** | локальный `*.json` | Пользователь (локально) |
| **theme (dark/light)** | локальный `*.json` | Пользователь (локально) |
| **view_mode** | локальный `*.json` | Пользователь (локально) |

### 🔄 Жизненный цикл:

**Разработка:**

```bash
# 1. Запуск из папки проекта
cd /Users/user/Project/BOMCategorizer
python app_qt.py

# 2. При первом запуске
if not exists("config_qt.json"):
    copy("config_qt.json.template" → "config_qt.json")

# 3. Приложение работает с config_qt.json
# Сохраняет личные настройки (scale_factor: 1.25)

# 4. Git игнорирует config_qt.json
# Личные настройки не попадут на GitHub
```

**Пользователь на другой машине:**

```bash
# 1. Клонирует репозиторий
git clone <repo>  # Получает только *.template файлы

# 2. Запускает приложение
python app_qt.py

# 3. Создается config_qt.json из template
# scale_factor: 1.0 (по умолчанию из template)

# 4. Пользователь настраивает UI под свой экран
# scale_factor: 0.8 для маленького экрана

# 5. Настройки сохраняются в локальный config_qt.json
```

### 💡 Конкретные примеры:

**Масштаб UI на разных машинах:**

```json
// config_qt.json.template (Git, для всех)
{
  "ui": {
    "scale_factor": 1.0  ← Универсальное значение
  }
}

// config_qt.json на macOS (локально)
{
  "ui": {
    "scale_factor": 1.25  ← Для большого экрана Retina
  }
}

// config_qt.json на Windows (локально)
{
  "ui": {
    "scale_factor": 0.8  ← Для маленького экрана
  }
}
```

**Размер окна:**

```json
// template: стандартный размер
"window": {
  "width": 720,
  "height": 900
}

// Локальный config после использования:
"window": {
  "width": 1200,  ← Пользователь растянул окно
  "height": 1400
}
```

### 🏢 В production (установленное приложение):

**macOS (.app bundle):**
```
BOM Categorizer.app/
├── Contents/
│   └── Resources/
│       ├── config_qt.json.template  ← Включен в сборку
│       └── config_qt.json           ← Создается при первом запуске
│                                      в ~/Library/Application Support/
```

**Windows (installer):**
```
C:\Users\User\AppData\Roaming\BOMCategorizerModern\
├── config_qt.json.template  ← Из installer
└── config_qt.json           ← Создается при первом запуске
```

### ⚠️ Важные нюансы:

**1. Обновление версии приложения:**

Когда пользователь обновляет приложение (например, 4.2.3 → 4.3.0):

- ✅ Новый `config_qt.json.template` приходит с новой версией
- ✅ Старый `config_qt.json` сохраняется с личными настройками
- ✅ Приложение может обновить номер версии в локальном config
- ✅ Личные настройки (scale_factor, window size) НЕ трогаются

**2. Сброс настроек:**

```bash
# Удалить локальный config
rm config_qt.json

# При следующем запуске создастся новый из template
# Все настройки вернутся к дефолтным
```

### 📝 Резюме:

| Вопрос | Ответ |
|--------|-------|
| **Когда создаются?** | При первом запуске приложения |
| **Откуда берутся?** | Копируются из `*.template` |
| **Кто их использует?** | Приложение во время работы |
| **Где хранятся?** | В папке проекта (dev) или AppData (production) |
| **Что в них хранится?** | Версия + личные настройки пользователя |
| **Попадают в Git?** | ❌ Нет (в `.gitignore`) |
| **Можно удалить?** | ✅ Да, пересоздадутся из template |

**TL;DR:** Локальные config файлы - это "рабочая копия" для каждого пользователя/машины, где хранятся личные настройки UI. Шаблоны - это "эталон" с версией проекта и дефолтными настройками для всех.

---

## Рабочий процесс

### 🎯 Сценарий 1: Релиз новой версии

```bash
# 1. Обновить версию Modern Edition
python update_version.py set modern 4.3.0

# 2. Проверить статус
python update_version.py status

# 3. Закоммитить изменения
git add config/config_qt.json.template deployment/installer_qt.iss
git commit -m "Release: Modern Edition v4.3.0"

# 4. Собрать проект
./deployment/build_macos.sh              # macOS
# или
python deployment/build_installer.py     # Windows
```

### 🎯 Сценарий 2: Работа на новой машине

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd BOMCategorizer

# 2. Проверить версии (покажет только шаблоны, т.к. локальных config еще нет)
python update_version.py status

# 3. Синхронизировать файлы сборки
python update_version.py sync

# 4. При первом запуске приложения создастся config.json из шаблона
python app_qt.py

# 5. После создания локальных config, проверьте синхронизацию
python update_version.py status
# Если версии отличаются, выполните: python update_version.py sync
```

### 🎯 Сценарий 3: Переключение веток

```bash
# 1. Переключиться на другую ветку
git checkout experimental/new-feature

# 2. Проверить версии (может показать расхождения)
python update_version.py status

# 3. Если версии отличаются, синхронизировать
python update_version.py sync

# 4. Проверить результат
python update_version.py status
```

---

## FAQ

### ❓ Что делать, если версии рассинхронизировались?

**Шаг 1:** Проверьте статус версий:
```bash
python update_version.py status
```

Команда покажет:
- Версии в шаблонах (источник правды)
- Версии в локальных config файлах
- Предупреждение, если версии отличаются

**Шаг 2:** Если версии отличаются, выполните синхронизацию:
```bash
python update_version.py sync
```

Это обновит:
- Локальные `config.json` и `config_qt.json` (только секция `app_info`)
- Файлы сборки `.iss` (синхронизируются с шаблонами)

**Важно:** Ваши личные настройки (scale_factor, window size, theme) не будут затронуты.

### ❓ Как узнать текущую версию?

```bash
python update_version.py status
```

Команда покажет версии в:
- ✅ Шаблонах (`config*.json.template`) — источник правды
- ✅ Локальных файлах (`config*.json`) — если они существуют
- ✅ Предупреждение, если версии отличаются, с рекомендацией выполнить `sync`

### ❓ Можно ли редактировать config.json напрямую?

**Не рекомендуется** для версий. Файл `config.json` - это локальные настройки пользователя (scale_factor, window size, и т.д.).

Для версий используйте только `config.json.template`.

### ❓ Почему config.json в .gitignore?

Чтобы локальные настройки пользователя (размер окна, масштаб UI) не попадали в Git. Каждая машина может иметь свои настройки, но версия проекта одна для всех.

### ❓ Что будет, если забыть синхронизировать .iss?

Windows installer соберется со старой версией. MacOS сборка будет с правильной версией (читает из шаблона автоматически).

**Решение:** Всегда запускайте `python update_version.py sync` перед сборкой.

### ❓ Команда sync обновит мои личные настройки?

**Нет!** Команда `sync` обновляет **только** секцию `app_info` в локальных config файлах:
- ✅ Обновляет: `version`, `release_date`, `last_updated`
- ❌ **НЕ трогает**: `scale_factor`, `window` (width/height), `theme`, `view_mode` и другие личные настройки

Ваши настройки UI останутся без изменений.

---

## Поддержка

При возникновении проблем с версиями:

1. **Проверьте статус:**
   ```bash
   python update_version.py status
   ```
   Команда покажет все версии и обнаружит расхождения.

2. **Синхронизируйте, если нужно:**
   ```bash
   python update_version.py sync
   ```
   Это обновит локальные config и файлы сборки.

3. **Посмотрите справку:**
   ```bash
   python update_version.py help
   ```
   Или `python update_version.py` без аргументов.

### Типичные проблемы:

**Проблема:** После `git pull` версии в локальных config отличаются от шаблонов  
**Решение:** Выполните `python update_version.py sync`

**Проблема:** Windows installer собирается со старой версией  
**Решение:** Выполните `python update_version.py sync` перед сборкой

**Проблема:** Не знаю, какая версия сейчас в проекте  
**Решение:** Выполните `python update_version.py status`

---

**Последнее обновление:** 13.11.2025  
**Автор:** Куреин М.Н.

