# Анализ кодовой базы: BOM Categorizer v1.7.6

> **Дата анализа:** 08.10.2025  
> **Тип проекта:** Desktop приложение (Python + Tkinter)  
> **Уровень сложности:** Middle-Senior friendly

---

## 📁 Структура проекта

```
ProjectSnabjenie/
├── 📦 bom_categorizer/              # Основной модуль (модульная архитектура)
│   ├── __init__.py                  # Метаданные модуля (v1.7.5)
│   ├── main.py                      # CLI точка входа и оркестрация
│   ├── classifiers.py               # Классификация компонентов
│   ├── parsers.py                   # Парсеры TXT/DOCX/Excel
│   ├── formatters.py                # Форматирование и очистка данных
│   ├── excel_writer.py              # Запись Excel с форматированием
│   ├── txt_writer.py                # Генерация TXT отчетов
│   ├── utils.py                     # Утилиты и регулярные выражения
│   └── gui.py                       # Tkinter GUI с PIN защитой
│
├── 📄 app.py                        # Entry point для GUI (делегирует в bom_categorizer.gui)
├── 📄 split_bom.py                  # Entry point для CLI (делегирует в bom_categorizer.main)
│
├── ⚙️ config.json                   # Конфигурация (версия, PIN, метаданные)
├── 📋 rules.json                    # Правила автоклассификации (обновляется динамически)
├── 📦 requirements.txt              # Зависимости Python
│
├── 🔧 Скрипты автоматизации:
│   ├── build_installer.py           # Автоматическая сборка инсталлятора
│   ├── start_gui.bat                # Запуск GUI (Windows)
│   ├── split_bom.bat                # Запуск CLI (Windows)
│   ├── run_app.bat                  # Универсальный запуск с выбором
│   └── post_install.ps1             # PowerShell скрипт для post-install
│
├── 📚 docs/                         # Документация
│   ├── QUICK_START.md               # Быстрый старт
│   ├── CLI_USAGE.md                 # Руководство по CLI
│   ├── PROJECT_STRUCTURE.md         # Структура проекта
│   ├── BAT_FILES.md                 # Работа с BAT файлами
│   ├── INTERACTIVE_MODE_GUIDE.md    # Интерактивная классификация
│   ├── TXT_EXPORT_GUIDE.md          # Экспорт в TXT
│   └── OFFLINE_INSTALLER.md         # Оффлайн установка
│
├── 📦 offline_packages/             # Wheel пакеты для оффлайн установки
│   ├── pandas-2.3.3-*.whl
│   ├── openpyxl-3.1.5-*.whl
│   ├── python_docx-1.2.0-*.whl
│   └── ... (12 пакетов)
│
├── 🛠️ Вспомогательные скрипты:
│   ├── interactive_classify.py      # Standalone интерактивная классификация
│   ├── interactive_classify_improved.py
│   └── preview_unclassified.py      # Предпросмотр нераспределенных
│
├── 🔧 Installer:
│   ├── installer_clean.iss          # Скрипт Inno Setup
│   └── BOMCategorizerSetup.exe      # Готовый инсталлятор (генерируется)
│
└── 📝 Прочее:
    ├── README.md                    # Главный README
    ├── BUILD.md                     # Инструкции по сборке
    └── example/                     # Примеры входных файлов
```

### Принцип организации кода

**Feature-based + Layer-based гибрид:**
- **Модульная архитектура** (`bom_categorizer/`) - разделение по слоям ответственности
- **Thin entry points** (`app.py`, `split_bom.py`) - минимальная логика в точках входа
- **Separation of Concerns** - парсинг, классификация, форматирование, вывод разделены
- **Dependency Injection** - функции получают данные через параметры, минимум глобального состояния

---

## 🛠 Технологический стек

| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Язык** | Python | 3.13+ | Основной язык разработки |
| **GUI** | Tkinter | встроен | Графический интерфейс |
| **Обработка данных** | Pandas | 2.3.3 | Манипуляция табличными данными |
| **Excel I/O** | openpyxl | 3.1.5 | Чтение/запись Excel с форматированием |
| **DOCX парсинг** | python-docx | 1.2.0 | Парсинг документов Word |
| **Windows API** | pywin32 | 311 | Интеграция с Windows |
| **Installer** | Inno Setup | 6.x | Создание Windows инсталлятора |
| **Зависимости** | numpy, lxml, dateutil | - | Транзитивные зависимости |

### Инструменты разработки и развертывания

- **Виртуальное окружение:** `venv` (`.venv/` на Windows)
- **Управление пакетами:** `pip` + `requirements.txt` + offline wheels
- **Сборка инсталлятора:** Python script (`build_installer.py`) + Inno Setup
- **Дистрибуция:** Standalone `.exe` инсталлятор с bundled зависимостями
- **Offline support:** Все `.whl` пакеты включены в `offline_packages/`

---

## 🏗 Архитектурные паттерны

### 1. Modular Pipeline Architecture

Основной процесс обработки реализован как пайплайн:

