# 🔤 Решение проблем отображения в BOM Categorizer

Документ описывает решения проблем с отображением текста, шрифтов и символов на разных платформах.

---

## 📋 Содержание

1. [Кириллица в PDF](#-кириллица-в-pdf)
2. [Шрифты на macOS Retina](#-шрифты-на-macos-retina)
3. [Эмодзи в Windows консоли](#-эмодзи-в-windows-консоли)

---

## 📄 Кириллица в PDF

### Проблема

После установки программы на новой машине кириллица в PDF файлах отображается некорректно (квадратиками или знаками вопроса).

### Причина

Программа использует ReportLab для создания PDF. Для корректного отображения кириллицы необходимы TrueType шрифты с поддержкой кириллических символов.

**Порядок поиска шрифтов:**

| Приоритет | Источник | Шрифт |
|-----------|----------|-------|
| 1 | Папка приложения | `{app}/fonts/DejaVuSans.ttf` |
| 2-3 | Системные | Arial (Windows/macOS) |
| 4 | Системные | DejaVuSans |
| 5 | Пакет reportlab | DejaVu |
| 6 | Системные Windows | Times New Roman |
| 7 | Fallback ⚠️ | Helvetica (БЕЗ кириллицы!) |

### Решение 1: Пересборка инсталлятора (рекомендуется)

```powershell
# Шаг 1: Скачать шрифты
.\download_fonts.ps1

# Или вручную: https://dejavu-fonts.github.io/
# Скопировать DejaVuSans.ttf и DejaVuSans-Bold.ttf в папку fonts/

# Шаг 2: Собрать инсталлятор
python build_installer.py

# Шаг 3: Установить на проблемную машину
```

**Преимущества:**
- ✅ Решает проблему для всех пользователей
- ✅ Не требует прав администратора
- ✅ Работает офлайн

### Решение 2: Ручная установка шрифтов

**Windows (без прав администратора):**
```
1. Скачайте DejaVu Sans с https://dejavu-fonts.github.io/
2. Создайте папку: C:\Users\{Вы}\AppData\Roaming\BOMCategorizerModern\fonts\
3. Скопируйте DejaVuSans.ttf и DejaVuSans-Bold.ttf
4. Перезапустите приложение
```

**Windows (с правами администратора):**
```
1. Скачайте шрифты
2. Правой кнопкой → "Установить для всех пользователей"
```

**macOS:**
```bash
brew tap homebrew/cask-fonts
brew install --cask font-dejavu
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu fonts-dejavu-core

# Fedora
sudo dnf install dejavu-sans-fonts

# Arch
sudo pacman -S ttf-dejavu
```

### Диагностика

```bash
# Проверить доступные шрифты
python check_pdf_fonts.py
# или
check_pdf_fonts.bat
```

**Успешно:**
```
✓ Зарегистрированы шрифты: DejaVuSans из папки приложения (поддержка кириллицы)
```

**Проблема:**
```
⚠️ ВНИМАНИЕ: Не удалось зарегистрировать шрифты с поддержкой кириллицы!
Кириллические символы в PDF будут отображаться некорректно.
```

### Inno Setup конфигурация

```iss
[Files]
; Встраиваем шрифты в инсталлятор
Source: "fonts\*.ttf"; DestDir: "{app}\fonts"; Flags: ignoreversion; Check: FontsExist

[Code]
function FontsExist: Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\fonts'));
end;
```

---

## 🖥️ Шрифты на macOS Retina

### Проблема

На macOS с Retina дисплеями (2x DPI) шрифты в Modern Edition отображались **в 2 раза меньше** чем на Windows.

**Симптомы:**
- Мелкие метки полей
- Мелкий текст на кнопках
- Мелкие плейсхолдеры
- При этом заголовки были крупными (из-за CSS)

### Решение

Реализованы macOS-специфичные исправления в `gui_qt.py`.

#### 1. High DPI Support в Qt

```python
# В main() ДО создания QApplication:
if platform.system() == 'Darwin':
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
```

#### 2. Глобальный шрифт для macOS

```python
# В main() ПОСЛЕ создания QApplication:
if platform.system() == 'Darwin':
    screens = QGuiApplication.screens()
    if screens and screens[0].devicePixelRatio() >= 2:
        base_size = 18  # Retina
    else:
        base_size = 14  # Обычный дисплей
    
    app_font = QFont(get_system_font(), base_size)
    app.setFont(app_font)
```

#### 3. Удаление font-size из CSS на macOS

```python
def apply_theme(self):
    theme_style = DARK_THEME if self.current_theme == "dark" else LIGHT_THEME
    
    # На macOS удаляем все font-size из стилей
    if platform.system() == 'Darwin':
        import re
        theme_style = re.sub(r'\s*font-size:\s*\d+pt;', '', theme_style)
    
    self.setStyleSheet(theme_style)
```

### Результаты

| Параметр | Windows/Linux | macOS (не Retina) | macOS (Retina) |
|----------|---------------|-------------------|----------------|
| **base_font_size** | 12pt | 14pt | 18pt |
| **default_scale** | 0.8 | 1.1 | 1.1 |
| **Итоговый размер** | 9.6pt | 15.4pt | 19.8pt |
| **font-size в CSS** | ✅ Используется | ❌ Удаляется | ❌ Удаляется |

### Особенности

- Автоматическое определение Retina: `devicePixelRatio() >= 2`
- Fallback на большие шрифты если DPI не определён
- Пользователь может изменить `scale_factor` через меню
- Совместимость с Qt 5 и Qt 6

---

## 💻 Эмодзи в Windows консоли

### Проблема

При выводе эмодзи (✅ 💡 ℹ️) в Windows консоли возникала ошибка:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'
```

**Причина:** Windows консоль по умолчанию использует cp1251, которая не поддерживает Unicode.

### Решение: Многоуровневая защита

#### Уровень 1: UTF-8 для консоли

```python
import sys
import io

def setup_console_encoding():
    """Настраивает UTF-8 для корректного вывода эмодзи в Windows"""
    if sys.platform == 'win32':
        try:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, 
                    encoding='utf-8', 
                    errors='replace'
                )
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, 
                    encoding='utf-8', 
                    errors='replace'
                )
        except Exception:
            pass

# Вызываем при запуске
setup_console_encoding()
```

#### Уровень 2: Класс эмодзи

```python
class Emoji:
    """Централизованное хранение эмодзи"""
    CHECK = '✅'
    INFO = 'ℹ️'
    WARN = '💡'
    ERROR = '❌'
    SYNC = '🔄'
    ARROW = '→'
```

#### Уровень 3: Безопасный вывод с fallback

```python
def safe_print(text):
    """Безопасный вывод с fallback на текст"""
    try:
        print(text)
    except UnicodeEncodeError:
        fallback = text
        fallback = fallback.replace(Emoji.CHECK, '[OK]')
        fallback = fallback.replace(Emoji.INFO, '[INFO]')
        fallback = fallback.replace(Emoji.WARN, '[WARN]')
        fallback = fallback.replace(Emoji.ERROR, '[ERROR]')
        fallback = fallback.replace(Emoji.SYNC, '[SYNC]')
        fallback = fallback.replace(Emoji.ARROW, '->')
        print(fallback)
```

#### UTF-8 для subprocess

```python
result = subprocess.run(
    [sys.executable, 'script.py'],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace',
    check=False
)
```

### Использование

```python
# ❌ Может упасть
print("✅ Готово")

# ✅ Всегда работает
safe_print(f"{Emoji.CHECK} Готово")
```

### Результат

```
✅ Modern Edition: 4.3.1 → 4.3.2
   Дата обновлена: 13.11.2025

✅ Версия обновлена в шаблонах
ℹ️ Синхронизирую файлы сборки...
🔄 СИНХРОНИЗАЦИЯ ФАЙЛОВ СБОРКИ
```

---

## 📁 Связанные файлы

| Файл | Проблема |
|------|----------|
| `bom_categorizer/pdf_exporter.py` | Кириллица в PDF |
| `bom_categorizer/gui_qt.py` | Шрифты на Retina |
| `bom_categorizer/styles.py` | Темы оформления |
| `update_version.py` | Эмодзи в консоли |
| `sync_installer_versions.py` | Эмодзи в консоли |
| `check_pdf_fonts.py` | Диагностика шрифтов |
| `download_fonts.ps1` | Скачивание шрифтов |

---

## ✅ Чек-лист для разработчиков

### Перед сборкой релиза:

- [ ] Скачаны шрифты: `.\download_fonts.ps1`
- [ ] Файлы существуют: `fonts/DejaVuSans.ttf`, `fonts/DejaVuSans-Bold.ttf`
- [ ] Проверена регистрация: `python check_pdf_fonts.py`
- [ ] Собран инсталлятор: `python build_installer.py`
- [ ] Тестовая установка на чистой машине
- [ ] Создан тестовый PDF с кириллицей ✓
- [ ] Протестировано на macOS Retina (если доступно)

---

## 📚 Внешние ресурсы

- [DejaVu Fonts](https://dejavu-fonts.github.io/) — шрифты с кириллицей
- [ReportLab Documentation](https://docs.reportlab.com/) — создание PDF
- [Qt High DPI](https://doc.qt.io/qt-6/highdpi.html) — масштабирование Qt

---

**Последнее обновление:** 25.11.2025  
**Версия документа:** 1.0


