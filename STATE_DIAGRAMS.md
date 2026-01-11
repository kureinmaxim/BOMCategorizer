# State-Machine Diagrams for BOMCategorizer

Диаграммы состояний для основных компонентов приложения BOMCategorizer.

---

## 1. BOM Processing Pipeline (CLI)

Основной поток обработки BOM файлов в [main.py](file:///Users/olgazaharova/Project/ProjectPython/BOMCategorizer/bom_categorizer/main.py):

```mermaid
stateDiagram-v2
    [*] --> Idle: запуск
    
    Idle --> LoadingFiles: выбор файлов
    LoadingFiles --> Parsing: файлы загружены
    LoadingFiles --> Error: ошибка чтения
    
    Parsing --> Normalizing: данные извлечены
    Parsing --> Error: ошибка парсинга
    
    Normalizing --> Classification: колонки нормализованы
    
    Classification --> Aggregation: категории назначены
    Classification --> InteractiveMode: требуется ручная классификация
    InteractiveMode --> Classification: категория выбрана
    
    Aggregation --> Writing: дубликаты объединены
    
    Writing --> ExcelOutput: запись Excel
    Writing --> PDFOutput: запись PDF
    Writing --> TXTOutput: запись TXT
    
    ExcelOutput --> Complete
    PDFOutput --> Complete
    TXTOutput --> Complete
    
    Complete --> [*]
    Error --> [*]
```

---

## 2. GUI Application States (Qt / Tkinter)

Состояния главного окна в [main_window.py](file:///Users/olgazaharova/Project/ProjectPython/BOMCategorizer/bom_categorizer/gui/main_window.py) и [gui.py](file:///Users/olgazaharova/Project/ProjectPython/BOMCategorizer/bom_categorizer/gui.py):

```mermaid
stateDiagram-v2
    [*] --> Initializing: запуск
    
    Initializing --> PINCheck: require_pin = true
    Initializing --> Ready: require_pin = false
    
    PINCheck --> SimpleMode: PIN не введен
    PINCheck --> Ready: PIN верный
    
    Ready --> FilesSelected: добавление файлов
    FilesSelected --> Ready: очистка файлов
    
    Ready --> Processing: нажатие "Обработать"
    FilesSelected --> Processing: нажатие "Обработать"
    
    Processing --> ShowingProgress: worker запущен
    ShowingProgress --> Success: обработка завершена
    ShowingProgress --> Error: ошибка
    
    Success --> Ready: закрытие диалога
    Error --> Ready: закрытие диалога
    
    Ready --> DatabaseDialog: открытие БД
    DatabaseDialog --> Ready: закрытие
    
    Ready --> SettingsDialog: открытие настроек
    SettingsDialog --> Ready: закрытие
    
    Ready --> [*]: закрытие приложения
```

---

## 3. Worker Thread States

Состояния фоновых потоков в [workers.py](file:///Users/olgazaharova/Project/ProjectPython/BOMCategorizer/bom_categorizer/gui/workers.py):

```mermaid
stateDiagram-v2
    [*] --> Idle: создание worker
    
    state ProcessingWorker {
        Idle --> Running: start()
        Running --> EmittingProgress: progress.emit()
        EmittingProgress --> Running: продолжение
        Running --> Finished: успех
        Running --> ErrorState: исключение
        Finished --> [*]: finished.emit(output, True)
        ErrorState --> [*]: finished.emit(error, False)
    }
    
    state ComparisonWorker {
        [*] --> Comparing: start()
        Comparing --> WritingDiff: файлы сравнены
        WritingDiff --> Done: diff записан
        Comparing --> CompareError: ошибка
        Done --> [*]: finished.emit(output, True)
        CompareError --> [*]: finished.emit(error, False)
    }
    
    state TruRkmWorker {
        [*] --> LoadingTru: start()
        LoadingTru --> ProcessingFile: следующий файл
        ProcessingFile --> EmitProgress: progress.emit()
        EmitProgress --> ProcessingFile: следующий файл
        ProcessingFile --> TruDone: все файлы обработаны
        TruDone --> [*]: finished.emit(results)
    }
```

---

## 4. File Parser States

Состояния парсеров в [parsers.py](file:///Users/olgazaharova/Project/ProjectPython/BOMCategorizer/bom_categorizer/parsers.py):

```mermaid
stateDiagram-v2
    [*] --> DetectFormat: открытие файла
    
    DetectFormat --> ParseTXT: .txt файл
    DetectFormat --> ParseDOCX: .docx файл
    DetectFormat --> ParseXLSX: .xlsx файл
    DetectFormat --> UnsupportedFormat: неизвестный формат
    
    state ParseDOCX {
        [*] --> LoadDocument
        LoadDocument --> FindTables: документ загружен
        FindTables --> GuessHeaders: таблицы найдены
        GuessHeaders --> ExtractRows: заголовки определены
        ExtractRows --> NormalizeCells: строки извлечены
        NormalizeCells --> [*]: DataFrame готов
    }
    
    state ParseTXT {
        [*] --> ReadLines
        ReadLines --> SplitColumns: строки прочитаны
        SplitColumns --> [*]: DataFrame готов
    }
    
    state ParseXLSX {
        [*] --> LoadWorkbook
        LoadWorkbook --> SelectSheet: книга загружена
        SelectSheet --> ReadData: лист выбран
        ReadData --> [*]: DataFrame готов
    }
    
    UnsupportedFormat --> [*]: ошибка
```

---

## 5. Classification Engine States

Состояния классификатора в [classifiers.py](file:///Users/olgazaharova/Project/ProjectPython/BOMCategorizer/bom_categorizer/classifiers.py):

```mermaid
stateDiagram-v2
    [*] --> ReceiveRow: classify_row()
    
    ReceiveRow --> CheckDatabase: проверка базы
    CheckDatabase --> ReturnCategory: найдено в БД
    CheckDatabase --> AnalyzeReference: не найдено
    
    AnalyzeReference --> CategoryFromRef: ref определяет категорию
    CategoryFromRef --> ReturnCategory
    
    AnalyzeReference --> AnalyzeDescription: ref не информативен
    AnalyzeDescription --> CategoryFromDesc: desc определяет категорию
    CategoryFromDesc --> ReturnCategory
    
    AnalyzeDescription --> AnalyzeValue: desc не информативен
    AnalyzeValue --> CategoryFromValue: value определяет категорию
    CategoryFromValue --> ReturnCategory
    
    AnalyzeValue --> Unclassified: не удалось определить
    Unclassified --> ReturnCategory: category = "unclassified"
    
    ReturnCategory --> [*]
```

---

## 6. PDF Export States

Состояния экспортера в [pdf_exporter.py](file:///Users/olgazaharova/Project/ProjectPython/BOMCategorizer/bom_categorizer/pdf_exporter.py):

```mermaid
stateDiagram-v2
    [*] --> Initialize: PDFExporter()
    
    Initialize --> RegisterFonts: инициализация
    RegisterFonts --> Ready: шрифты зарегистрированы
    RegisterFonts --> FontError: шрифты не найдены
    FontError --> Ready: fallback шрифт
    
    Ready --> LoadExcel: export_excel_to_pdf()
    LoadExcel --> ProcessSheets: Excel загружен
    
    ProcessSheets --> GetSheetData: следующий лист
    GetSheetData --> CreateTable: данные извлечены
    CreateTable --> AddToElements: таблица создана
    AddToElements --> ProcessSheets: добавлено в элементы
    
    ProcessSheets --> BuildPDF: все листы обработаны
    BuildPDF --> AddPageNumbers: документ собран
    AddPageNumbers --> SavePDF: номера добавлены
    SavePDF --> [*]: PDF сохранен
```