```python
# bom_categorizer/main.py - главная функция main()

def main():
    # 1. Load & Combine (parsers.py)
    df = load_and_combine_inputs(input_paths, sheets_str, sheet)
    
    # 2. Normalize (utils.py)
    df, cols = normalize_and_merge_columns(df)
    
    # 3. Classify (classifiers.py)
    df = run_classification(df, *cols, loose)
    
    # 4. Apply Rules (rules.json)
    df = apply_rules_from_json(df, rules_json, *cols)
    
    # 5. Interactive (если нужно)
    if unclassified_count > 0 and not no_interactive:
        df = interactive_classification(df, *cols, rules_json)
    
    # 6. Group by Category
    outputs = create_outputs_dict(df)
    
    # 7. Write Excel (excel_writer.py)
    write_categorized_excel(outputs, df, xlsx_path, combine)
    
    # 8. Write TXT (txt_writer.py)
    if txt_dir:
        write_txt_reports(outputs, txt_dir, desc_col)
```

### 2. Strategy Pattern для парсеров

```python
# bom_categorizer/parsers.py

def load_and_combine_inputs(input_paths, sheets_str, sheet):
    for input_path in input_paths:
        ext = os.path.splitext(input_path)[1].lower()
        
        if ext in [".txt"]:
            df_txt = parse_txt_like(input_path)  # Strategy 1
            all_rows.append(df_txt)
        
        elif ext in [".doc", ".docx"]:
            df_docx = parse_docx(input_path)     # Strategy 2
            all_rows.append(df_docx)
        
        elif ext in [".xlsx", ".xls"]:
            # Strategy 3 (multiple sheet handling)
            df_excel = parse_excel_with_sheets(input_path, sheets)
            all_rows.append(df_excel)
    
    return pd.concat(all_rows, ignore_index=True)
```

### 3. Rule-based Classification + Machine Learning-like Pattern Matching

```python
# bom_categorizer/classifiers.py - classify_row()

def classify_row(ref, description, value, partname, strict, 
                 source_file, note):
    """
    Многоуровневая классификация:
    1. Context-specific (source file self-reference)
    2. Reference prefix (R*, C*, L*, U*, etc.)
    3. Keyword matching (regex + has_any())
    4. Nominal value patterns (RESISTOR_VALUE_RE, CAP_VALUE_RE)
    5. Manufacturer/part number patterns
    """
    
    # Priority 1: Context
    if is_board_self_reference(description, source_file):
        return "our_developments"
    
    # Priority 2: Reference prefix
    ref_prefix = extract_prefix(ref)
    if ref_prefix.startswith("R"):
        return "resistors"
    
    # Priority 3: Keywords
    if has_any(text_blob, ["резист", "resistor"]):
        return "resistors"
    
    # Priority 4: Regex patterns
    if RESISTOR_VALUE_RE.search(text_blob):
        return "resistors"
    
    return "unclassified"
```

### 4. Data Transformation Pipeline (formatters.py)

```python
# bom_categorizer/formatters.py

# 1. Clean component names
cleaned_name = clean_component_name(original, note)

# 2. Extract TU codes
tu_code = extract_tu_code(description)

# 3. Extract nominal values for sorting
nominal_value, unit = extract_nominal_value(text, category)

# 4. Parse SMD codes (imported components)
if is_smd_code(text):
    nominal_value = parse_smd_code(text)

# 5. Format Excel output
formatted_df = format_excel_output(df, sheet_name, desc_col)
```

### 5. GUI Pattern: MVC-like with Tkinter

```python
# bom_categorizer/gui.py - BOMCategorizerApp

class BOMCategorizerApp(tk.Tk):
    def __init__(self):
        # Model
        self.input_files = []
        self.cfg = load_config()
        
        # View
        self.create_widgets()
        
        # Controller methods
        self.on_add_files()      # File selection
        self.on_run()            # Process files
        self.on_interactive_classify()  # Interactive mode
        
        # Security
        self.lock_interface()    # PIN protection
        self.show_pin_dialog()   # Authentication
```

### 6. Асинхронная обработка в GUI

```python
# bom_categorizer/gui.py

def run_cli_async(args_list, on_finish):
    """Запускает CLI в отдельном потоке для неблокирующего UI"""
    def worker():
        # Redirect stdout/stderr
        buf = StringIO()
        sys.stdout = buf
        sys.stderr = buf
        
        # Run CLI
        cli_main()
        
        # Restore and callback
        output = buf.getvalue()
        on_finish(output)
    
    threading.Thread(target=worker, daemon=True).start()
```

### 7. Dynamic Rule Learning System

```python
# Пользователь классифицирует элемент -> сохраняется в rules.json
# При следующем запуске правила применяются автоматически

def interactive_classification(df, desc_col, ..., rules_json):
    for item in unclassified_items:
        category = ask_user_for_category(item)
        
        # Save rule
        rule = {
            "contains": extract_keyword(item),
            "category": category,
            "comment": f"Добавлено пользователем для '{item}'"
        }
        save_rule_to_json(rule, rules_json)
    
    return df

# rules.json структура:
[
  {
    "contains": "аттенюатор qfa",
    "category": "others",
    "regex": null,
    "comment": "Добавлено пользователем"
  }
]
```

---

## 🎨 UI/UX и стилизация

### Tkinter GUI (bom_categorizer/gui.py)

**Подход к UI:**
- **Native look & feel:** Использование `ttk` для современного вида на Windows
- **Responsive layout:** Grid layout с `weight` для адаптации размеров
- **Accessibility:** Keyboard shortcuts (Enter для подтверждения, Escape для отмены)
- **Visual feedback:** 
  - Цветовое кодирование (зеленый для успеха, красный для ошибок)
  - Shake animation для ошибок ввода PIN
  - Progress indicators в интерактивном режиме

