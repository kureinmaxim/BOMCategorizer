# Руководство по тестированию BOM Categorizer

## Обзор

Проект включает комплексную систему тестирования:
- **Unit-тесты** - тестирование отдельных модулей
- **Интеграционные тесты** - тестирование на реальных файлах
- **Автоматизация** - BAT-файлы для быстрого запуска

## Быстрый старт

### Windows (рекомендуется)

```cmd
# Все тесты
run_tests.bat

# Только быстрые unit-тесты (2-3 секунды)
run_tests.bat quick

# Только интеграционные тесты (20-30 секунд)
run_tests.bat integration

# С покрытием кода
run_tests.bat coverage
```

### Прямой запуск через Python

```cmd
# Активировать окружение
.venv\Scripts\activate

# Все тесты
python run_tests.py -v

# Быстрые unit-тесты
python run_tests.py --quick -v

# Интеграционные тесты
python run_tests.py --integration -v

# С HTML отчетом
python run_tests.py --html -v

# С покрытием кода
python run_tests.py --coverage -v

# Конкретный тест
python run_tests.py -k test_resistor_classification -v
```

## Структура тестов

```
tests/
├── __init__.py              # Инициализация пакета тестов
├── conftest.py              # Общие фикстуры и конфигурация pytest
├── test_classifiers.py      # Тесты классификации компонентов
├── test_database.py         # Тесты базы данных компонентов
├── test_formatters.py       # Тесты форматирования и нормализации
├── test_integration.py      # Интеграционные тесты на реальных файлах
└── test_data/               # Тестовые данные (если нужны)
```

## Типы тестов

### 1. Unit-тесты классификации (`test_classifiers.py`)

Проверяют правильность классификации различных компонентов:

```python
# Примеры тестов
- test_resistor_classification     # Резисторы
- test_capacitor_classification    # Конденсаторы
- test_ic_classification          # Микросхемы
- test_semiconductor_classification # Полупроводники
- test_optical_classification     # Оптические компоненты
- test_debug_boards_classification # Отладочные платы
```

**Время выполнения:** ~1-2 секунды

### 2. Unit-тесты базы данных (`test_database.py`)

Проверяют работу с базой данных компонентов:

```python
- test_load_empty_database        # Создание начальной базы
- test_save_and_load_database    # Сохранение/загрузка
- test_add_component             # Добавление компонентов
- test_get_component_category    # Получение категории
```

**Время выполнения:** ~0.5-1 секунда

### 3. Unit-тесты форматирования (`test_formatters.py`)

Проверяют нормализацию и форматирование:

```python
- test_normalize_spaces_around_dashes  # Пробелы вокруг дефисов
- test_add_plus_minus_before_percent   # Добавление ±
- test_extract_simple_tu               # Извлечение ТУ кодов
- test_sort_resistors                  # Сортировка по номиналу
```

**Время выполнения:** ~0.5-1 секунда

### 4. Интеграционные тесты (`test_integration.py`)

Проверяют обработку реальных файлов из `example/`:

```python
- test_process_doc_file          # Обработка .doc
- test_process_xlsx_file         # Обработка .xlsx
- test_process_txt_file          # Обработка .txt
- test_plata_mkvh_doc           # Проблемный файл plata_MKVH.doc
```

**Время выполнения:** ~20-30 секунд (зависит от размера файлов)

## Установка зависимостей для тестирования

```cmd
# Активировать окружение
.venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Или установить вручную
pip install pytest pytest-html pytest-cov
```

## Запуск конкретных тестов

### По имени теста

```cmd
# Один конкретный тест
pytest tests/test_classifiers.py::TestBasicClassification::test_resistor_classification -v

# Все тесты резисторов
pytest tests/test_classifiers.py::TestBasicClassification -v

# По ключевому слову
pytest -k resistor -v
pytest -k "resistor or capacitor" -v
```

### По файлу

```cmd
# Только классификаторы
pytest tests/test_classifiers.py -v

# Только база данных
pytest tests/test_database.py -v

# Несколько файлов
pytest tests/test_classifiers.py tests/test_database.py -v
```

