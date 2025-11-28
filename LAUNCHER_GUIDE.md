# 🚀 Руководство по запуску BOM Categorizer

Это руководство поможет вам быстро запустить приложение в Windows и WSL, а также настроить удобное окружение для разработки.

---

## ⚡️ Быстрая справка (Cheatsheet)

### 🪟 Windows (Для пользователей)
*   **Modern Edition (Красивый UI):** Запустите `scripts/run_modern_debug.bat`
*   **Standard Edition (Классика):** Запустите `scripts/run_standard_debug.bat`
*   *Совет: Создайте ярлык на рабочем столе для быстрого доступа.*

### 🐧 WSL / Linux (Для разработчиков)
```bash
# Быстрый запуск (если настроен alias)
wa

# Ручной запуск
source .venv-wsl/bin/activate
python3 app_qt.py
```

---

## 📋 Предварительные требования

### Для Windows
1.  **Python 3.13+** установлен.
2.  Папка проекта находится где угодно (скрипты автоматически определяют путь).
3.  Виртуальное окружение `.venv` создано (скрипт создаст его автоматически при первом запуске).

### Для WSL / Linux
1.  **Python 3.10+** и **pip**.
2.  Установленные пакеты `requirements.txt`.
3.  (Опционально) **Alacritty** + **Zellij** для продвинутого терминала.

---

## 🪟 Windows: Запуск через .bat файлы

В директории `scripts/` находятся готовые скрипты для запуска. Они автоматически:
- Переходят в корневую папку проекта
- Активируют виртуальное окружение
- Запускают приложение в режиме отладки (с консолью)

### Доступные варианты
| Файл | Версия | Описание |
|------|--------|----------|
| **`scripts/run_modern_debug.bat`** | **Modern** | PySide6 (Qt). Современный интерфейс, темная/светлая темы. **Рекомендуется.** |
| **`scripts/run_standard_debug.bat`** | **Standard** | Tkinter. Классический, простой интерфейс. |
| **`scripts/run_app.bat`** | **Auto** | Универсальный запуск с первоначальной настройкой. |

### Преимущества .bat файлов
*   ✅ **Работает отовсюду:** Скрипты автоматически определяют путь к проекту (не нужно хардкодить).
*   ✅ **Авто-настройка:** Создают виртуальное окружение при первом запуске.
*   ✅ **Диагностика:** Окно консоли остается открытым после закрытия программы.

---

## 🐧 WSL / Linux: Продвинутый запуск

### Вариант 1: Alacritty + Zellij (Рекомендуется)
Используйте нашу готовую конфигурацию для максимальной продуктивности.

1.  **Запуск:** Введите `wa` в адресной строке проводника (в папке проекта) или в терминале.
2.  **Layout:** Выберите пункт **4) BOM Categorizer** (если настроен) или загрузите вручную:
    ```bash
    zellij --layout bom-categorizer.kdl
    ```
    *Это откроет 2 таба: один для запуска приложения, второй с LazyVim для кода.*

### Вариант 2: Ручной запуск (Терминал)

**Онлайн (с интернетом):**
```bash
cd /mnt/c/Project/BOMCategorizer
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
pip install -r requirements.txt
python3 app_qt.py
```

**Оффлайн (без интернета):**
*Требуется папка `offline-packages-linux/` в корне проекта.*
```bash
source .venv-wsl/bin/activate
pip install --no-index --find-links=offline-packages-linux -r requirements.txt
python3 app_qt.py
```

---

## 🍎 macOS: Запуск приложения

### Вариант 1: Установленное приложение (.app bundle)

Если вы установили приложение из DMG файла:

1. **Запуск через Finder:**
   - Откройте папку **Applications**
   - Найдите **BOM Categorizer Modern Edition.app** или **BOM Categorizer Standard.app**
   - Двойной клик для запуска

2. **Запуск через Spotlight:**
   - Нажмите `Cmd + Space`
   - Введите "BOM Categorizer"
   - Нажмите `Enter`

3. **Запуск через Dock:**
   - Перетащите приложение из Applications в Dock для быстрого доступа

#### 🔒 Первый запуск (Gatekeeper)

При первом запуске macOS может заблокировать приложение:

1. **Способ 1 (рекомендуется):**
   - Нажмите правой кнопкой на приложение
   - Выберите **"Открыть"**
   - В диалоге нажмите **"Открыть"** еще раз

2. **Способ 2 (через Настройки):**
   - Откройте **Системные настройки** → **Безопасность и конфиденциальность**
   - Внизу увидите сообщение о заблокированном приложении
   - Нажмите **"Открыть в любом случае"**

### Вариант 2: Запуск из исходного кода (для разработчиков)

#### Первоначальная настройка

```bash
# 1. Клонируйте репозиторий
cd ~/Projects
git clone https://github.com/kureinmaxim/BOMCategorizer.git
cd BOMCategorizer

# 2. Создайте виртуальное окружение
python3 -m venv venv

# 3. Активируйте окружение
source venv/bin/activate

# 4. Установите зависимости
# python -m pip install -r requirements.txt # old
pip install -r requirements.txt
```

#### Запуск приложения