```python
# Пример адаптивного layout
frm.grid_rowconfigure(row+1, weight=1)  # Text area растягивается
frm.grid_columnconfigure(2, weight=1)   # Правая колонка растягивается
```

**Тематизация:**
- Использование стандартных цветов Tkinter
- Кастомизация для PIN protection:
  - 🔒 Темно-зеленый (#2E7D32) для заблокированного состояния
  - Черный для разблокированного
- Визуальный footbar с информацией о разработчике

**Security UX:**
```python
# PIN Dialog с улучшенным UX
- Центрированное модальное окно
- Маскированный ввод (●●●●)
- Визуальная обратная связь при ошибке (shake animation)
- Двойной клик по имени разработчика для разблокировки
```

### Excel Output Styling (excel_writer.py)

**Форматирование вывода:**
- Автоматическое выравнивание колонок
- Центрирование ячеек (кроме текстовых колонок)
- Auto-sizing колонок по содержимому
- Структурированный вывод с пустыми строками между группами

```python
def apply_excel_styles(writer):
    """
    - Замораживание первой строки (заголовки)
    - Выравнивание: center для чисел, left для текста
    - Auto-fit ширины колонок
    """
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        ws.freeze_panes = "A2"  # Freeze header
        
        for column in ws.columns:
            ws.column_dimensions[column[0].column_letter].width = calculated_width
```

---

## ✅ Качество кода

### Линтеры и стандарты

**Конфигурации:** Отсутствуют явные `.pylintrc`, `.flake8`, `pyproject.toml`

**Соглашения по коду:**
- ✅ **UTF-8 encoding:** Все файлы начинаются с `# -*- coding: utf-8 -*-`
- ✅ **Docstrings:** Функции документированы с Args/Returns
- ✅ **Type hints:** Частичное использование (`Optional[str]`, `List[str]`, `Dict[str, pd.DataFrame]`)
- ✅ **Именование:** 
  - `snake_case` для функций и переменных
  - `PascalCase` для классов
  - `UPPER_CASE` для констант и regex паттернов

```python
# Примеры качественного кода

# 1. Docstring со структурой
def load_and_combine_inputs(input_paths: List[str], 
                           sheets_str: Optional[str] = None) -> pd.DataFrame:
    """
    Загружает и объединяет данные из всех входных файлов
    
    Args:
        input_paths: Список путей к входным файлам
        sheets_str: Строка с номерами листов Excel (через запятую)
        
    Returns:
        Объединенный DataFrame со всеми данными
    """
    ...

# 2. Type hints
def enrich_with_mr_and_total(df: pd.DataFrame) -> pd.DataFrame:
    ...

# 3. Константы вынесены в utils.py
RESISTOR_VALUE_RE = re.compile(
    r"(?i)\b\d+(?:[\.,]\d+)?\s*(?:ом|ohm|kohm|к\s*ом)\b"
)
```

### Обработка ошибок

**Паттерны:**
1. **Try-except на уровне парсеров:**
```python
try:
    df_txt = parse_txt_like(input_path)
except Exception as exc:
    print(f"⚠️ Не удалось прочитать TXT '{input_path}': {exc}", file=sys.stderr)
```

2. **Graceful degradation:**
```python
# Если не нашли колонку - используем fallback
desc_col = find_column(["description", "наименование"], df.columns)
if not desc_col:
    df["_row_text_"] = df.apply(lambda r: " ".join(str(x) for x in r.values), axis=1)
    desc_col = "_row_text_"
```

3. **Encoding fallback:**
```python
try:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
except UnicodeDecodeError:
    with open(path, "r", encoding="cp1251", errors="ignore") as f:
        text = f.read()
```

### Тестирование

**Статус:** ❌ Отсутствуют unit/integration тесты

**Альтернативные подходы к QA:**
- ✅ **Extensive documentation** с примерами использования
- ✅ **Example files** в `example/` директории
- ✅ **Helper scripts:** `preview_unclassified.py`, `verify_normalization.py`
- ✅ **Interactive validation:** Пользователь видит результаты классификации и может исправить

**Рекомендации:**
```python
# Предлагаемая структура тестов:
tests/
├── test_parsers.py          # Тесты парсеров TXT/DOCX/Excel
├── test_classifiers.py      # Тесты классификации компонентов
├── test_formatters.py       # Тесты извлечения номиналов и ТУ
├── fixtures/                # Тестовые файлы
│   ├── sample.xlsx
│   ├── sample.docx
│   └── rules_test.json
└── test_integration.py      # End-to-end тесты
```

### Документация в коде

**Качество:** ⭐⭐⭐⭐ (4/5)

- ✅ Все модули имеют module-level docstrings
- ✅ Функции документированы с Args/Returns
- ✅ Сложные регулярные выражения комментированы
- ⚠️ Местами отсутствуют inline комментарии для сложной логики

```python
# Отличный пример документации модуля
"""
Парсеры для различных форматов BOM файлов

Поддерживаемые форматы:
- TXT: текстовые файлы с разделителями
- DOCX: документы Word с таблицами
- Excel: XLSX файлы
"""
```

---

## 🔧 Ключевые компоненты

### 1. `bom_categorizer/classifiers.py` - Ядро классификации

**Назначение:** Классификация электронных компонентов по категориям на основе эвристик

**Основная функция:**
```python
def classify_row(
    ref: Optional[str],        # R1, C2, U3
    description: Optional[str], # "Резистор 100 Ом"
    value: Optional[str],       # "100 Ом"
    partname: Optional[str],    # Артикул
    strict: bool,              # Строгий режим
    source_file: Optional[str], # Имя исходного файла
    note: Optional[str]         # Примечания
) -> str:
    """Возвращает категорию: resistors, capacitors, ics, ..."""
    
    # 1. Context-specific checks (self-referencing boards)
    if is_board_file(source_file, description):
        return "our_developments"
    
    # 2. Reference prefix analysis
    ref_prefix = extract_prefix(ref)  # "R" from "R1-R4"
    if ref_prefix.startswith("R"):
        return "resistors"
    
    # 3. Keyword matching
    text_blob = f"{description} {value} {partname} {note}"
    if has_any(text_blob, ["резист", "resistor"]):
        return "resistors"
    
    # 4. Regex pattern matching
    if RESISTOR_VALUE_RE.search(text_blob):
        return "resistors"
    
    return "unclassified"
```

**Категории (12 штук):**
- `resistors`, `capacitors`, `inductors` - пассивные компоненты
- `ics` - микросхемы
- `semiconductors` - диоды, транзисторы, стабилитроны
- `connectors` - разъемы
- `optics` - оптические компоненты
- `dev_boards`, `rf_modules`, `our_developments` - платы и модули
- `power_modules` - модули питания
- `cables` - кабели
- `others` - прочее (предохранители, генераторы)
- `unclassified` - требуют классификации

**Зависимости:**
- `utils.has_any()` - проверка ключевых слов
- Regex паттерны: `RESISTOR_VALUE_RE`, `CAP_VALUE_RE`, `IND_VALUE_RE`

---

### 2. `bom_categorizer/parsers.py` - Универсальный парсинг

**Назначение:** Чтение BOM данных из разных форматов в единый DataFrame

**Ключевые функции:**

```python
def parse_docx(path: str) -> pd.DataFrame:
    """
    Парсит DOCX с таблицами, обрабатывая:
    - Многострочные заголовки
    - Групповые заголовки (без qty) для ТУ кодов
    - Диапазоны позиционных обозначений (R1-R4)
    """
    doc = Document(path)
    
    # 1. Find table with data
    for table in doc.tables:
        header_row = guess_header_index(table)
        
        # 2. Extract group header info (TU, component type)
        current_group_tu = None
        current_group_type = None
        
        for row in table.rows[header_row+1:]:
            cells = [normalize_cell(cell.text) for cell in row.cells]
            
            # 3. Check if this is a group header
            if is_group_header(cells):
                current_group_tu = extract_tu_from_header(cells)
                current_group_type = extract_type_from_header(cells)
                continue
            
            # 4. Parse data row
            row_data = parse_docx_row(cells, header_cols)
            if current_group_tu:
                row_data["tu"] = current_group_tu
                row_data["note"] = current_group_type
            
            extracted.append(row_data)
    
    return pd.DataFrame(extracted)
```

**Особенности DOCX парсинга:**
- Обработка групповых заголовков (напр: "Резисторы Р1-12 ШКАБ.434110.002 ТУ")
- Извлечение ТУ кодов и применение к последующим строкам
- Разворачивание диапазонов позиций (R1-R4 → R1, R2, R3, R4)

---

### 3. `bom_categorizer/formatters.py` - Обработка данных

**Назначение:** Очистка, нормализация и извлечение метаданных из названий компонентов

**Ключевые функции:**

```python
def clean_component_name(original_text: str, note: str = "") -> str:
    """
    Удаляет префиксы типа "РЕЗИСТОР", "КОНДЕНСАТОР"
    Нормализует единицы: ОМ → Ом, КОМ → кОм
    Убирает $ в конце
    """
    text = original_text.strip().rstrip('$').strip()
    
    # Remove component type prefixes
    for comp_type in ['РЕЗИСТОР', 'КОНДЕНСАТОР', 'МИКРОСХЕМА', ...]:
        if text.upper().startswith(comp_type):
            text = text[len(comp_type):].strip()
    
    # Normalize units
    text = re.sub(r'(\d)\s*ОМ\b', r'\1 Ом', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*КОМ\b', r'\1 кОм', text, flags=re.IGNORECASE)
    
    return text


def extract_nominal_value(text: str, category: str) -> Tuple[Optional[float], str]:
    """
    Извлекает номинал для сортировки компонентов
    
    Примеры:
    - "100 Ом" → (100.0, "Ом")
    - "10 кОм" → (10000.0, "Ом")  # normalized to base unit
    - "1 мкФ" → (0.000001, "Ф")
    """
    if category == "resistors":
        # Search for resistance pattern
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*(ом|ком|мом|ohm)', text, re.I)
        if match:
            value = float(match.group(1).replace(',', '.'))
            unit = match.group(2).lower()
            
            # Convert to base unit (Ohm)
            if unit in ['ком', 'kohm']:
                value *= 1000
            elif unit in ['мом', 'mohm']:
                value *= 1_000_000
            
            return (value, "Ом")
    
    elif category == "capacitors":
        # Similar logic for capacitance
        ...
    
    return (None, "")


def parse_smd_code(text: str) -> Optional[float]:
    """
    Парсит SMD коды импортных резисторов и конденсаторов
    
    Примеры:
    - "0805" → None (это размер корпуса)
    - "102" → 1000.0 (1kΩ для резисторов, 1nF для конденсаторов)
    - "473" → 47000.0
    """
    # 3-digit code: XYZ = XY × 10^Z
    match = re.search(r'\b(\d)(\d)(\d)\b', text)
    if match:
        xy = int(match.group(1) + match.group(2))
        z = int(match.group(3))
        return xy * (10 ** z)
    
    return None
```

---

### 4. `bom_categorizer/excel_writer.py` - Форматированный вывод

**Назначение:** Запись категоризованных данных в Excel с профессиональным форматированием

**Ключевая функция:**

```python
def write_categorized_excel(
    outputs: Dict[str, pd.DataFrame],  # {category: DataFrame}
    df: pd.DataFrame,                  # Исходный DataFrame
    output_xlsx: str,                  # Путь к выходному файлу
    combine: bool,                     # Создать ли SUMMARY лист
    desc_col: str                      # Название колонки с описанием
):
    """
    Записывает Excel файл с листами по категориям
    
    Структура выходного файла:
    - Отладочные платы и модули (комбинированный лист)
    - Микросхемы
    - Резисторы (сортировка по номиналу)
    - Конденсаторы (сортировка по номиналу)
    - ... остальные категории ...
    - SUMMARY (если combine=True)
    - SOURCES (список исходных файлов)
    """
    
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        for key, part_df in outputs.items():
            sheet_name = RUS_SHEET_NAMES[key]  # "resistors" → "Резисторы"
            
            # 1. Enrich with МР code and total quantity
            result_df = enrich_with_mr_and_total(part_df)
            
            # 2. Format for output (add serial numbers, clean names, etc.)
            result_df = format_excel_output(result_df, sheet_name, desc_col)
            
            # 3. Write to Excel
            result_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # 4. Create SUMMARY sheet
        if combine:
            summary = create_summary(outputs)
            summary.to_excel(writer, sheet_name="SUMMARY", index=False)
        
        # 5. Apply styling
        apply_excel_styles(writer)


def format_excel_output(df: pd.DataFrame, sheet_name: str, desc_col: str) -> pd.DataFrame:
    """
    Форматирует DataFrame для финального вывода:
    - Добавляет серийные номера (№ п/п)
    - Очищает наименования компонентов
    - Извлекает ТУ коды
    - Добавляет колонку "Примечание" для типа компонента
    - Сортирует по номиналу (для R, C, L)
    - Удаляет технические колонки
    - Переименовывает колонки для презентации
    """
    
    # Sort by nominal value
    if sheet_name in ["Резисторы", "Конденсаторы", "Индуктивности"]:
        df = sort_by_nominal_value(df, sheet_name)
    
    # Clean names and extract TU
    df["Наименование ИВП"] = df[desc_col].apply(
        lambda x: clean_component_name(x, df.get("note", ""))
    )
    df["ТУ"] = df[desc_col].apply(extract_tu_code)
    
    # Add note column (component type if differs from category)
    df["Примечание"] = df.apply(
        lambda row: get_component_type_note(row, sheet_name), axis=1
    )
    
    # Rename source_file to "Источник"
    df = df.rename(columns={"source_file": "Источник"})
    
    # Drop technical columns
    drop_cols = ["category", "_row_text_", "_merged_qty_", "ед. изм. ктд", "код мр"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    
    # Add serial numbers
    df.insert(0, "№ п/п", range(1, len(df) + 1))
    
    return df
```

---

### 5. `bom_categorizer/gui.py` - Графический интерфейс

**Назначение:** Tkinter GUI с PIN защитой и интерактивной классификацией

**Архитектура класса:**

```python
class BOMCategorizerApp(tk.Tk):
    def __init__(self):
        # Configuration
        self.cfg = load_config()  # from config.json
        self.require_pin = self.cfg.get("security", {}).get("require_pin", False)
        self.correct_pin = self.cfg.get("security", {}).get("pin", "5421")
        
        # State
        self.input_files = []
        self.unlocked = False
        self.lockable_widgets = []  # Widgets to enable/disable
        
        # UI
        self.create_widgets()
        if self.require_pin:
            self.lock_interface()
    
    def create_widgets(self):
        """Создает UI компоненты"""
        # File selection
        self.listbox = tk.Listbox(...)
        ttk.Button(text="Добавить файлы", command=self.on_add_files)
        
        # Options
        self.combine = tk.BooleanVar(value=True)
        ttk.Checkbutton(text="Суммарная комплектация", variable=self.combine)
        
        # Action buttons
        ttk.Button(text="Запустить обработку", command=self.on_run)
        ttk.Button(text="Интерактивная классификация", 
                  command=self.on_interactive_classify)
        
        # Log output
        self.txt = tk.Text(height=10, wrap=tk.WORD)
        
        # Footer with developer info
        self.dev_label = tk.Label(text="Куреин М.Н.", cursor="hand2")
        self.dev_label.bind("<Double-Button-1>", self.on_developer_double_click)
    
    def on_run(self):
        """Асинхронно запускает CLI обработку"""
        args = self._build_args(self.output_xlsx.get())
        
        def after_run(output_text):
            self.txt.insert(tk.END, output_text)
            self.check_and_offer_interactive_classification()
        
        run_cli_async(args, after_run)
    
    def open_classification_dialog(self, df_unclassified, temp_output):
        """Открывает модальное окно для классификации"""
        dialog = tk.Toplevel(self)
        dialog.title("Интерактивная классификация")
        dialog.geometry("900x650")
        dialog.grab_set()  # Modal
        
        # Display item info
        name_label = ttk.Label(info_frame, text=item['Наименование ИВП'])
        
        # Category buttons (1-11)
        for num, name in categories:
            ttk.Button(text=f"{num}. {name}", 
                      command=lambda n=num: on_category_select(n))
        
        # Keyboard shortcuts
        dialog.bind('<Key>', on_key_press)  # 1-9, 0 for skip
    
    def show_pin_dialog(self):
        """Показывает диалог ввода PIN с shake animation"""
        dialog = tk.Toplevel(self)
        pin_entry = tk.Entry(dialog, show="●", font=("Arial", 16))
        
        def check_pin():
            if pin_var.get() == self.correct_pin:
                dialog.destroy()
                self.unlock_interface()
            else:
                error_label.config(text="❌ Неверный PIN-код!")
                # Shake animation
                for i in range(3):
                    dialog.geometry(f"+{x-10}+{y}")
                    dialog.after(50)
                    dialog.geometry(f"+{x+10}+{y}")
```

**Интерактивная классификация:**
1. Обработка файлов → обнаружение unclassified элементов
2. Автоматическое предложение классифицировать
3. Модальное окно с выбором категории (кнопки + keyboard shortcuts)
4. Сохранение правил в `rules.json`
5. Повторная обработка с новыми правилами

---

## 📋 Паттерны и Best Practices

### 1. Defensive Programming

```python
# Проверка на None/NaN
def to_text(x: Any) -> str:
    if x is None:
        return ""
    try:
        import math
        if isinstance(x, float) and math.isnan(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

# Безопасное преобразование к числу
qty_series = pd.to_numeric(tmp[qty_col], errors='coerce').fillna(1).astype(float)
```

### 2. Column Name Normalization

```python
# Гибкий поиск колонок с учетом вариаций
def find_column(possible_names: List[str], columns: List[str]) -> Optional[str]:
    # Exact match first
    for candidate in possible_names:
        if candidate in columns:
            return candidate
    
    # Partial match (starts with)
    for candidate in possible_names:
        for col in columns:
            if col.startswith(candidate):
                return col
    
    return None

# Usage:
desc_col = find_column([
    "description", "desc", "наименование", "имя", 
    "item", "part", "part name", "наим."
], df.columns)
```

### 3. Multi-format Input Handling

```python
# Автоматическое определение формата по расширению
for input_path in input_paths:
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext in [".txt"]:
        df_txt = parse_txt_like(input_path)
    elif ext in [".doc", ".docx"]:
        df_docx = parse_docx(input_path)
    elif ext in [".xlsx", ".xls"]:
        df_excel = parse_excel(input_path)
```

### 4. Regex-based Data Extraction

```python
# Извлечение ТУ кодов
TU_PATTERN = re.compile(
    r'\b([A-ZА-Я]{2,10}[\.\-]?\d{2,6}[\.\-]?\d{2,6}(?:[\.\-]?\d{2,6})?(?:[\-\s]?ТУ)?)\b',
    re.IGNORECASE
)

def extract_tu_code(text: str) -> str:
    match = TU_PATTERN.search(text)
    return match.group(1) if match else ""
```

### 5. Sorting with Custom Key

```python
def sort_by_nominal_value(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """Сортирует компоненты по номиналу (от меньшего к большему)"""
    
    def nominal_sort_key(row):
        text = str(row.get(desc_col, ""))
        nominal, unit = extract_nominal_value(text, category)
        
        # Primary: nominal value (None goes to end)
        # Secondary: alphabetical
        return (
            nominal if nominal is not None else float('inf'),
            text.lower()
        )
    
    sorted_df = df.iloc[df.apply(nominal_sort_key, axis=1).argsort()]
    return sorted_df.reset_index(drop=True)
```

### 6. Dynamic Configuration

```python
# config.json structure
{
  "app_info": {
    "version": "1.7.6",
    "release_date": "08.10.2025",
    "developer": "Куреин М.Н.",
    "description": "Категоризатор BOM файлов"
  },
  "security": {
    "pin": "5421",
    "require_pin": true
  }
}

# Usage
cfg = load_config()
ver = cfg.get("app_info", {}).get("version", "dev")
require_pin = cfg.get("security", {}).get("require_pin", False)
```

### 7. UTF-8 Encoding Everywhere

```python
# Module-level encoding declaration
# -*- coding: utf-8 -*-

# Stdout/stderr reconfiguration for Russian text
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# File I/O with explicit encoding
with open(rules_json, "w", encoding="utf-8") as f:
    json.dump(rules, f, ensure_ascii=False, indent=2)
```

---

## 🔨 Инфраструктура разработки

### Скрипты в проекте

**BAT файлы (Windows convenience):**

```batch
# start_gui.bat
@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe app.py
) else (
    python app.py
)
pause

# split_bom.bat
@echo off
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe split_bom.py %*
) else (
    python split_bom.py %*
)
```

**Автоматизация сборки (build_installer.py):**

```python
def main():
    # 1. Clean temp directory
    clean_temp_dir()
    
    # 2. Copy files
    copy_files()  # FILES_TO_COPY, DIRECTORIES_TO_COPY
    
    # 3. Copy .iss to root
    copy_iss_to_root()
    
    # 4. Run Inno Setup Compiler
    run_inno_setup()
    
    # Result: BOMCategorizerSetup.exe
```

**Post-install (post_install.ps1):**

```powershell
# Создание виртуального окружения
python -m venv .venv

# Установка зависимостей из offline_packages
.\.venv\Scripts\pip.exe install --no-index --find-links="$INSTALL_DIR\offline_packages" `
    pandas openpyxl python-docx pywin32

# Создание ярлыков на рабочем столе
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Desktop\BOM Categorizer.lnk")
$Shortcut.TargetPath = "$INSTALL_DIR\start_gui.bat"
$Shortcut.Save()
```

### Настройки среды разработки

**Виртуальное окружение:**
- Windows: `.venv\` (предпочтительно из-за стабильности)
- macOS/Linux: `venv/`

**Команды разработки:**

```bash
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run
python app.py                    # GUI
python split_bom.py --help       # CLI help

# Build installer
python build_installer.py

# Testing (manual)
python split_bom.py --inputs example/Plata_Preobrz.xlsx --xlsx output.xlsx --combine
```

### CI/CD

**Статус:** ❌ Отсутствует

**Потенциальная структура:**
```yaml
# .github/workflows/build.yml
name: Build Installer

on: [push, pull_request]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: python build_installer.py
      - uses: actions/upload-artifact@v2
        with:
          name: BOMCategorizerSetup
          path: BOMCategorizerSetup.exe
```

---

## 📊 Выводы и рекомендации

### ✨ Сильные стороны

1. **🏗️ Модульная архитектура** - четкое разделение ответственности, легко расширять
2. **📚 Excellent documentation** - подробные README, guide для каждой фичи
3. **🔒 Security** - PIN protection для GUI
4. **🎯 User-centric design** - интерактивная классификация с автосохранением правил
5. **📦 Offline-first** - полностью автономная работа с bundled dependencies
6. **🔄 Robust parsing** - поддержка TXT/DOCX/Excel, обработка edge cases
7. **🎨 Professional output** - форматированный Excel с сортировкой и стилями
8. **🛡️ Defensive coding** - обработка encoding errors, missing columns, NaN values

### 🔧 Области для улучшения

#### 1. Тестирование (Критично)

**Проблема:** Отсутствуют автоматизированные тесты

**Решение:**
```python
# Добавить pytest + fixtures
def test_classify_resistor():
    result = classify_row(
        ref="R1",
        description="Резистор 100 Ом",
        value="100",
        partname=None,
        strict=True,
        source_file=None,
        note=None
    )
    assert result == "resistors"

def test_parse_docx_with_group_headers():
    df = parse_docx("tests/fixtures/sample_with_groups.docx")
    assert "tu" in df.columns
    assert df[df["reference"] == "R1"]["tu"].iloc[0] == "ШКАБ.434110.002 ТУ"
```

#### 2. Type Hints (Средний приоритет)

**Проблема:** Частичное использование type hints

**Решение:**
```python
# Полная типизация
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd

def classify_row(
    ref: Optional[str],
    description: Optional[str],
    value: Optional[str],
    partname: Optional[str],
    strict: bool,
    source_file: Optional[str] = None,
    note: Optional[str] = None
) -> str:
    ...

# Использовать mypy для проверки
# mypy bom_categorizer/ --strict
```

#### 3. Logging (Средний приоритет)

**Проблема:** Использование `print()` вместо логгера

**Решение:**
```python
import logging

# Setup в __init__.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bom_categorizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.info(f"Обработка файла: {input_path}")
logger.warning(f"Не удалось найти колонку {desc_col}")
logger.error(f"Ошибка при парсинге: {exc}")
```

#### 4. Configuration Management (Низкий приоритет)

**Проблема:** Хардкод путей к Inno Setup, категории в коде

**Решение:**
```python
# config.yaml
inno_setup:
  path: "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"

categories:
  resistors:
    name_ru: "Резисторы"
    name_en: "Resistors"
    sort_by: "nominal"
    prefixes: ["R"]
    keywords: ["резист", "resistor"]
    
# Load with pyyaml
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)
```

#### 5. Performance Optimization

**Проблема:** Возможные медленные операции на больших файлах

**Решение:**
```python
# 1. Использовать векторизацию pandas вместо apply()
# Было:
df["cleaned"] = df["description"].apply(lambda x: clean_component_name(x))

