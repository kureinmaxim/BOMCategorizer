# Тестирование и отладка BOM Categorizer

Подробное руководство по тестированию, диагностике и отладке приложения.

---

## Содержание

1. [Быстрый старт](#-быстрый-старт)
2. [Установка зависимостей](#-установка-зависимостей)
3. [Запуск тестов](#-запуск-тестов)
4. [Структура тестов](#-структура-тестов)
5. [Описание тестовых модулей](#-описание-тестовых-модулей)
6. [Режимы тестирования](#-режимы-тестирования)
7. [Отладка алгоритма сопоставления BOM-ТРУ](#-отладка-алгоритма-сопоставления-bom-тру)
8. [Ручное тестирование GUI](#-ручное-тестирование-gui)
9. [Отчёты покрытия](#-отчёты-покрытия)
10. [Добавление новых тестов](#-добавление-новых-тестов)
11. [Устранение неполадок](#-устранение-неполадок)

---

## 1. Быстрый старт

```bash
# Установить зависимости для тестов
pip install pytest pytest-html pytest-cov

# Запустить все тесты
python run_tests.py

# Или напрямую через pytest
python -m pytest tests/ -v
```

---

## 2. Установка зависимостей

### Минимальные зависимости для тестирования

```bash
pip install pytest
```

### Полный набор (с отчётами и покрытием)

```bash
pip install pytest pytest-html pytest-cov
```

### Зависимости проекта (нужны для интеграционных тестов)

```bash
pip install -r requirements.txt
```

---

## 3. Запуск тестов

### Через `run_tests.py` (рекомендуется)

```bash
python run_tests.py                        # Все тесты
python run_tests.py --quick                # Только быстрые unit-тесты
python run_tests.py --integration          # Только интеграционные тесты
python run_tests.py -v                     # Подробный вывод
python run_tests.py -k "tru_merger"        # Фильтр по ключевому слову
python run_tests.py --coverage             # С отчётом покрытия кода
python run_tests.py --html                 # С HTML-отчётом (test_report.html)
```

### Через pytest напрямую

```bash
# Все тесты
python -m pytest tests/ -v

# Конкретный файл
python -m pytest tests/test_tru_merger.py -v

# Конкретный класс
python -m pytest tests/test_tru_merger.py::TestExtractPureCode -v

# Конкретный тест
python -m pytest tests/test_tru_merger.py::TestExtractPureCode::test_chip_inductor_prefix_removal -v

# Фильтр по ключевому слову
python -m pytest tests/ -k "erp" -v

# С покрытием кода
python -m pytest tests/ --cov=bom_categorizer --cov-report=term-missing

# Остановиться на первом падении
python -m pytest tests/ -x

# Показать print() в тестах
python -m pytest tests/ -s

# Краткий вывод ошибок
python -m pytest tests/ --tb=short
```

---

## 4. Структура тестов

```
tests/
├── conftest.py                 # Общие фикстуры (temp_dir, sample_bom_df, и т.д.)
│
├── test_classifiers.py         # Классификация компонентов (classify_row)
├── test_formatters.py          # Нормализация текста (normalize_description, sort_by_value)
├── test_database.py            # База данных компонентов (load, save, add, lookup)
│
├── test_tru_merger.py          # ТРУ-матчинг: extract_pure_code, find_matching_tru_row,
│                               #   merge_tru_into_bom, build_ostatki_and_zapas_reports
├── test_parsers.py             # Парсеры: normalize_dashes, count_from_reference, parse_txt
├── test_main_pipeline.py       # Пайплайн: multiply_quantities, aggregate_duplicate_items,
│                               #   detect_comparison_file_type, normalize_name_for_comparison
├── test_tru_rkm_processor.py   # ТРУ/РКМ файлы: detect_file_type, generate_output_filename,
│                               #   _read_tru_file
├── test_comparison.py          # Сравнение BOM: compare_processed_files, compare_flat_files
│
├── test_integration.py         # Интеграционные тесты на реальных файлах из example/
├── test_local_integration.py   # Локальные интеграционные тесты
└── test_telegram_integration.py # Тесты Telegram-интеграции
```

---

## 5. Описание тестовых модулей

### `test_tru_merger.py` — Объединение BOM + ТРУ (66 тестов)

Тестирует основной алгоритм сопоставления компонентов BOM с позициями ТРУ.

| Класс | Кол-во | Что тестирует |
|-------|--------|---------------|
| `TestNormalizeForMatching` | 7 | Нормализация строк: регистр, тире, пробелы, суффиксы, пустые значения |
| `TestNormalizeErpCode` | 9 | Нормализация ERP-кодов: None/NaN, 'Артикул', ведущие нули, десятичные, неразрывные пробелы |
| `TestExtractPureCode` | 8 | Чистый код: удаление категорий, производителей, замена кириллица→латиница |
| `TestExtractComponentCode` | 6 | Код компонента: 1564АП3У2, К10-17Б, SN74LVC8T245 |
| `TestExtractNominal` | 5 | Номинал: кОм, нФ, мкГн, пустые значения |
| `TestExtractTruNumber` | 5 | Номер ТРУ из имени файла: ТРУ.953033.7471_tpy.xlsx |
| `TestSimilarityRatio` | 3 | Схожесть строк: идентичные, разные, похожие |
| `TestParseQtyPair` | 5 | Парсинг "15 (10)": валидные, невалидные, None, NaN |
| `TestFindMatchingTruRow` | 7 | Матчинг: pure code, prefix, вилка/розетка, unknown, short code, required_code |
| `TestMergeTruIntoBom` | 5 | Полный merge: базовый, ERP-колонки, пустой ТРУ, несовпавшие, несколько ТРУ |
| `TestBuildOstatkiZapas` | 5 | Отчёты: ostatki/zapas, избыток/дефицит, пустой DF, unmatched_tru |

### `test_parsers.py` — Парсеры файлов (21 тест)

| Класс | Кол-во | Что тестирует |
|-------|--------|---------------|
| `TestNormalizeDashes` | 6 | EN/EM DASH, MINUS SIGN, HYPHEN, обычный дефис, пустые |
| `TestNormalizeCell` | 5 | Пробелы, тире, None, числа, табуляции |
| `TestCountFromReference` | 7 | R1→1, R1,R2→2, R1-R6→6, FU1-FU6→6, смешанные, пустые |
| `TestParseTxtLike` | 3 | UTF-8 файл, пустой файл, тип результата |

### `test_main_pipeline.py` — Функции пайплайна (19 тестов)

| Класс | Кол-во | Что тестирует |
|-------|--------|---------------|
| `TestMultiplyQuantities` | 5 | Множитель 1, 2, варианты колонок, отсутствие колонки, NaN |
| `TestAggregateDuplicateItems` | 5 | Дедупликация, разные элементы, файлы, combine_across_files, reference |
| `TestNormalizeNameForComparison` | 5 | Пробелы, множественные пробелы, пустые, None, NaN |
| `TestDetectComparisonFileType` | 4 | BOM (категории), flat (РКМ), один лист, несуществующий |

### `test_tru_rkm_processor.py` — Обработка ТРУ/РКМ файлов (16 тестов)

| Класс | Кол-во | Что тестирует |
|-------|--------|---------------|
| `TestDetectFileType` | 10 | tru/try/tpy/тру (латиница/кириллица/смешанное), rkm/pkm/ркм, unknown, регистр |
| `TestGenerateOutputFilename` | 3 | Суффикс _tpy/_rkm, расширение .xlsx, директория |
| `TestReadTruFile` | 3 | Реальный ТРУ файл, ожидаемые колонки, пакетное чтение (интеграционные) |

### `test_comparison.py` — Сравнение BOM файлов (7 тестов)

| Класс | Кол-во | Что тестирует |
|-------|--------|---------------|
| `TestCompareProcessedFiles` | 4 | Идентичные файлы, добавленные/удалённые компоненты, изменение количества |
| `TestCompareFlatFiles` | 3 | Общие элементы, уникальные элементы, создание выходного файла |

### `test_classifiers.py` — Классификация (22 теста)

| Класс | Кол-во | Что тестирует |
|-------|--------|---------------|
| `TestBasicClassification` | 11 | Все категории: резисторы, конденсаторы, МС, полупроводники, разъёмы, оптика, и т.д. |
| `TestAdvancedClassification` | 5 | Примечания, строгий режим, нормализация, спецсимволы, регистр |
| `TestEdgeCases` | 4 | Пустые, None, длинные строки, юникод |

### `test_database.py` — База данных компонентов (тесты CRUD и версионирования)

### `test_formatters.py` — Форматирование текста (нормализация, сортировка по номиналу)

---

## 6. Режимы тестирования

### Unit-тесты (быстрые, без файлов)

Работают на синтетических данных, не требуют реальных файлов:

```bash
python -m pytest tests/test_tru_merger.py tests/test_parsers.py tests/test_main_pipeline.py -v
```

Время выполнения: ~1 секунда.

### Интеграционные тесты (с реальными файлами)

Используют файлы из `example/`, `TRU/` и корня проекта. Автоматически пропускаются (`pytest.skip`), если файлы отсутствуют:

```bash
python -m pytest tests/test_integration.py tests/test_tru_rkm_processor.py::TestReadTruFile -v
```

### Тесты по модулю

```bash
# Классификация
python -m pytest tests/test_classifiers.py -v

# ТРУ-матчинг
python -m pytest tests/test_tru_merger.py -v

# Парсеры
python -m pytest tests/test_parsers.py -v

# Пайплайн
python -m pytest tests/test_main_pipeline.py -v

# ТРУ/РКМ обработка
python -m pytest tests/test_tru_rkm_processor.py -v

# Сравнение BOM
python -m pytest tests/test_comparison.py -v
```

### Тесты по функции

```bash
# Все тесты extract_pure_code
python -m pytest tests/test_tru_merger.py::TestExtractPureCode -v

# Все тесты матчинга
python -m pytest tests/test_tru_merger.py::TestFindMatchingTruRow -v

# Все тесты merge
python -m pytest tests/test_tru_merger.py::TestMergeTruIntoBom -v
```

---

## 7. Отладка алгоритма сопоставления BOM-ТРУ

Алгоритм сопоставления — самая сложная часть приложения. Ниже описано, как его диагностировать.

### Архитектура матчинга

```
BOM: "Чип катушки индуктивности 0603HP-47NXJ_LW"
                    │
                    ▼
         extract_pure_code()           ← Убирает категории, производителей,
                    │                     заменяет кириллицу на латиницу
                    ▼
         "0603hp-47nxj"
                    │
                    ▼
         find_matching_tru_row()       ← Стратегии матчинга (по приоритету):
            │  1. Точное совпадение pure code (score 0.99)
            │  2. Вхождение pure code (score 0.97)
            │  3. Короткий BOM код в ТРУ (score 0.95)
            │  4. Совпадение component code (score 0.92)
            │  5. Вхождение нормализованного имени (score 0.90)
            │  6. Общая similarity_ratio (порог 0.70)
            ▼
         merge_tru_into_bom()          ← Применяет найденные совпадения
```

### Диагностический скрипт

Для анализа конкретных проблем матчинга создайте скрипт:

```python
# diagnose_matching.py
import sys, os, glob
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))

from bom_categorizer.tru_merger import (
    extract_pure_code, find_matching_tru_row,
    merge_tru_into_bom, similarity_ratio, normalize_for_matching
)
from bom_categorizer.tru_rkm_processor import _read_tru_file

# 1. Загрузить BOM
BOM_PATH = "БФ+БУ_ШСК-М.xlsx"
all_sheets = pd.read_excel(BOM_PATH, sheet_name=None, engine='openpyxl')

# 2. Загрузить все ТРУ
tru_files = sorted(glob.glob("TRU/*.xlsx"))
tru_dfs = []
for tf in tru_files:
    df = _read_tru_file(tf)
    if df is not None and not df.empty:
        tru_dfs.append(df)
all_tru = pd.concat(tru_dfs, ignore_index=True)

# 3. Для каждого BOM элемента: показать best match
for sheet_name, df in all_sheets.items():
    if 'Наименование ИВП' not in df.columns:
        continue
    for _, row in df.iterrows():
        bom_name = str(row['Наименование ИВП'])
        bom_pure = extract_pure_code(bom_name)

        best = find_matching_tru_row(bom_name, "", all_tru)
        if best is None:
            tru_name = ""
            sim = 0.0
        else:
            tru_name = str(best.get('Наименование', ''))
            tru_pure = extract_pure_code(tru_name)
            sim = similarity_ratio(
                normalize_for_matching(bom_name),
                normalize_for_matching(tru_name)
            )

        status = "[OK]" if sim > 0.70 else "[? ]" if sim > 0.50 else "[!!]"
        if sim < 0.70:
            print(f"[{sheet_name}] {status} sim={sim:.2f}")
            print(f"  BOM:  '{bom_name}'")
            print(f"    pure: '{bom_pure}'")
            if tru_name:
                print(f"  ТРУ:  '{tru_name}'")
                print(f"    pure: '{extract_pure_code(tru_name)}'")
            print()
```

### Отладка конкретного элемента

```python
from bom_categorizer.tru_merger import extract_pure_code, normalize_for_matching, similarity_ratio

# Анализ кодов
bom = "50HFFA - 009 - 2/6SMA"
tru = "Аттенюатор JFW 50HFFA-009-2/6SMA"

print(f"BOM pure: '{extract_pure_code(bom)}'")
print(f"TRU pure: '{extract_pure_code(tru)}'")
print(f"BOM norm: '{normalize_for_matching(bom)}'")
print(f"TRU norm: '{normalize_for_matching(tru)}'")
print(f"Similarity: {similarity_ratio(normalize_for_matching(bom), normalize_for_matching(tru)):.3f}")
```

### Типичные причины несовпадения

| Проблема | Пример | Решение |
|----------|--------|---------|
| Производитель в одном месте, но не в другом | BOM: `50HFFA-009-2/6SMA`, ТРУ: `Аттенюатор JFW 50HFFA-009-2/6SMA` | Добавить производителя в `category_words` или `manufacturers` в `extract_pure_code()` |
| Кириллица vs Латиница | BOM: `0603НР`, ТРУ: `0603HP` | Уже решено через `confusables` map в `extract_pure_code()` |
| Разные обозначения единиц | BOM: `1.78 МОм`, ТРУ: `178 кОм` | Нормализация номиналов (пока не реализована) |
| Слово-категория не в списке | BOM: `Индуктивность X`, pure code не убирает | Добавить в `category_words` в `extract_pure_code()` |
| Спец-символы (/, «», и т.д.) | BOM: `К53-66 «Е»`, ТРУ: `К53-66-"Е"` | Нормализация кавычек в `extract_pure_code()` |

### Ключевые файлы для отладки матчинга

- `bom_categorizer/tru_merger.py` — `extract_pure_code()` (строка ~329), `find_matching_tru_row()` (строка ~419), `merge_tru_into_bom()` (строка ~636)
- `bom_categorizer/gui/main_window.py` — `start_bom_tru_merge()` (строка ~1247), `_apply_category_prefix()` (строка ~1407)

---

## 8. Ручное тестирование GUI

### Режим 1: Категоризация BOM

1. Запустить `python app_qt.py`
2. Нажать "Открыть файл" → выбрать `.xlsx`/`.docx`/`.txt`
3. Нажать "Обработать"
4. Проверить:
   - Все категории заполнены (Резисторы, Конденсаторы, МС, и т.д.)
   - "Не распределено" минимально (< 5% позиций)
   - SUMMARY лист содержит сводку

### Режим 2: BOM + ТРУ (объединение)

1. Открыть обработанный BOM файл (`.xlsx` с категориями)
2. Добавить ТРУ файлы (кнопка "ТРУ/РКМ файлы")
3. Нажать "Обработать"
4. Проверить выходные файлы:
   - `*_тру.xlsx` — BOM с данными из ТРУ (КОД ERP, стоимость, № ТРУ)
   - `*_ostatki.xlsx` — позиции без ТРУ + остатки
   - `*_zapas.xlsx` — избыточные ТРУ позиции + запасы
5. Проверить:
   - Совпавшие строки подсвечены голубым
   - Количество в формате "TRU (BOM)" при различии
   - Категорийные префиксы добавлены к именам

### Режим 3: Сравнение BOM

1. Выбрать два BOM файла для сравнения
2. Нажать "Сравнить"
3. Проверить:
   - Добавленные/удалённые позиции
   - Изменения количества
   - Общие позиции

### Режим 4: Обработка ТРУ/РКМ файлов

1. Выбрать `.xls` файлы ТРУ или РКМ
2. Нажать "Обработать ТРУ/РКМ"
3. Проверить:
   - Выходной файл `*_tpy.xlsx` или `*_rkm.xlsx` создан
   - Колонки: Наименование, Количество, Цена, Стоимость, Артикул

---

## 9. Отчёты покрытия

### Генерация отчёта покрытия

```bash
# Терминальный отчёт
python -m pytest tests/ --cov=bom_categorizer --cov-report=term-missing

# HTML-отчёт (откроется в браузере)
python -m pytest tests/ --cov=bom_categorizer --cov-report=html
# Открыть: htmlcov/index.html

# HTML-отчёт тестов
python run_tests.py --html
# Открыть: test_report.html
```

### Текущее покрытие по модулям

| Модуль | Покрытие | Примечание |
|--------|----------|------------|
| `classifiers.py` | Хорошее | 22 теста на все категории |
| `tru_merger.py` | Хорошее | 66 тестов на нормализацию, матчинг, merge, отчёты |
| `parsers.py` | Среднее | 21 тест (парсинг docx — только через интеграционные) |
| `main.py` | Среднее | 19 тестов на пайплайн и сравнение |
| `tru_rkm_processor.py` | Среднее | 16 тестов (detect + read) |
| `component_database.py` | Хорошее | Тесты CRUD |
| `formatters.py` | Хорошее | Нормализация + сортировка |
| `excel_writer.py` | Низкое | Тестируется через интеграционные |
| `gui/main_window.py` | Низкое | GUI — только ручное тестирование |

---

## 10. Добавление новых тестов

### Конвенции

- Файлы: `tests/test_<модуль>.py`
- Классы: `TestXxxYyy` (английские имена)
- Методы: `test_<описание>` (английские имена)
- Docstrings: на русском языке
- Фреймворк: `pytest` (не `unittest`)
- Фикстуры: общие — в `conftest.py`, локальные — в тестовом файле

### Пример unit-теста

```python
class TestMyFunction:
    """Тесты для my_function"""

    def test_basic_case(self):
        """Базовый случай"""
        result = my_function("input")
        assert result == "expected"

    def test_empty_input(self):
        """Пустой ввод"""
        assert my_function("") == ""

    def test_none_input(self):
        """None ввод"""
        assert my_function(None) == ""
```

### Пример интеграционного теста

```python
class TestIntegration:
    """Интеграционные тесты"""

    def test_with_real_file(self, temp_dir):
        """Тест с реальным файлом"""
        input_file = Path("example/test.xlsx")
        if not input_file.exists():
            pytest.skip("Файл не найден")

        output_file = temp_dir / "output.xlsx"
        result = process_file(str(input_file), str(output_file))
        assert result is not None
        assert output_file.exists()
```

### Доступные фикстуры (conftest.py)

| Фикстура | Описание |
|----------|----------|
| `temp_dir` | Временная директория (автоочистка после теста) |
| `example_dir` | Путь к `example/` |
| `tru_dir` | Путь к `TRU/` |
| `real_bom_file` | Путь к `БФ+БУ_ШСК-М.xlsx` (skip если нет) |
| `sample_bom_df` | Синтетический BOM DataFrame (5 строк) |
| `sample_tru_df` | Синтетический ТРУ DataFrame (5 строк) |
| `sample_component_data` | Пример данных компонента (dict) |
| `mock_component_database` | Мокированная БД компонентов |
| `make_temp_excel` | Фабрика для создания временных Excel файлов |

---

## 11. Устранение неполадок

### pytest не установлен

```bash
pip install pytest
# или
python -m pip install pytest
```

### Ошибка импорта модулей

Убедитесь, что запускаете тесты из корня проекта:

```bash
cd c:\Project\BOMCategorizer
python -m pytest tests/ -v
```

### Кодировка (UnicodeEncodeError на Windows)

Используйте UTF-8 режим:

```bash
python -X utf8 -m pytest tests/ -v
```

Или установите переменную окружения:

```powershell
$env:PYTHONUTF8 = "1"
python -m pytest tests/ -v
```

### Тесты пропускаются (SKIPPED)

Интеграционные тесты пропускаются если:
- Нет папки `example/` с тестовыми файлами
- Нет папки `TRU/` с файлами ТРУ
- Нет файла `БФ+БУ_ШСК-М.xlsx` в корне проекта

Это нормальное поведение — unit-тесты работают без реальных файлов.

### Тесты зависают

Если тесты зависают на интеграционных, можно запустить только unit-тесты:

```bash
python run_tests.py --quick
```

### Конфликт версий зависимостей

```bash
pip install --upgrade pytest pandas openpyxl
```