```bash
# Активируйте окружение (если еще не активировано)
source venv/bin/activate

# Modern Edition (PySide6)
python3 app_qt.py

# Standard Edition (Tkinter)
python3 app.py
```

#### Создание alias для быстрого запуска

Добавьте в `~/.zshrc` или `~/.bash_profile`:

```bash
# BOM Categorizer aliases
alias bom-modern='cd ~/Projects/BOMCategorizer && source venv/bin/activate && python3 app_qt.py'
alias bom-standard='cd ~/Projects/BOMCategorizer && source venv/bin/activate && python3 app.py'
alias bom-cd='cd ~/Projects/BOMCategorizer'
```

Затем:
```bash
source ~/.zshrc  # или source ~/.bash_profile
```

Теперь можно запускать просто: `bom-modern`

### Вариант 3: Сборка собственного .app bundle

Если вы разработчик и хотите создать собственный инсталлятор:

```bash
# 1. Перейдите в папку проекта
cd ~/Projects/BOMCategorizer

# 2. Запустите скрипт сборки
./deployment/build_macos.sh

# 3. Следуйте инструкциям в интерактивном меню:
#    - Выберите версию (Modern или Standard)
#    - Дождитесь завершения сборки
#    - DMG файл появится в папке dist/
```

**Результат:**
- `.app` bundle в папке `dist/`
- `.dmg` образ для распространения

### 📁 Доступ к файлам внутри .app bundle

Если нужно получить доступ к конфигурации или базе данных:

**Через Finder:**
1. Найдите приложение в Applications
2. Правой кнопкой → **"Показать содержимое пакета"**
3. Перейдите в `Contents/Resources/`
4. Здесь находятся:
   - `config_qt.json` или `config.json`
   - `component_database.json`
   - `rules.json`

**Через Terminal:**
```bash
# Перейти в ресурсы Modern Edition
cd "/Applications/BOM Categorizer Modern Edition.app/Contents/Resources"

# Посмотреть конфигурацию
cat config_qt.json

# Сделать резервную копию БД
cp component_database.json ~/Desktop/database_backup_$(date +%Y%m%d_%H%M%S).json
```

### 🔧 Управление базой данных на macOS

**Резервное копирование:**
```bash
# Для установленного приложения
cp "/Applications/BOM Categorizer Modern Edition.app/Contents/Resources/component_database.json" \
   ~/Desktop/db_backup_$(date +%Y%m%d).json

# Для разработки
cp ~/Projects/BOMCategorizer/component_database.json \
   ~/Desktop/db_backup_$(date +%Y%m%d).json
```

**Экспорт в Excel (через Python):**
```bash
cd "/Applications/BOM Categorizer Modern Edition.app/Contents/Resources"
./MacOS/python -c "from bom_categorizer.component_database import export_database_to_excel; export_database_to_excel('~/Desktop/db_export.xlsx')"
```

### 🐛 Отладка на macOS

**Запуск с выводом в терминал:**
```bash
# Для установленного приложения
"/Applications/BOM Categorizer Modern Edition.app/Contents/MacOS/BOM Categorizer Modern Edition"

# Это покажет все print() и ошибки в терминале
```

**Просмотр логов системы:**
```bash
# Логи приложения
log show --predicate 'process == "BOM Categorizer Modern Edition"' --last 1h

# Или через Console.app
open -a Console
```

---

## ⚙️ Сравнение версий

| Характеристика | Modern Edition | Standard Edition |
|---------------|----------------|------------------|
| **Интерфейс** | PySide6 (Qt) 🎨 | Tkinter 😐 |
| **Темы** | Темная / Светлая | Только системная |
| **Дизайн** | Современный, анимации | Базовый, утилитарный |
| **Файл запуска** | `app_qt.py` | `app.py` |

---

## 🛠 Устранение проблем

| Проблема | Решение |
|----------|---------|
| **Не запускается .bat файл** | Убедитесь, что запускаете из папки `scripts/`. Скрипт автоматически перейдёт в корень проекта. |
| **Python executable not found** | Виртуальное окружение не создано. Запустите `scripts/run_app.bat` для первичной настройки. |
| **did not find executable (WSL)** | Вы пытаетесь использовать `.venv` от Windows в WSL (или наоборот). Удалите папку `.venv` и создайте `.venv-wsl` для Linux. |
| **No matching distribution pywin32** | В Linux/macOS используйте `requirements.txt` — `pywin32` автоматически пропускается на Linux/macOS. |
| **Не находит config/rules файлы** | После рефакторинга конфиги в `config/`, база данных в `data/`. Приложение автоматически создаст их при первом запуске. |

## 💡 Полезные советы
*   **Ярлыки:** Создайте ярлык для `.bat` файла из `scripts/`, нажмите `Свойства` -> `Сменить значок`, чтобы сделать красиво.
*   **SendTo:** Добавьте ярлык в папку `shell:sendto`, чтобы открывать файлы через "Отправить -> BOM Categorizer".
*   **Оффлайн режим:** Используйте `offline-packages-linux` для установки зависимостей на изолированных машинах.
*   **Обновление версии:** Используйте `tools/update_version.py` для синхронизации версий между конфигами и инсталляторами.