# Стало:
df["cleaned"] = df["description"].str.replace(r'^РЕЗИСТОР\s+', '', regex=True)

# 2. Кэширование regex компиляции (уже есть)
TU_PATTERN = re.compile(r'...', re.IGNORECASE)  # ✓

# 3. Профилирование
python -m cProfile -o profile.stats split_bom.py --inputs large_file.xlsx
python -m pstats profile.stats
```

#### 6. Internationalization (Низкий приоритет)

**Проблема:** Русский язык хардкоден в коде

**Решение:**
```python
# i18n/ru.json
{
  "ui.title": "Категоризатор BOM файлов",
  "ui.add_files": "Добавить файлы",
  "categories.resistors": "Резисторы"
}

# Usage
from typing import Dict
TRANSLATIONS: Dict[str, str] = load_translations("ru")

def tr(key: str) -> str:
    return TRANSLATIONS.get(key, key)

# В коде
ttk.Label(text=tr("ui.add_files"))
```

### 🎯 Приоритетные задачи (Roadmap)

**v1.8.0 - Testing & Quality:**
1. Добавить pytest + coverage >= 80%
2. Настроить mypy для статической типизации
3. Добавить pre-commit hooks (black, flake8, mypy)
4. Настроить GitHub Actions для CI

**v1.9.0 - User Experience:**
1. Drag & drop для добавления файлов в GUI
2. Прогресс-бар для длительных операций
3. Preview окно для просмотра классификации до сохранения
4. История последних обработок

**v2.0.0 - Advanced Features:**
1. Экспорт правил классификации (import/export rules.json)
2. Batch processing mode (обработка папки файлов)
3. Плагины для кастомных категорий
4. Web-версия (Flask/FastAPI backend + React frontend)

---

## 📈 Метрики проекта

| Метрика | Значение |
|---------|----------|
| **Строк кода** | ~3,500+ (Python) |
| **Модулей** | 8 (bom_categorizer/*) |
| **Функций** | 50+ |
| **Классов** | 1 (BOMCategorizerApp) |
| **Категорий классификации** | 12 |
| **Поддерживаемых форматов** | 3 (TXT, DOCX, XLSX) |
| **Размер инсталлятора** | ~25 MB |
| **Зависимостей** | 4 прямых + 8 транзитивных |
| **Документации** | 9 MD файлов (~2000 строк) |
| **Версия** | 1.7.6 |

---

## 🎓 Уровень сложности проекта

**Оценка:** Middle-Senior friendly ⭐⭐⭐⭐

**Причины:**

**Middle-уровень требуется для:**
- ✅ Понимание pandas DataFrame API
- ✅ Работа с Tkinter GUI
- ✅ Регулярные выражения (intermediate level)
- ✅ File I/O и encoding handling
- ✅ Базовая работа с threading

**Senior-уровень полезен для:**
- 🔄 Архитектурные решения (pipeline, модульность)
- 🔄 Heuristic-based classification logic
- 🔄 Multi-format parsing с edge cases
- 🔄 Installer deployment и Windows integration
- 🔄 Performance optimization для больших файлов

**Junior-friendly аспекты:**
- 📚 Отличная документация
- 🎯 Четкая структура модулей
- 💡 Примеры использования в docs/
- 🛡️ Defensive programming patterns

---

## 🔍 Интересные решения

### 1. Dynamic Rule Learning System

Система автоматически "учится" на классификациях пользователя:

```python
# Пользователь: "Аттенюатор QFA1802" → Категория "Другие"
# Система сохраняет правило:
{
  "contains": "аттенюатор qfa",
  "category": "others",
  "comment": "Добавлено пользователем"
}

