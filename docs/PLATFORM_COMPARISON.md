# 🖥️ Сравнение версий Windows vs macOS

**BOM Categorizer** имеет две версии с разными технологиями UI для оптимальной работы на каждой платформе.

---

## 📋 Содержание

1. [Основные различия](#-основные-различия)
2. [Технические отличия](#-технические-отличия)
3. [Windows (Standard Edition) - Workflow](#-windows-standard-edition---workflow)
4. [macOS (Modern Edition) - Workflow](#-macos-modern-edition---workflow)
5. [Кросс-платформенная работа](#-кросс-платформенная-работа)
6. [Управление конфигурацией](#-управление-конфигурацией)
7. [Быстрые команды](#-быстрые-команды)
8. [Решение проблем](#-решение-проблем)
9. [Краткая справка](#-краткая-справка)

---

## 📊 Основные различия

| Характеристика | Windows (Standard) | macOS (Modern) |
|---------------|-------------------|----------------|
| **UI Framework** | Tkinter | PySide6 (Qt) |
| **Издание** | Standard Edition | Modern Edition |
| **Версия** | 3.3.0 | 4.2.3 |
| **Конфиг** | `config.json` | `config_qt.json` |
| **Шаблон** | `config.json.template` | `config_qt.json.template` |
| **Размер окна (default)** | 750×1110 | 720×900 |
| **Масштабирование UI** | ❌ Нет | ✅ 0.8× - 1.5× |
| **Темы оформления** | ❌ Нет | ✅ Light/Dark |
| **Installer** | `installer_clean.iss` | `installer_qt.iss` |
| **Build Script** | `build_installer.py` | `build_macos.sh` |

---

## 🔧 Технические отличия

### Windows (Standard Edition)

**Технологии:**
- Python 3.12+
- Tkinter (встроенная UI библиотека)
- Inno Setup (для создания EXE installer)

**Особенности:**
- Легковесная, быстрая загрузка
- Классический Windows-стиль интерфейса
- Нет зависимостей от внешних UI библиотек
- Меньший размер установщика

**Файлы:**
```
config.json               # Локальный конфиг (не в Git)
config.json.template      # Шаблон для новых установок
installer_clean.iss       # Inno Setup скрипт
build_installer.py        # Python скрипт сборки
```

---

### macOS (Modern Edition)

**Технологии:**
- Python 3.13+
- PySide6 (Qt6 для Python)
- py2app (для создания .app bundle)
- hdiutil (для создания DMG)

**Особенности:**
- Современный Qt интерфейс
- Масштабирование UI (80% - 150%)
- Темная и светлая темы
- Расширенные настройки отображения
- Больший размер приложения

**Файлы:**
```
config_qt.json            # Локальный конфиг (не в Git)
config_qt.json.template   # Шаблон для новых установок
installer_qt.iss          # Inno Setup (для Windows сборки)
build_macos.sh            # Bash скрипт сборки для macOS
setup_macos.py            # py2app конфигурация
```

---

## 🪟 Windows (Standard Edition) - Workflow

### 1️⃣ Первая установка

```powershell
# Клонирование проекта
git clone https://github.com/your-repo/BOMCategorizer.git
cd BOMCategorizer

# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Первый запуск
python app.py
```

**Что происходит:**
1. `initialize_all_configs()` создает `config.json` из `config.json.template`
2. Окно открывается с размером **750×1110** (из template)
3. При закрытии размер автоматически сохраняется в `config.json`

---

### 2️⃣ Изменение размера окна

```
📝 Действия пользователя:
1. Запускаем приложение → окно 750×1110
2. Вручную растягиваем окно до 900×1200
3. Закрываем приложение
   ✅ Размер автоматически сохраняется в config.json

4. Следующий запуск → окно открывается 900×1200
```

**Сохранение размера:**
- **Автоматическое:** При закрытии окна (через ×)
- **Ручное:** Меню → Настройки → Сохранить размер окна

---

### 3️⃣ Сборка установщика (Windows)

```powershell
# Обновление версии
python update_version.py set standard 3.4.0

# Синхронизация installer файлов
python sync_installer_versions.py

# Сборка EXE installer
python build_installer.py
```

**Результат:**
```
Output\BOM_Categorizer_Standard_v3.4.0_Setup.exe
```

**Что включается:**
- ✅ Исполняемый файл `BOMCategorizer.exe`
- ✅ Все зависимости Python
- ✅ Шаблон конфига `config.json.template`
- ✅ База данных компонентов
- ✅ Документация
- ❌ НЕ включается `config.json` (создается при первом запуске)

---

### 4️⃣ Установка на новый ПК

```
1. Запускаем BOM_Categorizer_Standard_v3.4.0_Setup.exe
2. Следуем инструкциям установщика
3. Запускаем установленное приложение
4. ✅ Автоматически создается config.json из template
5. Окно открывается с размером 750×1110
```

---

### 5️⃣ Обновление до новой версии

```powershell
# В папке проекта
git pull origin main

# Если нужно - обновляем зависимости
pip install -r requirements.txt --upgrade

# Запускаем
python app.py
```

**Что сохраняется:**
- ✅ `config.json` с вашими настройками (размер окна, PIN)
- ✅ База данных компонентов
- ✅ История классификаций

**Что обновляется:**
- ✅ Код приложения
- ✅ `config.json.template` (новые дефолтные значения)
- ✅ Версия в шаблоне

---

## 🍎 macOS (Modern Edition) - Workflow

### 1️⃣ Первая установка

```bash
# Клонирование проекта
git clone https://github.com/your-repo/BOMCategorizer.git
cd BOMCategorizer

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements_macos.txt

# Первый запуск
python app_qt.py
```

**Что происходит:**
1. `initialize_all_configs()` создает `config_qt.json` из `config_qt.json.template`
2. Окно открывается с размером **720×900** (из template)
3. UI масштаб: **1.0× (100%)**
4. Тема: **Dark** (по умолчанию)
5. При закрытии размер и настройки сохраняются в `config_qt.json`

---

### 2️⃣ Изменение масштаба UI

```
📝 Сценарий 1: Увеличение масштаба

1. Открываем приложение → 720×900, scale 1.0×
2. Настройки → UI Scale → 125% (1.25×)
3. ✅ Окно автоматически ресайзится:
   - Новая ширина: 720 × 1.25 = 900
   - Новая высота: 900 × 1.25 = 1125
4. Закрываем → сохраняется:
   {
     "window": {"width": 900, "height": 1125},
     "ui": {"scale_factor": 1.25}
   }
5. Следующий запуск → окно 900×1125 с scale 1.25×
```

```
📝 Сценарий 2: Уменьшение масштаба

1. Открываем → 720×900, scale 1.0×
2. Настройки → UI Scale → 80% (0.8×)
3. ✅ Окно ресайзится:
   - Новая ширина: 720 × 0.8 = 576
   - Новая высота: 900 × 0.8 = 720
4. Закрываем → сохраняется 576×720, scale 0.8×
```

---

### 3️⃣ Смена темы

```
📝 Действия:
1. Настройки → Theme → Light/Dark
2. ✅ Интерфейс мгновенно меняет цветовую схему
3. При закрытии сохраняется в config_qt.json:
   {
     "ui": {"theme": "light"}
   }
```

---

### 4️⃣ Сборка DMG installer (macOS)

```bash
# Обновление версии
python update_version.py set modern 4.3.0

# Сборка (автоматически читает версию из template)
chmod +x build_macos.sh
./build_macos.sh
```

**Процесс:**
1. Активирует виртуальное окружение
2. Читает версии из `config_qt.json.template`
3. Создает `.app` bundle через `py2app`
4. Копирует шаблоны конфигов в `.app`
5. Создает DMG образ с инсталлятором

**Результат:**
```
BOM Categorizer Modern v4.3.0.dmg  (macOS-Modern edition)
BOM Categorizer Standard v3.3.0.dmg (macOS-Standard edition)
```

**Что включается в .app:**
- ✅ Python interpreter
- ✅ PySide6 и все зависимости
- ✅ Шаблон конфига `config_qt.json.template`
- ✅ База данных компонентов
- ✅ Документация
- ❌ НЕ включается `config_qt.json` (создается при первом запуске)

---

### 5️⃣ Установка на новый Mac

```
1. Открываем BOM Categorizer Modern v4.3.0.dmg
2. Перетаскиваем .app в Applications
3. Запускаем приложение
4. ✅ Автоматически создается config_qt.json из template
5. Окно открывается 720×900, dark theme, scale 1.0×
```

---

### 6️⃣ Обновление до новой версии

```bash
# В папке проекта
git pull origin main

# Обновляем зависимости
source venv/bin/activate
pip install -r requirements_macos.txt --upgrade

# Запускаем
python app_qt.py
```

**Что сохраняется:**
- ✅ `config_qt.json` с вашими настройками (размер, масштаб, тема)
- ✅ База данных компонентов
- ✅ История классификаций

**Что обновляется:**
- ✅ Код приложения
- ✅ `config_qt.json.template` (новые дефолтные значения)
- ✅ Версия в шаблоне

---

## 🔄 Кросс-платформенная работа

### Сценарий: Разработка на Windows → Тестирование на macOS

```powershell
# На Windows
git checkout -b feature/new-classifier
# ... делаем изменения в коде ...
git add .
git commit -m "Добавлен новый классификатор"
git push origin feature/new-classifier
```

```bash
# На macOS
git fetch origin
git checkout feature/new-classifier
source venv/bin/activate
pip install -r requirements_macos.txt
python app_qt.py  # Тестируем Modern Edition
```

**Что синхронизируется:**
- ✅ Исходный код
- ✅ Шаблоны конфигов (`.template`)
- ✅ База данных компонентов
- ✅ Документация
- ✅ Скрипты сборки

**Что НЕ синхронизируется (игнорируется Git):**
- ❌ `config.json` (локальные настройки Windows)
- ❌ `config_qt.json` (локальные настройки macOS)
- ❌ Виртуальные окружения (`venv/`, `venv_win/`)
- ❌ Собранные установщики (`dist/`, `Output/`)
- ❌ Кеш Python (`__pycache__/`, `*.pyc`)

---

## 📦 Управление конфигурацией

### Windows

```json
// config.json.template (в Git)
{
  "app_info": {
    "version": "3.3.0",
    "edition": "Standard"
  },
  "window": {
    "width": 750,
    "height": 1110
  }
}

// config.json (локальный, игнорируется Git)
{
  "app_info": {
    "version": "3.3.0",
    "edition": "Standard"
  },
  "window": {
    "width": 920,      // ← изменен пользователем
    "height": 1250     // ← изменен пользователем
  },
  "security": {
    "pin": "5678"      // ← персональный PIN
  }
}
```

---

### macOS

```json
// config_qt.json.template (в Git)
{
  "app_info": {
    "version": "4.2.3",
    "edition": "Modern Edition"
  },
  "window": {
    "width": 720,
    "height": 900
  },
  "ui": {
    "theme": "dark",
    "scale_factor": 1.0
  }
}

// config_qt.json (локальный, игнорируется Git)
{
  "app_info": {
    "version": "4.2.3",
    "edition": "Modern Edition"
  },
  "window": {
    "width": 900,          // ← изменен автоматически при scale
    "height": 1125         // ← изменен автоматически при scale
  },
  "ui": {
    "theme": "light",      // ← изменено пользователем
    "scale_factor": 1.25   // ← изменено пользователем
  },
  "security": {
    "pin": "9999"          // ← персональный PIN
  }
}
```

---

## 🚀 Быстрые команды

### Windows

```powershell
# Разработка
python app.py                              # Запуск Standard Edition
python app_qt.py                           # Запуск Modern Edition (если установлен PySide6)

# Версии
python update_version.py status            # Показать текущие версии
python update_version.py set standard 3.4.0  # Обновить Standard
python sync_installer_versions.py          # Синхронизировать .iss файлы

# Сборка
python build_installer.py                  # Собрать Windows installer
```

---

### macOS

```bash
# Разработка
python app.py                              # Запуск Standard Edition (Tkinter)
python app_qt.py                           # Запуск Modern Edition (PySide6)

# Версии
python update_version.py status            # Показать текущие версии
python update_version.py set modern 4.3.0  # Обновить Modern
python sync_installer_versions.py          # Синхронизировать .iss файлы

# Сборка
./build_macos.sh                           # Собрать DMG installer (обе версии)
```

---

## 🆘 Решение проблем

### Windows: Окно не сохраняет размер

**Проблема:** После закрытия и открытия размер сбрасывается.

**Решение:**
1. Проверьте, что файл `config.json` существует и доступен для записи
2. Убедитесь, что приложение запущено не от имени администратора (ограничивает доступ)
3. Проверьте логи в консоли на ошибки сохранения

```powershell
# Пересоздать config.json из template
del config.json
python app.py  # Создаст новый из template
```

---

### macOS: Масштаб не применяется

**Проблема:** После изменения scale_factor окно не изменяется.

**Решение:**
1. Закройте и откройте приложение заново
2. Проверьте, что `config_qt.json` содержит правильный `scale_factor`

```bash
# Проверить конфиг
cat config_qt.json | grep scale_factor

# Пересоздать из template
rm config_qt.json
python app_qt.py
```

---

### Обе платформы: "Конфиг не найден"

**Проблема:** Приложение не находит файл конфигурации.

**Решение:**
```bash
# Убедитесь, что template файлы существуют
ls -la *.template

# Запустите инициализацию вручную
python -c "from bom_categorizer.config_manager import initialize_all_configs; initialize_all_configs()"

# Или используйте модуль напрямую
python -m bom_categorizer.config_manager
```

---

## 📚 Дополнительная документация

- [**BUILD.md**](../BUILD.md) - Инструкции по сборке установщиков
- [**VERSION_MANAGEMENT.md**](VERSION_MANAGEMENT.md) - Управление версиями
- [**ANALYSIS_PROJECT.md**](../ANALYSIS_PROJECT.md) - Структура проекта (и архитектура)
- [**README.md**](../README.md) - Общая документация

---

## 📋 Краткая справка

| Задача | Windows | macOS |
|--------|---------|-------|
| Запуск Standard | `python app.py` | `python app.py` |
| Запуск Modern | `python app_qt.py` | `python app_qt.py` |
| Обновить версию | `python update_version.py set standard 3.4.0` | `python update_version.py set modern 4.3.0` |
| Собрать installer | `python build_installer.py` | `./build_macos.sh` |
| Сбросить конфиг | `del config.json` | `rm config_qt.json` |
| Проверить версии | `python update_version.py status` | `python update_version.py status` |

---

**Последнее обновление:** 25.11.2025  
**Версия документа:** 1.1

