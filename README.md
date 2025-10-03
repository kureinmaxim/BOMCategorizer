## Быстрый старт (Windows PowerShell)

```powershell
# 1) Перейти в папку проекта
cd C:\Project\ProjectSnabjenie

# 2) Создать виртуальное окружение (однажды)
python -m venv .venv

# 3) Активировать окружение (PowerShell)
.\.venv\Scripts\Activate.ps1

# 4) Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt

# 5) Запустить графический интерфейс
python app.py

# 6) (Опционально) Запуск без активации окружения
.\.venv\Scripts\python.exe app.py

# 7) Пример командной строки для разборки
.\.venv\Scripts\python.exe split_bom.py --inputs all_25.xlsx "БЗ.doc" "Докупить в 2025.txt" --sheets 3,4 --xlsx categorized.xlsx --combine --interactive --assign-json rules.json
```

## Быстрый старт (Windows CMD)

```cmd
cd /d C:\Project\ProjectSnabjenie
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Быстрый старт (macOS/Linux)

```bash
cd /path/to/ProjectSnabjenie
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 app.py
```

## Ключевые опции
- `--inputs` — список входных файлов (XLSX/DOCX/DOC/TXT).
- `--sheets` — номера/имена листов для XLSX (например `3,4`).
- `--xlsx` — путь к выходному XLSX (по умолчанию `categorized.xlsx`).
- `--txt-dir` — папка для создания TXT файлов по категориям (дополнительно к XLSX).
- `--combine` — добавить лист `SUMMARY` с суммарной комплектацией.
- `--interactive` — интерактивная разметка «Не распределено».
- `--assign-json rules.json` — JSON‑правила автоклассификации; обновляется после интерактива.

## Интерактивная классификация

**Важно:** Интерактивный режим не поддерживается в GUI. Используйте командную строку:

```bash
# Простой способ
python interactive_classify.py --input "example/Plata_Preobrz.xlsx" --output "categorized.xlsx"

# С указанием листов
python interactive_classify.py --input "example/Plata_Preobrz.xlsx" --output "categorized.xlsx" --sheets "3,4"

# Прямой вызов split_bom
python split_bom.py --inputs "example/Plata_Preobrz.xlsx" --xlsx "categorized.xlsx" --interactive --combine
```

## Список категорий
`resistors`, `capacitors`, `inductors`, `ics`, `connectors`, `dev_boards`, `optics`, `rf_modules`, `cables`, `power_modules`, `diods`, `our_developments`, `others`.

## Пример: только TXT
```powershell
.\.venv\Scripts\python.exe split_bom.py --inputs "Докупить в 2025.txt" --xlsx categorized_from_txt.xlsx --combine --loose
```

## Экспорт в TXT файлы (новое!)
Создание отдельных TXT файлов для каждой категории в удобочитаемом формате:

```powershell
# Базовое использование
.\.venv\Scripts\python.exe split_bom.py --inputs "example/БЗ.doc" --xlsx categorized.xlsx --txt-dir categorized_txt --combine

# С несколькими входными файлами
.\.venv\Scripts\python.exe split_bom.py --inputs "file1.xlsx" "file2.doc" --xlsx output.xlsx --txt-dir output_txt
```

**Что создаётся:**
- Папка с TXT файлами: `Резисторы.txt`, `Конденсаторы.txt`, `Оптические компоненты.txt`, и т.д.
- Каждый файл содержит список компонентов в удобочитаемом формате
- Подробности в файле `TXT_EXPORT_GUIDE.md`

## Проблемы активации PowerShell
Если PowerShell запрещает выполнение скриптов:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Создание инсталлятора (Inno Setup)
1) Установите Inno Setup Compiler (`innosetup.com`).
2) Откройте файл `installer.iss` и при необходимости скорректируйте `AppVersion` и `DefaultDirName`.
3) Скомпилируйте скрипт — получится `BOMCategorizerSetup.exe`.
4) Инсталлятор:
   - Скопирует файлы проекта в `Program Files`.
   - Выполнит `post_install.ps1` (создаст `.venv` и поставит зависимости).
   - Создаст ярлык «BOM Categorizer» (запускает GUI через локальный `.venv`).

Требования: установленный Python 3.10+ (или доработайте `post_install.ps1` под установку embeddable‑Python).