# При следующем запуске все "аттенюатор qfa*" автоматически в "Другие"
```

### 2. Group Header Context Propagation

DOCX парсер сохраняет контекст группового заголовка:

```
Таблица в DOCX:
┌─────────────────────────────────────────┐
│ Резисторы Р1-12 ШКАБ.434110.002 ТУ     │ ← Групповой заголовок (нет qty)
├─────────────────────────────────────────┤
│ R1-R4 НР1-4Р-5,1 кОм ±5%     4          │ ← Данные (наследуют ТУ)
│ R5    Р1-12-100 Ом ±5%       1          │ ← Данные (наследуют ТУ)
└─────────────────────────────────────────┘

# Парсер:
current_group_tu = "ШКАБ.434110.002 ТУ"  # из заголовка
current_group_type = "Резисторы"          # из заголовка

# Для R1-R4 и R5:
row["tu"] = current_group_tu              # применяется к данным
row["note"] = current_group_type          # применяется к данным
```

### 3. SMD Code Parsing для импортных компонентов

```python
# Импортный резистор: "0805 102"
# "0805" - размер корпуса (игнорируем)
# "102" - код номинала: 10 × 10² = 1000 Ом

def parse_smd_code(text):
    match = re.search(r'\b(\d)(\d)(\d)\b', text)
    if match:
        xy = int(match.group(1) + match.group(2))  # "10"
        z = int(match.group(3))                     # "2"
        return xy * (10 ** z)                       # 1000.0
