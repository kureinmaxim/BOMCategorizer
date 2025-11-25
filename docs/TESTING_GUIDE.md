# 🧪 Руководство по тестированию BOM Categorizer

> **Версия:** 2.1  
> **Дата:** 25.11.2025  
> **Автор:** Куреин М.Н.

---

## 📋 Содержание

1. [Быстрый старт](#-быстрый-старт)
2. [Структура тестов](#-структура-тестов)
3. [Типы тестов](#-типы-тестов)
4. [Как создавать тесты](#-как-создавать-тесты)
5. [Запуск тестов](#-запуск-тестов)
6. [Тестирование на реальных файлах](#-тестирование-на-реальных-файлах)
7. [Отчёты и метрики](#-отчёты-и-метрики)
8. [База данных компонентов](#-база-данных-компонентов)
9. [Рабочий процесс](#-рабочий-процесс)
10. [CI/CD интеграция](#-cicd-интеграция)
11. [Устранение проблем](#-устранение-проблем)

---

## ⚡ Быстрый старт

### Windows

```cmd
# Быстрые unit-тесты (2-3 секунды)
scripts\run_tests.bat quick

# Полный прогон всех тестов
scripts\run_tests.bat

# Интеграционные тесты
scripts\run_tests.bat integration

# С покрытием кода
scripts\run_tests.bat coverage
```

### macOS / Linux

```bash
# Активация окружения
source venv/bin/activate

# Запуск всех тестов
pytest

# Быстрые тесты
pytest tests/test_classifiers.py tests/test_formatters.py tests/test_database.py -v

# Конкретный тест
pytest tests/test_classifiers.py -v
```

### Через Python (универсально)

```bash
# Все тесты
python run_tests.py -v

# Быстрые unit-тесты
python run_tests.py --quick -v

# С HTML отчётом
python run_tests.py --html -v

# С покрытием
python run_tests.py --coverage -v
```

---

## 🏗 Структура тестов

```
BOMCategorizer/
├── tests/                      # Unit и интеграционные тесты
│   ├── __init__.py            # Инициализация пакета
│   ├── conftest.py            # Общие фикстуры pytest
│   ├── test_classifiers.py    # Тесты классификации
│   ├── test_database.py       # Тесты базы данных
│   ├── test_formatters.py     # Тесты форматирования
│   └── test_integration.py    # Интеграционные тесты
│
├── run_tests.py               # Скрипт запуска pytest
├── scripts/run_tests.bat      # BAT файл для Windows
└── test_output/               # Результаты (создаётся автоматически)
```

| Файл | Назначение | Время |
|------|------------|-------|
| `test_classifiers.py` | Классификация компонентов | ~1-2 сек |
| `test_formatters.py` | Форматирование и нормализация | ~0.5-1 сек |
| `test_database.py` | Работа с базой данных | ~0.5-1 сек |
| `test_integration.py` | Обработка реальных файлов | ~20-30 сек |

---

## 🧩 Типы тестов

### 1. Unit-тесты классификации

Проверяют правильность определения категорий:

```python
# Примеры тестов
- test_resistor_classification     # Резисторы
- test_capacitor_classification    # Конденсаторы
- test_ic_classification          # Микросхемы
- test_semiconductor_classification # Полупроводники
- test_optical_classification     # Оптические компоненты
```

**Что тестируется:**
- ✅ Классификация по категориям
- ✅ Работа с базой данных компонентов
- ✅ Нормализация описаний
- ✅ Извлечение ТУ кодов
- ✅ Сортировка по номиналу

### 2. Unit-тесты форматирования

```python
- test_normalize_spaces_around_dashes  # Пробелы вокруг дефисов
- test_add_plus_minus_before_percent   # Добавление ±
- test_extract_simple_tu               # Извлечение ТУ кодов
- test_sort_resistors                  # Сортировка по номиналу
```

### 3. Unit-тесты базы данных

```python
- test_load_empty_database        # Создание начальной базы
- test_save_and_load_database    # Сохранение/загрузка
- test_add_component             # Добавление компонентов
- test_get_component_category    # Получение категории
```

### 4. Интеграционные тесты

Проверяют обработку реальных файлов из `example/`:

```python
- test_process_doc_file          # Обработка .doc
- test_process_xlsx_file         # Обработка .xlsx
- test_process_txt_file          # Обработка .txt
```

**Что тестируется:**
- ✅ Обработка .doc, .docx, .xlsx, .txt файлов
- ✅ Обработка нескольких файлов одновременно
- ✅ Валидация выходных данных

---

## 📝 Как создавать тесты

### Простой тест

```python
from bom_categorizer.classifiers import classify_component

def test_resistor_classification():
    # 1. Подготовка (Arrange)
    description = "RES 10k 1% 0603"
    
    # 2. Действие (Act)
    category = classify_component(description)
    
    # 3. Проверка (Assert)
    assert category == "resistors"

def test_unknown_component():
    description = "Strange Device 3000"
    category = classify_component(description)
    assert category == "unclassified"
```

### Использование фикстур

```python
def test_database_add(mock_database):
    # mock_database - временная копия БД, удалится после теста
    mock_database.add("New Part", "chips")
    assert mock_database.get("New Part") == "chips"
```

### Параметризация (много тестов в одном)

```python
import pytest
from bom_categorizer.formatters import normalize_value

@pytest.mark.parametrize("input_val, expected", [
    ("10k", "10 kOhm"),
    ("4k7", "4.7 kOhm"),
    ("100R", "100 Ohm"),
    ("0.1uF", "100 nF"),
])
def test_normalization(input_val, expected):
    assert normalize_value(input_val) == expected
```

### Тестовый класс

```python
class TestNewFeature:
    """Тесты новой функции"""
    
    def test_basic_case(self):
        """Базовый случай"""
        result = my_function("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """Граничный случай"""
        result = my_function("")
        assert result is None
```

---

## 🏃 Запуск тестов

### По режиму

```bash
# Быстрые unit-тесты
scripts\run_tests.bat quick

# Интеграционные
scripts\run_tests.bat integration

# С покрытием
scripts\run_tests.bat coverage
```

### По файлу

```bash
pytest tests/test_classifiers.py -v
pytest tests/test_database.py -v
pytest tests/test_classifiers.py tests/test_database.py -v
```

### По имени теста

```bash
# Один конкретный тест
pytest tests/test_classifiers.py::TestBasicClassification::test_resistor_classification -v

# По ключевому слову
pytest -k resistor -v
pytest -k "resistor or capacitor" -v
```

### Полезные флаги pytest

```bash
pytest -v                  # Подробный вывод
pytest -x                  # Остановка на первой ошибке
pytest --lf                # Только упавшие в прошлый раз
pytest --durations=10      # Показать 10 самых медленных
pytest --collect-only      # Показать все тесты без запуска
```

---

## 📂 Тестирование на реальных файлах

> ⚠️ **Важно:** Папка `example/` исключена из Git для защиты конфиденциальных данных.

### Настройка

1. Создайте папку `example/` в корне проекта:
   ```bash
   mkdir example
   ```

2. Добавьте свои BOM файлы:
   ```
   example/
     ├── plata1.doc
     ├── plata2.docx
     ├── spisok.xlsx
     └── zakupka.txt
   ```

### Запуск

```bash
# Windows
test_examples.bat                    # Все файлы
test_examples.bat plata.doc          # Конкретный файл
test_examples.bat plata.doc Plata.xlsx  # Несколько файлов

# macOS/Linux
pytest tests/test_integration.py -v
```

### Результаты

Выходные файлы создаются в `test_output/`.

---

## 📊 Отчёты и метрики

### HTML отчёт по тестам

```bash
python run_tests.py --html -v
# Создаёт test_report.html
```

### Отчёт покрытия кода

```bash
python run_tests.py --coverage -v
# Создаёт htmlcov/index.html
```

Откройте в браузере для просмотра.

### Целевые показатели

| Метрика | Цель |
|---------|------|
| Покрытие кода | > 70% |
| Успешность тестов | 100% |
| Время unit-тестов | < 5 сек |
| Время интеграционных | < 60 сек |

---

## 🗄 База данных компонентов

### Расположение

- **Разработка:** `component_database.json` в корне проекта
- **Установка:** `%APPDATA%\BOMCategorizer\Data\` (Windows) или `~/Library/Application Support/BOMCategorizer/` (macOS)

### Мокирование в тестах

```python
def test_with_mock_db(mock_component_database):
    """Тест с временной базой данных"""
    from bom_categorizer.component_database import add_component_to_database
    
    add_component_to_database("Test", "resistors")
    # База автоматически очистится после теста
```

### Просмотр статистики

```python
from bom_categorizer.component_database import get_database_stats

stats = get_database_stats()
print(f"Всего компонентов: {stats['total']}")
print(f"По категориям: {stats['by_category']}")
```

---

## 🔄 Рабочий процесс

### Во время разработки

```bash
# После каждого изменения - быстрые тесты
scripts\run_tests.bat quick
```

### Перед коммитом

```bash
# Полный прогон
scripts\run_tests.bat
```

### Перед релизом

```bash
# Полная проверка с покрытием
scripts\run_tests.bat coverage
```

Проверьте:
- ✅ Все тесты проходят (100%)
- ✅ Покрытие кода > 70%
- ✅ Реальные файлы обрабатываются корректно

---

## 🚀 CI/CD интеграция

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: python -m pip install -r requirements.txt
      - name: Run unit tests
        run: python run_tests.py --quick -v
      - name: Run integration tests
        run: python run_tests.py --integration -v
      - name: Generate coverage
        run: python run_tests.py --coverage -v
```

---

## 🚫 Устранение проблем

| Проблема | Решение |
|----------|---------|
| **pytest не найден** | `pip install -r requirements.txt` |
| **ModuleNotFoundError** | Активируйте venv: `.venv\Scripts\activate` (Win) или `source venv/bin/activate` (macOS) |
| **Тесты падают на файлах** | Создайте папку `example/` и добавьте туда BOM файлы |
| **Ошибка кодировки (Windows)** | Выполните `chcp 65001` перед запуском |
| **Database locked** | Используйте фикстуру `mock_component_database` |

### Подробная диагностика

```bash
# Проверить структуру тестов
pytest --collect-only

# Проверить что pytest видит тесты
pytest tests/ --collect-only

# Запустить с максимальной детализацией
pytest -vvv --tb=long
```

---

## 📚 Дополнительно

- [CLI_USAGE.md](CLI_USAGE.md) — Использование командной строки
- [INTERACTIVE_MODE_GUIDE.md](INTERACTIVE_MODE_GUIDE.md) — Интерактивная классификация
- [AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md) — AI интеграция
- [DATABASE_MANAGEMENT_GUIDE.md](DATABASE_MANAGEMENT_GUIDE.md) — Управление базой данных

---

*Для версии: BOM Categorizer Standard 3.3.0+ / Modern Edition 4.4.9+*
