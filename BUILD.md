# ⚙️ Инструкция по сборке и релизу

Этот документ описывает полный цикл подготовки релиза: от обновления версии до создания инсталляторов.

> **Быстрый старт (Makefile):**
> ```bash
> make help              # Показать все доступные команды
> make version-status    # Проверить текущие версии
> make version-sync      # Синхронизировать версии
> make build-macos       # Собрать macOS DMG
> make run-qt            # Запустить Modern Edition
> ```
>
> **Альтернативный способ (без Makefile):**
> *   **Windows:** `python deployment/build_installer.py`
> *   **macOS:** `./deployment/build_macos.sh` (не `/deployment/...` — это разные пути!)
> *   **Версии:** `python3 tools/update_version.py status`
>
> ⚠️ **macOS:** Используйте `python3` вместо `python` для всех команд.

---

## 🔄 1. Управление версиями (Versioning)

В проекте используется **централизованная система версий**. 
Единственный источник правды — это **шаблоны конфигурации**.

### 📂 Где хранятся версии?
*   **Standard Edition:** `config/config.json.template`
*   **Modern Edition:** `config/config_qt.json.template`

> ⚠️ **Важно:** Никогда не меняйте версию вручную в локальных файлах `config.json` или `.iss`. Используйте утилиту `tools/update_version.py`.

### 🛠 Пошаговый процесс обновления

#### Шаг 1: Проверка текущего статуса
Перед началом работы проверьте, синхронизированы ли версии.

```bash
# Windows
python tools/update_version.py status

# macOS / Linux
python3 tools/update_version.py status
```
*Если есть расхождения, скрипт предложит выполнить синхронизацию.*

#### Шаг 2: Установка новой версии
Используйте команду `set` для обновления версии. Скрипт автоматически обновит шаблоны, дату релиза и синхронизирует все файлы.

```bash
# Обновить только Modern Edition
python3 tools/update_version.py set modern 4.5.0

# Обновить только Standard Edition
python3 tools/update_version.py set standard 3.5.0

# Обновить обе версии сразу (рекомендуется для мажорных релизов)
python3 tools/update_version.py set both 5.0.0
```

#### Шаг 3: Синхронизация (если нужно)
Команда `set` делает это автоматически, но если вы скачали обновления из Git, выполните:

```bash
python3 tools/update_version.py sync
```
**Что делает sync:**
1.  Обновляет локальные `config.json` / `config_qt.json` (не трогая ваши настройки).
2.  Обновляет файлы инсталлятора `deployment/installer_clean.iss` и `deployment/installer_qt.iss`.
3.  Обновляет захардкоженные версии в Python коде.

---

## 📦 2. Сборка инсталляторов (Build)

После того как версии обновлены, можно приступать к сборке.

### 🪟 Windows

Для сборки используется скрипт `deployment/build_installer.py`, который автоматически управляет компилятором Inno Setup.

**Запуск:**
```powershell
python deployment/build_installer.py
```

> 💡 **Примечание:** На Windows обычно работает команда `python`, но если нет — используйте `python3` или `py`.

**Процесс:**
1.  Скрипт спросит, какую версию собирать (1 - Standard, 2 - Modern).
2.  Создаст временную папку `temp_installer`.
3.  Скопирует туда код, зависимости и документацию.
4.  Запустит Inno Setup Compiler.
5.  Готовый `.exe` появится в корне проекта.

> **Результат:** `BOMCategorizerModernSetup.exe` или `BOMCategorizerSetup.exe`

### 🍎 macOS

Для сборки используется скрипт `deployment/build_macos.sh`, который создает `.dmg` образ.

**Запуск (рекомендуется):**
```bash
make build-macos
```

**Или напрямую:**
```bash
# Важно: используйте ./ в начале (относительный путь)
./deployment/build_macos.sh

# ❌ НЕ используйте абсолютный путь:
# /deployment/build_macos.sh  — это ошибка!
```

**Процесс:**
1.  Скрипт автоматически синхронизирует версии.
2.  Спросит, какую версию собирать (Standard/Modern).
3.  Запустит `py2app` для создания `.app` бандла.
4.  Упакует `.app` в `.dmg` образ.

> **Результат:** `BOMCategorizer-5.5.1-macOS-Modern.dmg`

---

## 🚀 3. Публикация (Release)

Рекомендуемый workflow для создания релиза на GitHub:

1.  **Подготовка:**
    ```bash
    python3 tools/update_version.py status  # Проверяем, что все чисто
    ```

2.  **Обновление:**
    ```bash
    python3 tools/update_version.py set modern 4.5.0
    ```

3.  **Сборка:**
    ```bash
    python deployment/build_installer.py  # Собираем Windows
    ./deployment/build_macos.sh           # Собираем macOS (если есть Mac)
    ```

4.  **Git Commit:**
    ```bash
    git add config/config_qt.json.template config/config.json.template
    git add deployment/installer_qt.iss deployment/installer_clean.iss
    git commit -m "Release: v4.5.0"
    git tag v4.5.0
    git push origin main --tags
    ```

5.  **GitHub Release:**
    Загрузите созданные `.exe` и `.dmg` файлы в новый релиз на GitHub.

---

## 🐛 Устранение неполадок

### ❌ Ошибка "Inno Setup не найден"
Скрипт ищет компилятор в `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`.
Если у вас другой путь, отредактируйте `deployment/build_installer.py`:
```python
INNO_SETUP_PATH = r"D:\Apps\Inno Setup 6\ISCC.exe"
```

### ❌ Ошибка "PySide6 не найден" в offline_packages
Если при сборке Modern Edition возникает ошибка с зависимостями:
1.  Удалите папку `offline_packages`.
2.  Запустите сборку заново — скрипт попытается скачать пакеты.
3.  Или скачайте вручную:
    ```powershell
    pip download PySide6 -d offline_packages --platform win_amd64 --python-version 313 --only-binary=:all:
    ```

### ❌ Версии рассинхронизировались
Если `status` показывает красные предупреждения:
1.  Запустите `python3 tools/update_version.py sync`.
2.  Это принудительно приведет все файлы к состоянию шаблонов.

### ❌ Ошибка "command not found: python" (macOS)
На macOS Python 3 доступен как `python3`, а не `python`.
Замените `python` на `python3` во всех командах.