```

### 4. Shake Animation для UI Feedback

```python
# При неверном PIN - окно "трясется"
def check_pin():
    if pin != correct_pin:
        original_x = dialog.winfo_x()
        for i in range(3):
            dialog.geometry(f"+{original_x-10}+{y}")  # Влево
            dialog.after(50)
            dialog.geometry(f"+{original_x+10}+{y}")  # Вправо
            dialog.after(50)
        dialog.geometry(f"+{original_x}+{y}")         # Центр
```

### 5. Offline-first Installer

Весь проект работает без интернета благодаря:
- Bundled Python wheels в `offline_packages/`
- PowerShell скрипт `post_install.ps1` с `--no-index --find-links`
- Inno Setup упаковывает все в один `.exe`

---

## 📝 Заключение

**BOM Categorizer** - это зрелый, хорошо структурированный desktop application для автоматизации классификации электронных компонентов. Проект демонстрирует:

✅ **Solid architecture** - модульность, separation of concerns  
✅ **User-centric design** - GUI + CLI, интерактивная классификация  
✅ **Production-ready** - оффлайн инсталлятор, error handling, документация  
✅ **Maintainable code** - понятная структура, docstrings, type hints  

⚠️ **Требует улучшений:**
- Автоматизированное тестирование (pytest)
- Полная типизация (mypy)
- Структурированное логирование
- CI/CD pipeline

**Итоговая оценка:** ⭐⭐⭐⭐ (4/5)

Отличный проект для middle-senior разработчиков, демонстрирующий best practices в организации Python desktop applications с акцентом на user experience и maintainability.

---

*Документ создан: 08.10.2025*  
*Версия проекта: 1.7.6*  
*Формат анализа адаптирован из frontend_analysis_prompt.md*