## Отчеты

### HTML отчет

```cmd
python run_tests.py --html -v
```

Создаст файл `test_report.html` с подробным отчетом.

### Покрытие кода

```cmd
python run_tests.py --coverage -v
```

Создаст:
- Отчет в консоли
- HTML отчет в папке `htmlcov/`

Откройте `htmlcov/index.html` в браузере для просмотра.

## Разработка тестов

### Добавление нового теста

1. Выберите подходящий файл (или создайте новый)
2. Добавьте тестовый класс или функцию:

```python
class TestNewFeature:
    """Тесты новой функции"""
    
    def test_basic_case(self):
        """Тест базового случая"""
        result = my_function("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """Тест граничного случая"""
        result = my_function("")
        assert result is None
```

3. Запустите тест:

```cmd
pytest tests/test_new.py -v
```

### Использование фикстур

Фикстуры определены в `conftest.py`:

```python
def test_with_temp_dir(temp_dir):
    """Тест с временной директорией"""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test")
    assert file_path.exists()

def test_with_example_files(example_dir):
    """Тест с файлами из example/"""
    doc_file = example_dir / "plata_MKVH.doc"
    if doc_file.exists():
        # Ваш тест
        pass
```

### Мокирование базы данных

```python
def test_with_mock_db(mock_component_database):
    """Тест с временной базой данных"""
    from bom_categorizer.component_database import add_component_to_database
    
    add_component_to_database("Test", "resistors")
    # База будет автоматически очищена после теста
```

## Интеграция с разработкой

### Before commit (перед коммитом)

```cmd
# Быстрая проверка
run_tests.bat quick
```

Если все прошло успешно - можно коммитить.

### Before merge (перед слиянием)

```cmd
# Полная проверка
run_tests.bat
```

### Before release (перед релизом)

```cmd
# Полная проверка с покрытием
run_tests.bat coverage
```

Проверьте что покрытие > 70%.

## Непрерывная интеграция (CI)

Для CI/CD систем (GitHub Actions, GitLab CI):

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py -v
```

## Troubleshooting

### Тесты не находятся

```cmd
# Убедитесь что находитесь в корне проекта
cd C:\Project\ProjectSnabjenie

# Проверьте структуру
dir tests\
```

### pytest не установлен

```cmd
pip install pytest pytest-html pytest-cov
```

### Ошибки импорта модулей

```cmd
# Убедитесь что виртуальное окружение активировано
.venv\Scripts\activate

# Переустановите зависимости
pip install -r requirements.txt
```

### Интеграционные тесты падают

Проверьте что файлы есть в `example/`:

```cmd
dir example\plata_MKVH.doc
dir example\*.xlsx
```

### База данных не очищается между тестами

Используйте фикстуру `mock_component_database` - она автоматически создает временную базу.

## Best Practices

1. **Быстрые тесты сначала** - запускайте `--quick` для быстрой проверки
2. **Изолированные тесты** - каждый тест независим
3. **Понятные имена** - `test_resistor_classification` лучше чем `test_1`
4. **Один assert = одна проверка** - по возможности
5. **Используйте фикстуры** - для повторяющейся настройки

## Полезные команды

```cmd
# Показать все доступные тесты
pytest --collect-only

# Запустить с остановкой на первой ошибке
pytest -x

# Запустить последние упавшие тесты
pytest --lf

# Показать 10 самых медленных тестов
pytest --durations=10

# Запустить в параллель (если установлен pytest-xdist)
pytest -n auto
```

## Метрики качества

### Целевые показатели

- ✅ **Покрытие кода:** > 70%
- ✅ **Успешность тестов:** 100%
- ✅ **Время unit-тестов:** < 5 секунд
- ✅ **Время интеграционных:** < 60 секунд

### Текущий статус

Запустите для проверки:

```cmd
python run_tests.py --coverage -v
```

---

**Версия:** 1.1  
**Обновлено:** 30.10.2025  
**Автор:** Куреин М.Н.
