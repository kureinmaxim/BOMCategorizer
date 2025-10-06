# 🖥️ Использование CLI (командная строка)

## ❌ Частая ошибка

**НЕ правильно:**
```bash
split_bom --inputs file.xlsx  # Ошибка: команда не найдена
```

## ✅ Правильные способы запуска

### Windows (с активированным venv):
```powershell
# 1. Активировать окружение
.\.venv\Scripts\Activate.ps1

# 2. Запустить скрипт
python split_bom.py --inputs D:/path/to/file.xlsx --xlsx output.xlsx
```

### Windows (без активации venv):
```powershell
# Прямой запуск через venv Python
.\.venv\Scripts\python.exe split_bom.py --inputs D:/path/to/file.xlsx --xlsx output.xlsx --txt-dir D:/output --combine
```

### macOS/Linux:
```bash
# С активацией
source venv/bin/activate
python3 split_bom.py --inputs file.xlsx --xlsx output.xlsx

# Без активации
venv/bin/python3 split_bom.py --inputs file.xlsx --xlsx output.xlsx
```

---

## 📋 Пример команды

### Ваш случай (исправленная команда):

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "D:/!ШСК_М/Project/Plata_Preobrz.xlsx" `
  --xlsx "D:/!ШСК_М/Project/categorized.xlsx" `
  --txt-dir "D:/!ШСК_М/Project/1_txt" `
  --combine
```

или с активированным окружением:

```powershell
# Активировать
.\.venv\Scripts\Activate.ps1

# Запустить
python split_bom.py `
  --inputs "D:/!ШСК_М/Project/Plata_Preobrz.xlsx" `
  --xlsx "D:/!ШСК_М/Project/categorized.xlsx" `
  --txt-dir "D:/!ШСК_М/Project/1_txt" `
  --combine
```

---

## 🎯 Все опции CLI

```
python split_bom.py [опции]

Обязательные:
  --inputs FILE [FILE ...]    Входные файлы (XLSX/DOCX/DOC/TXT)
  --xlsx OUTPUT.xlsx          Выходной Excel файл

Опциональные:
  --sheets N[,M,...]          Номера листов XLSX (например: 3,4)
  --txt-dir PATH              Папка для TXT файлов по категориям
  --combine                   Добавить лист SUMMARY с суммарными данными
  --merge-into SHEET          Имя листа для объединения (по умолчанию: categorized)
  --loose                     Разрешить свободный формат текста
  --assign-json rules.json    Файл с правилами автоклассификации
```

---

## 📝 Примеры использования

### 1. Простая обработка одного файла:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "example/БЗ.doc" `
  --xlsx "output.xlsx"
```

### 2. Несколько файлов с суммарными данными:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "file1.xlsx" "file2.doc" "file3.txt" `
  --xlsx "combined.xlsx" `
  --combine
```

### 3. С экспортом в TXT:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "БЗ.doc" `
  --xlsx "output.xlsx" `
  --txt-dir "output_txt" `
  --combine
```

### 4. Выбор конкретных листов из Excel:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "workbook.xlsx" `
  --sheets 3,4,5 `
  --xlsx "output.xlsx"
```

### 5. С автоклассификацией по правилам:
```powershell
.\.venv\Scripts\python.exe split_bom.py `
  --inputs "БЗ.doc" `
  --xlsx "output.xlsx" `
  --assign-json rules.json `
  --combine
```

---

## 🚫 Решение проблем

### Ошибка: "wrong # args: should be .!frame.!text insert..."
**Причина:** Запущен неправильный скрипт (возможно, app.py вместо split_bom.py)

**Решение:** Используйте полный путь:
```powershell
.\.venv\Scripts\python.exe split_bom.py --inputs file.xlsx --xlsx output.xlsx
```

### Ошибка: "python не является внутренней командой"
**Причина:** Python не в PATH или venv не активирован

**Решение:** Используйте полный путь к python.exe:
```powershell
.\.venv\Scripts\python.exe split_bom.py ...
```

### Ошибка: "ModuleNotFoundError: No module named 'pandas'"
**Причина:** Зависимости не установлены или venv не активирован

**Решение:**
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

---

## 💡 Советы

1. **Используйте обратные кавычки `` ` `` в PowerShell** для многострочных команд
2. **Заключайте пути с пробелами в кавычки**: `"D:/My Files/file.xlsx"`
3. **Проверяйте пути**: используйте `Test-Path "путь"` для проверки существования файла
4. **Относительные пути**: работают относительно текущей директории в терминале

---

*Создано: 06.10.2025*

