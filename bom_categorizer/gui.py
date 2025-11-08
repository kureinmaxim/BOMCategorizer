# -*- coding: utf-8 -*-
"""
GUI для BOM Categorizer

Tkinter-интерфейс с поддержкой:
- Выбора входных файлов (XLSX, DOCX, TXT)
- Настройки параметров обработки
- Интерактивной классификации нераспределенных элементов
- PIN-защиты интерфейса
"""

import os
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
import platform

from .component_database import (
    add_component_to_database, 
    get_database_path, 
    get_database_stats,
    export_database_to_excel,
    import_database_from_excel,
    backup_database,
    is_first_run,
    initialize_database_from_template,
    format_history_tooltip
)

# Исправление кодировки для корректного вывода русских символов
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from .main import main as cli_main


class ToolTip:
    """
    Класс для создания всплывающих подсказок (tooltip)
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Показывает tooltip"""
        if self.tooltip:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, 
                        justify=tk.LEFT,
                        background="#FFFFDD", 
                        foreground="black",
                        relief=tk.SOLID, 
                        borderwidth=1,
                        font=("Courier", 10),
                        padx=10, 
                        pady=8)
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Скрывает tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def get_system_fonts():
    """
    Возвращает подходящие шрифты для текущей ОС

    Returns:
        dict: Словарь с типами шрифтов (default, monospace)
    """
    system = platform.system()

    if system == 'Darwin':  # macOS
        return {
            'default': 'SF Pro Text',  # Системный шрифт macOS
            'default_fallback': 'Helvetica Neue',
            'monospace': 'Menlo',
            'monospace_fallback': 'Monaco'
        }
    elif system == 'Windows':
        return {
            'default': 'Segoe UI',
            'default_fallback': 'Arial',
            'monospace': 'Consolas',
            'monospace_fallback': 'Courier New'
        }
    else:  # Linux и другие
        return {
            'default': 'DejaVu Sans',
            'default_fallback': 'Sans',
            'monospace': 'DejaVu Sans Mono',
            'monospace_fallback': 'Monospace'
        }


def run_cli_async(args_list, on_finish):
    """
    Запускает CLI асинхронно в отдельном потоке
    
    Args:
        args_list: Список аргументов для CLI
        on_finish: Callback-функция, вызываемая после завершения с выводом
    """
    def worker():
        import sys
        from io import StringIO
        old_out, old_err = sys.stdout, sys.stderr
        buf = StringIO()
        try:
            sys.stdout = buf
            sys.stderr = buf
            # emulate CLI call
            import argparse
            import sys as _sys
            _old_argv = _sys.argv
            try:
                _sys.argv = ["split_bom.py"] + args_list
                cli_main()
            finally:
                _sys.argv = _old_argv
        except SystemExit as e:
            pass
        except Exception as e:
            print(f"Error: {e}")
        finally:
            output = buf.getvalue()
            sys.stdout = old_out
            sys.stderr = old_err
            on_finish(output)
    threading.Thread(target=worker, daemon=True).start()


def load_config() -> dict:
    """Загружает конфигурацию из config.json"""
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"app_info": {"version": "dev", "description": "BOM Categorizer"}}


class BOMCategorizerApp(tk.Tk):
    """Главное окно приложения BOM Categorizer"""
    
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        ver = self.cfg.get("app_info", {}).get("version", "dev")
        name = self.cfg.get("app_info", {}).get("description", "BOM Categorizer")
        self.title(f"{name} v{ver}")
        self.geometry("800x750")  # Компактное окно

        # Применяем современную цветовую схему
        self._setup_modern_styles()

        self.input_files: dict[str, int] = {}  # {путь_к_файлу: количество}
        self.sheet_spec = tk.StringVar()
        self.output_xlsx = tk.StringVar(value="categorized.xlsx")
        self.merge_into = tk.StringVar()
        self.combine = tk.BooleanVar(value=True)
        self.interactive = tk.BooleanVar(value=False)
        self.assign_json = tk.StringVar()
        self.txt_dir = tk.StringVar()
        self.create_txt = tk.BooleanVar(value=False)
        self.current_file_multiplier = tk.IntVar(value=1)  # Количество для выбранного файла
        self.selected_file_index = None  # Индекс последнего выбранного файла

        # Сравнение файлов
        self.compare_file1 = tk.StringVar()
        self.compare_file2 = tk.StringVar()
        self.compare_output = tk.StringVar(value="comparison.xlsx")
        
        # PIN protection
        self.unlocked = False
        self.require_pin = self.cfg.get("security", {}).get("require_pin", False)
        self.correct_pin = self.cfg.get("security", {}).get("pin", "1234")
        
        # Список виджетов для блокировки/разблокировки
        self.lockable_widgets = []

        self.create_widgets()
        
        # Блокируем интерфейс если требуется PIN
        if self.require_pin:
            self.lock_interface()
        
        # Проверяем первый запуск и предлагаем импорт БД
        self.after(500, self.check_first_run_and_offer_import)

    def _setup_modern_styles(self):
        """Настраивает современные стили для ttk виджетов"""
        style = ttk.Style()

        # Получаем подходящие шрифты для текущей ОС
        fonts = get_system_fonts()
        default_font = fonts['default']
        mono_font = fonts['monospace']

        # Сохраняем шрифты для использования в других методах
        self.default_font = default_font
        self.monospace_font = mono_font

        # Современная цветовая палитра
        colors = {
            'primary': '#2196F3',      # Синий
            'primary_dark': '#1976D2',  # Темно-синий
            'success': '#4CAF50',       # Зеленый
            'danger': '#F44336',        # Красный
            'warning': '#FF9800',       # Оранжевый
            'bg': '#F5F5F5',            # Светло-серый фон
            'surface': '#FFFFFF',       # Белый
            'text': '#212121',          # Темно-серый текст
            'text_secondary': '#757575' # Серый текст
        }

        # Настройка цвета фона окна
        self.configure(bg=colors['bg'])

        # Стиль для основных кнопок
        style.configure('Primary.TButton',
                       font=(default_font, 13),
                       padding=(10, 4),
                       borderwidth=0)

        # Стиль для акцентных кнопок
        style.configure('Accent.TButton',
                       font=(default_font, 13, 'bold'),
                       padding=(10, 4),
                       borderwidth=0)

        # Стиль для меток с жирным шрифтом
        style.configure('Bold.TLabel',
                       font=(default_font, 13, 'bold'),
                       foreground=colors['text'])

        # Стиль для секций
        style.configure('Section.TLabelframe.Label',
                       font=(default_font, 14, 'bold'),
                       foreground=colors['primary'])

        style.configure('Section.TLabelframe',
                       borderwidth=2,
                       relief='solid')

        # Стиль для обычных меток
        style.configure('TLabel',
                       font=(default_font, 12),
                       foreground=colors['text'])

        # Стиль для кнопок
        style.configure('TButton',
                       font=(default_font, 12),
                       padding=(8, 4))

    def create_widgets(self):
        """Создает все виджеты интерфейса"""
        pad = {"padx": 3, "pady": 2}  # Очень компактные отступы

        # Создать Canvas с вертикальной прокруткой
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        canvas = tk.Canvas(main_container, bg='#F5F5F5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)

        # Создать фрейм внутри canvas для содержимого
        frm = ttk.Frame(canvas)

        # Привязать фрейм к canvas
        frm.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frm, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Разместить canvas и scrollbar
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязать прокрутку колесом мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        row = 0

        # Главная рабочая зона (в рамке)
        main_work_frame = ttk.LabelFrame(frm, text=" 📁 Основные настройки ", padding=6, style='Section.TLabelframe')
        main_work_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        
        # Сбросить счетчик строк для рамки
        work_row = 0
        ttk.Label(main_work_frame, text="Входные файлы (XLSX/DOCX/DOC/TXT):", style='Bold.TLabel').grid(row=work_row, column=0, sticky="w", **pad)
        btn1 = ttk.Button(main_work_frame, text="➕ Добавить файлы", command=self.on_add_files)
        btn1.grid(row=work_row, column=1, sticky="w", **pad)
        self.lockable_widgets.append(btn1)

        btn2 = ttk.Button(main_work_frame, text="🗑️ Очистить", command=self.on_clear_files)
        btn2.grid(row=work_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn2)
        
        self.listbox = tk.Listbox(main_work_frame, height=4, font=(self.default_font, 12),
                                 relief=tk.FLAT, bg='#FFFFFF', fg='#212121',
                                 selectbackground='#2196F3', selectforeground='#FFFFFF')
        self.listbox.grid(row=work_row+1, column=0, columnspan=3, sticky="nsew", **pad)
        self.listbox.bind('<<ListboxSelect>>', self.on_file_selected)
        self.lockable_widgets.append(self.listbox)
        main_work_frame.grid_rowconfigure(work_row+1, weight=1)
        main_work_frame.grid_columnconfigure(2, weight=1)

        work_row += 2
        # Поле для указания количества для выбранного файла
        multiplier_frame = ttk.Frame(main_work_frame)
        multiplier_frame.grid(row=work_row, column=0, columnspan=3, sticky="w", **pad)
        
        ttk.Label(multiplier_frame, text="Количество экземпляров для выбранного файла:").pack(side="left")
        self.file_multiplier_spinbox = ttk.Spinbox(multiplier_frame, from_=1, to=1000, 
                                                     textvariable=self.current_file_multiplier, 
                                                     width=10)
        self.file_multiplier_spinbox.pack(side="left", padx=(10, 0))
        self.lockable_widgets.append(self.file_multiplier_spinbox)
        
        # Добавляем кнопку "Применить" для явного обновления
        apply_btn = ttk.Button(multiplier_frame, text="Применить", command=self.on_multiplier_changed)
        apply_btn.pack(side="left", padx=(5, 0))
        self.lockable_widgets.append(apply_btn)
        
        ttk.Label(multiplier_frame, text="(выберите файл и измените количество)", 
                  font=('TkDefaultFont', 11), foreground='gray').pack(side="left", padx=(10, 0))

        work_row += 1
        ttk.Label(main_work_frame, text="Листы (например: Лист1,Лист2 или оставьте пустым для всех):").grid(row=work_row, column=0, columnspan=3, sticky="w", **pad)
        
        work_row += 1
        self.sheet_entry = ttk.Entry(main_work_frame, textvariable=self.sheet_spec, state='normal')
        self.sheet_entry.grid(row=work_row, column=0, columnspan=3, sticky="ew", **pad)
        self.lockable_widgets.append(self.sheet_entry)
        
        # Устанавливаем placeholder для ясности
        if not self.sheet_spec.get():
            self.sheet_spec.set("")
        
        # Подсказка о работе параметра "Листы"
        work_row += 1
        sheets_hint = ttk.Label(main_work_frame, 
                               text="💡 Если поле ПУСТОЕ - обрабатываются ВСЕ листы из каждого .xlsx файла. Если ЗАПОЛНЕНО - только указанные листы из КАЖДОГО .xlsx файла.",
                               font=('TkDefaultFont', 11), 
                               foreground='gray',
                               wraplength=600)
        sheets_hint.grid(row=work_row, column=0, columnspan=3, sticky="w", **pad)
        self.sheets_warning_label = sheets_hint

        work_row += 1
        ttk.Label(main_work_frame, text="Выходной XLSX:").grid(row=work_row, column=0, sticky="w", **pad)
        entry2 = ttk.Entry(main_work_frame, textvariable=self.output_xlsx, font=(self.default_font, 12))
        entry2.grid(row=work_row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry2)

        btn3 = ttk.Button(main_work_frame, text="💾 Сохранить как...", command=self.on_pick_output)
        btn3.grid(row=work_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn3)

        work_row += 1
        ttk.Label(main_work_frame, text="Папка для TXT файлов (опционально):").grid(row=work_row, column=0, sticky="w", **pad)
        entry3 = ttk.Entry(main_work_frame, textvariable=self.txt_dir, font=(self.default_font, 12))
        entry3.grid(row=work_row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry3)

        btn4 = ttk.Button(main_work_frame, text="📂 Выбрать...", command=self.on_pick_txt_dir)
        btn4.grid(row=work_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn4)

        work_row += 1
        chk1 = ttk.Checkbutton(main_work_frame, text="Суммарная комплектация (SUMMARY)", variable=self.combine)
        chk1.grid(row=work_row, column=0, columnspan=2, sticky="w", **pad)
        self.lockable_widgets.append(chk1)

        work_row += 1
        # Кнопки запуска - выделяем цветом и крупнее
        btn5 = ttk.Button(main_work_frame, text="▶ Запустить обработку", command=self.on_run, style='Primary.TButton')
        btn5.grid(row=work_row, column=0, columnspan=2, sticky="ew", **pad)
        self.lockable_widgets.append(btn5)

        btn6 = ttk.Button(main_work_frame, text="🔄 Интерактивная классификация", command=self.on_interactive_classify, style='Accent.TButton')
        btn6.grid(row=work_row, column=2, sticky="ew", **pad)
        self.lockable_widgets.append(btn6)

        # Продолжаем с основным фреймом
        # Секция для сравнения двух BOM файлов
        row += 1
        ttk.Separator(frm, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=3)

        row += 1
        compare_frame = ttk.LabelFrame(frm, text=" 🔍 Сравнение двух BOM файлов ", padding=6, style='Section.TLabelframe')
        compare_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)

        compare_row = 0
        ttk.Label(compare_frame, text="Первый файл (базовый):").grid(row=compare_row, column=0, sticky="w", **pad)
        entry_cmp1 = ttk.Entry(compare_frame, textvariable=self.compare_file1)
        entry_cmp1.grid(row=compare_row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry_cmp1)
        btn_cmp1 = ttk.Button(compare_frame, text="📂 Выбрать...", command=self.on_select_compare_file1)
        btn_cmp1.grid(row=compare_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn_cmp1)
        compare_frame.grid_columnconfigure(1, weight=1)

        compare_row += 1
        ttk.Label(compare_frame, text="Второй файл (новый):").grid(row=compare_row, column=0, sticky="w", **pad)
        entry_cmp2 = ttk.Entry(compare_frame, textvariable=self.compare_file2)
        entry_cmp2.grid(row=compare_row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry_cmp2)
        btn_cmp2 = ttk.Button(compare_frame, text="📂 Выбрать...", command=self.on_select_compare_file2)
        btn_cmp2.grid(row=compare_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn_cmp2)

        compare_row += 1
        ttk.Label(compare_frame, text="Файл результата:").grid(row=compare_row, column=0, sticky="w", **pad)
        entry_cmp_out = ttk.Entry(compare_frame, textvariable=self.compare_output)
        entry_cmp_out.grid(row=compare_row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry_cmp_out)
        btn_cmp_out = ttk.Button(compare_frame, text="💾 Сохранить как...", command=self.on_select_compare_output)
        btn_cmp_out.grid(row=compare_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn_cmp_out)

        compare_row += 1
        btn_compare = ttk.Button(compare_frame, text="⚡ Сравнить файлы", command=self.on_compare_files, style='Primary.TButton')
        btn_compare.grid(row=compare_row, column=0, columnspan=3, sticky="ew", **pad)
        self.lockable_widgets.append(btn_compare)

        # Секция Лог
        row += 1
        ttk.Separator(frm, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=3)

        row += 1
        log_frame = ttk.LabelFrame(frm, text=" 📋 Лог выполнения ", padding=6, style='Section.TLabelframe')
        log_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)

        self.txt = tk.Text(log_frame, height=8, wrap=tk.WORD, font=(self.monospace_font, 12),
                          relief=tk.FLAT, bg='#FFFFFF', fg='#212121')
        self.txt.pack(fill=tk.BOTH, expand=True)
        self.lockable_widgets.append(self.txt)
        frm.grid_rowconfigure(row, weight=2)

        row += 1
        ttk.Separator(frm, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=3)

        row += 1
        # Секция управления базой данных
        db_frame = ttk.LabelFrame(frm, text=" 🗄️ Управление базой данных ", padding=6, style='Section.TLabelframe')
        db_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        
        # Описание секции
        db_info_text = ("Управляйте базой данных компонентов: просматривайте статистику, создавайте резервные "
                      "копии, экспортируйте для переноса на другой ПК.")
        ttk.Label(db_frame, text=db_info_text, wraplength=600, justify='left', font=(self.default_font, 11)).pack(fill=tk.X, pady=(0, 3))
        
        # Фрейм для кнопок в 3 ряда
        db_buttons_frame = ttk.Frame(db_frame)
        db_buttons_frame.pack(fill=tk.X)
        
        # Первый ряд кнопок
        db_row1 = ttk.Frame(db_buttons_frame)
        db_row1.pack(fill=tk.X, pady=(0, 2))
        
        btn_db_stats = ttk.Button(db_row1, text="📊 Статистика", command=self.on_show_db_stats, width=18)
        btn_db_stats.pack(side=tk.LEFT, padx=(0, 3), expand=True, fill=tk.X)
        self.lockable_widgets.append(btn_db_stats)
        
        btn_db_export = ttk.Button(db_row1, text="📤 Экспорт в Excel", command=self.on_export_database, width=18)
        btn_db_export.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
        self.lockable_widgets.append(btn_db_export)
        
        btn_db_backup = ttk.Button(db_row1, text="💾 Резервная копия", command=self.on_backup_database, width=18)
        btn_db_backup.pack(side=tk.LEFT, padx=(3, 0), expand=True, fill=tk.X)
        self.lockable_widgets.append(btn_db_backup)
        
        # Второй ряд кнопок
        db_row2 = ttk.Frame(db_buttons_frame)
        db_row2.pack(fill=tk.X, pady=(0, 2))
        
        btn_db_import = ttk.Button(db_row2, text="📥 Импорт из Excel", command=self.on_import_database, width=18)
        btn_db_import.pack(side=tk.LEFT, padx=(0, 3), expand=True, fill=tk.X)
        self.lockable_widgets.append(btn_db_import)
        
        btn_db_folder = ttk.Button(db_row2, text="📁 Открыть папку", command=self.on_open_db_folder, width=18)
        btn_db_folder.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
        self.lockable_widgets.append(btn_db_folder)
        
        btn_db_replace = ttk.Button(db_row2, text="🔄 Заменить БД", command=self.on_replace_database, width=18)
        btn_db_replace.pack(side=tk.LEFT, padx=(3, 0), expand=True, fill=tk.X)
        self.lockable_widgets.append(btn_db_replace)
        
        # Третий ряд - кнопка импорта из выходного файла (НОВОЕ!)
        db_row3 = ttk.Frame(db_buttons_frame)
        db_row3.pack(fill=tk.X)
        
        btn_db_import_output = ttk.Button(db_row3, text="⬇️ Добавить все из выходного файла", 
                                          command=self.on_import_from_output, 
                                          style='Accent.TButton')
        btn_db_import_output.pack(fill=tk.X, padx=0)
        self.lockable_widgets.append(btn_db_import_output)

        # Футер с информацией о разработчике
        self._create_footer()

    def _create_footer(self):
        """Создает футер с информацией о разработчике и базе данных"""
        footer = ttk.Frame(self)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        ttk.Separator(footer, orient='horizontal').pack(fill=tk.X, pady=(0, 2))
        
        # Первая строка: Разработчик и дата выпуска
        footer_text = ttk.Frame(footer)
        footer_text.pack()
        
        ttk.Label(footer_text, text="Разработчик: ", 
                 font=("Arial", 13)).pack(side=tk.LEFT)
        
        self.dev_label = tk.Label(footer_text, 
                                  text=self.cfg.get("app_info", {}).get("developer", "Н/Д"),
                                  font=("Arial", 13, "bold"),
                                  fg="#2E7D32",
                                  cursor="hand2")
        self.dev_label.pack(side=tk.LEFT)
        self.dev_label.bind("<Double-Button-1>", self.on_developer_double_click)
        
        ttk.Label(footer_text, text=" | ", 
                 font=("Arial", 13)).pack(side=tk.LEFT)
        
        ttk.Label(footer_text, 
                 text=f"Дата выпуска: {self.cfg.get('app_info', {}).get('release_date', 'N/A')}", 
                 font=("Arial", 13)).pack(side=tk.LEFT)
        
        # Вторая строка: Информация о базе данных
        db_info_frame = ttk.Frame(footer)
        db_info_frame.pack(pady=(1, 0))
        
        # Получаем информацию о базе данных
        try:
            db_path = get_database_path()
            db_stats = get_database_stats()
            
            # Определяем, откуда загружена БД
            if "AppData" in db_path or "Roaming" in db_path:
                location = "Установка (%APPDATA%)"
                location_color = "#1565C0"  # Синий
            else:
                location = "Проект (разработка)"
                location_color = "#F57C00"  # Оранжевый
            
            # Версия БД
            db_version = db_stats.get("metadata", {}).get("version", "N/A")
            total_components = db_stats.get("metadata", {}).get("total_components", 0)
            
            ttk.Label(db_info_frame, text="🗄️ БД: ", 
                     font=("Arial", 13)).pack(side=tk.LEFT)
            
            # Метка с версией БД с tooltip историей и кликом для открытия файла
            version_label = tk.Label(db_info_frame, 
                     text=f"v{db_version} ({total_components} компонентов)", 
                     font=("Arial", 13, "bold"),
                     foreground="#424242",
                     cursor="hand2",
                     bg=self.cget('bg'))
            version_label.pack(side=tk.LEFT)
            
            # Создаем tooltip с историей БД
            try:
                history_text = format_history_tooltip()
                ToolTip(version_label, history_text)
            except Exception as e:
                print(f"⚠️ Не удалось создать tooltip: {e}")
            
            # При клике открываем БД в текстовом редакторе
            version_label.bind("<Button-1>", lambda e: self.on_open_database_in_editor())
            
            ttk.Label(db_info_frame, text=" | ", 
                     font=("Arial", 13)).pack(side=tk.LEFT)
            
            ttk.Label(db_info_frame, text="📁 ", 
                     font=("Arial", 13)).pack(side=tk.LEFT)
            
            # Кликабельная метка для открытия папки
            location_label = tk.Label(db_info_frame, 
                    text=location, 
                    font=("Arial", 13, "bold"),
                    fg=location_color,
                    cursor="hand2")
            location_label.pack(side=tk.LEFT)
            
            # Привязываем клик к открытию папки
            location_label.bind("<Button-1>", lambda e: self.on_open_db_folder_from_footer())
            
        except Exception as e:
            # Если не удалось загрузить информацию о БД
            ttk.Label(db_info_frame, 
                     text="🗄️ БД: информация недоступна", 
                     font=("Arial", 13),
                     foreground="#757575").pack(side=tk.LEFT)

    def on_add_files(self):
        """Обработчик кнопки добавления файлов"""
        files = filedialog.askopenfilenames(
            title="Выберите файлы",
            filetypes=[
                ("Документы Word", "*.docx *.doc"),
                ("Excel", "*.xlsx"),
                ("Текст", "*.txt"),
            ],
        )
        if not files:
            return
        for f in files:
            if f not in self.input_files:
                self.input_files[f] = 1  # По умолчанию 1 экземпляр
        self.update_listbox()
        self.update_output_filename()  # Обновляем имя выходного файла

    def on_clear_files(self):
        """Обработчик кнопки очистки списка файлов"""
        self.input_files.clear()
        self.listbox.delete(0, tk.END)
        self.current_file_multiplier.set(1)
        self.selected_file_index = None
        self.output_xlsx.set("categorized.xlsx")  # Возврат к имени по умолчанию
    
    def update_listbox(self):
        """Обновляет отображение файлов в списке с указанием количества"""
        self.listbox.delete(0, tk.END)
        for file_path, count in self.input_files.items():
            display_text = f"{file_path}  [x{count}]"
            self.listbox.insert(tk.END, display_text)
        
        # Управление полем "Листы" в зависимости от количества .xlsx файлов
        xlsx_files = [f for f in self.input_files.keys() if f.lower().endswith(('.xlsx', '.xls'))]
        
        if len(xlsx_files) > 1:
            # Несколько .xlsx файлов - отключаем поле и показываем предупреждение
            self.sheet_entry.config(state='disabled')
            self.sheet_spec.set("")  # Очищаем значение
            self.sheets_warning_label.config(foreground='red')
        elif len(xlsx_files) == 1:
            # Один .xlsx файл - включаем поле, предупреждение обычное
            self.sheet_entry.config(state='normal')
            self.sheets_warning_label.config(foreground='gray')
        else:
            # Нет .xlsx файлов - отключаем поле
            self.sheet_entry.config(state='disabled')
            self.sheet_spec.set("")
            self.sheets_warning_label.config(foreground='gray')
    
    def update_output_filename(self):
        """
        Автоматически формирует имя выходного файла на основе входных файлов
        
        Логика:
        - Если один файл: имя_файла_out.xlsx в папке входного файла
        - Если несколько файлов: out.xlsx в папке первого файла
        - Если нет файлов: categorized.xlsx (по умолчанию)
        """
        if not self.input_files:
            self.output_xlsx.set("categorized.xlsx")
            return
        
        # Получаем первый файл (по порядку добавления)
        first_file = list(self.input_files.keys())[0]
        file_dir = os.path.dirname(first_file)
        
        if len(self.input_files) == 1:
            # Один файл: имя_файла_out.xlsx
            base_name = os.path.basename(first_file)
            name_without_ext = os.path.splitext(base_name)[0]
            output_name = f"{name_without_ext}_out.xlsx"
            output_path = os.path.join(file_dir, output_name)
        else:
            # Несколько файлов: out.xlsx
            output_path = os.path.join(file_dir, "out.xlsx")
        
        self.output_xlsx.set(output_path)
    
    def on_file_selected(self, event):
        """Обработчик выбора файла в списке"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        self.selected_file_index = idx  # Сохраняем индекс
        file_paths = list(self.input_files.keys())
        if idx < len(file_paths):
            selected_file = file_paths[idx]
            current_count = self.input_files.get(selected_file, 1)
            self.current_file_multiplier.set(current_count)
    
    def on_multiplier_changed(self):
        """Обработчик изменения количества для выбранного файла"""
        # Используем сохраненный индекс вместо текущего выделения
        if self.selected_file_index is None:
            messagebox.showwarning("Внимание", "Сначала выберите файл в списке")
            return
        
        idx = self.selected_file_index
        file_paths = list(self.input_files.keys())
        if idx < len(file_paths):
            selected_file = file_paths[idx]
            new_count = self.current_file_multiplier.get()
            if new_count < 1:
                new_count = 1
                self.current_file_multiplier.set(1)
            self.input_files[selected_file] = new_count
            self.update_listbox()
            # Восстанавливаем выделение
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)  # Прокручиваем к выбранному элементу

    def on_pick_output(self):
        """Обработчик выбора выходного файла"""
        f = filedialog.asksaveasfilename(title="Выберите выходной XLSX", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if f:
            self.output_xlsx.set(f)

    def on_pick_txt_dir(self):
        """Обработчик выбора папки для TXT файлов"""
        d = filedialog.askdirectory(title="Выберите папку для TXT файлов")
        if d:
            self.txt_dir.set(d)
    
    def on_select_compare_file1(self):
        """Обработчик выбора первого файла для сравнения"""
        f = filedialog.askopenfilename(
            title="Выберите первый файл (базовый)",
            filetypes=[("Excel", "*.xlsx")]
        )
        if f:
            self.compare_file1.set(f)
    
    def on_select_compare_file2(self):
        """Обработчик выбора второго файла для сравнения"""
        f = filedialog.askopenfilename(
            title="Выберите второй файл (новый)",
            filetypes=[("Excel", "*.xlsx")]
        )
        if f:
            self.compare_file2.set(f)
    
    def on_select_compare_output(self):
        """Обработчик выбора выходного файла для результатов сравнения"""
        f = filedialog.asksaveasfilename(
            title="Сохранить результат сравнения как",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if f:
            self.compare_output.set(f)
    
    def on_compare_files(self):
        """Обработчик кнопки сравнения файлов"""
        file1 = self.compare_file1.get().strip()
        file2 = self.compare_file2.get().strip()
        output = self.compare_output.get().strip()
        
        if not file1 or not file2:
            messagebox.showerror("Ошибка", "Выберите оба файла для сравнения")
            return
        
        if not output:
            messagebox.showerror("Ошибка", "Укажите имя файла для результатов")
            return
        
        # Формируем аргументы для CLI
        args = ["--compare", file1, file2, "--compare-output", output, "--no-interactive"]
        
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, f"Сравнение файлов:\n")
        self.txt.insert(tk.END, f"  Первый:  {file1}\n")
        self.txt.insert(tk.END, f"  Второй:  {file2}\n")
        self.txt.insert(tk.END, f"  Результат: {output}\n\n")
        self.update_idletasks()
        
        def after_compare(output_text):
            self.txt.insert(tk.END, output_text)
            self.txt.insert(tk.END, "\n\n✅ Сравнение завершено!\n")
            self.txt.see(tk.END)
            self.update_idletasks()
            
            # Предложить открыть файл
            if os.path.exists(output):
                result = messagebox.askyesno(
                    "Готово", 
                    f"Сравнение завершено!\nФайл сохранен: {output}\n\nОткрыть файл?"
                )
                if result:
                    import subprocess
                    subprocess.Popen([output], shell=True)
        
        run_cli_async(args, after_compare)

    def _build_args(self, output_file):
        """
        Формирует список аргументов для CLI
        
        Args:
            output_file: Путь к выходному файлу
            
        Returns:
            Список аргументов для передачи в CLI
        """
        args = []
        if self.input_files:
            # Формируем список файлов в формате "файл:количество"
            file_specs = []
            for file_path, count in self.input_files.items():
                if count > 1:
                    file_specs.append(f"{file_path}:{count}")
                else:
                    file_specs.append(file_path)
            args.extend(["--inputs"] + file_specs)
        sheet_txt = self.sheet_spec.get().strip()
        if sheet_txt:
            args.extend(["--sheets", sheet_txt])
        args.extend(["--xlsx", output_file])
        if self.combine.get():
            args.append("--combine")
        td = self.txt_dir.get().strip()
        if td:
            args.extend(["--txt-dir", td])

        # Всегда отключаем автоматический интерактивный режим в GUI
        args.append("--no-interactive")
        return args

    def check_and_convert_doc_files(self):
        """
        Проверяет наличие .doc файлов и предлагает конвертацию
        
        Returns:
            True если можно продолжить, False если нужно остановить
        """
        import os
        
        # Ищем .doc файлы (старый формат)
        doc_files = [f for f in self.input_files.keys() if f.lower().endswith('.doc') and not f.lower().endswith('.docx')]
        
        if not doc_files:
            return True  # Нет .doc файлов, продолжаем
        
        # Показываем диалог выбора
        dialog = tk.Toplevel(self)
        dialog.title("⚠️ Обнаружены .doc файлы")
        dialog.geometry("650x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"650x400+{x}+{y}")
        
        result = {"action": None}
        
        # Заголовок
        header = ttk.Label(dialog, text="⚠️ ВНИМАНИЕ: Обнаружены файлы в старом формате .doc", 
                          font=("Arial", 12, "bold"), foreground="orange")
        header.pack(pady=10)
        
        # Список файлов
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(info_frame, text="Следующие файлы имеют старый формат .doc:", 
                 font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
        
        files_text = tk.Text(info_frame, height=5, wrap=tk.WORD, font=("Courier", 12))
        files_text.pack(fill=tk.BOTH, expand=True)
        for doc_file in doc_files:
            files_text.insert(tk.END, f"  • {os.path.basename(doc_file)}\n")
        files_text.config(state=tk.DISABLED)
        
        # Пояснение
        explanation = ttk.Label(dialog, 
                               text="Библиотека python-docx работает только с новым форматом .docx\n"
                                    "Необходимо конвертировать файлы перед обработкой.",
                               font=("Arial", 11), foreground="gray")
        explanation.pack(pady=10)
        
        # Кнопки выбора
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(pady=20)
        
        def on_word_convert():
            result["action"] = "word"
            dialog.destroy()
        
        def on_manual():
            result["action"] = "manual"
            dialog.destroy()
        
        def on_cancel():
            result["action"] = "cancel"
            dialog.destroy()
        
        ttk.Button(buttons_frame, text="🔄 Конвертировать через Word (автоматически)", 
                  command=on_word_convert, width=40).pack(pady=5)
        
        ttk.Label(buttons_frame, text="Требуется установленный Microsoft Word", 
                 font=("Arial", 10), foreground="gray").pack()
        
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="📝 Конвертировать вручную (инструкция)", 
                  command=on_manual, width=40).pack(pady=5)
        
        ttk.Label(buttons_frame, text="Откроет инструкцию и остановит обработку", 
                 font=("Arial", 10), foreground="gray").pack()
        
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="❌ Отмена", 
                  command=on_cancel, width=40).pack(pady=5)
        
        dialog.wait_window()
        
        # Обработка выбора
        if result["action"] == "word":
            # Автоматическая конвертация через Word
            return self.convert_doc_files_with_word(doc_files)
        
        elif result["action"] == "manual":
            # Показываем инструкцию
            instruction = (
                "📝 ИНСТРУКЦИЯ ПО КОНВЕРТАЦИИ .doc → .docx\n\n"
                "1. Откройте каждый .doc файл в Microsoft Word\n"
                "2. Нажмите: Файл → Сохранить как\n"
                "3. В поле 'Тип файла' выберите: 'Документ Word (*.docx)'\n"
                "4. Нажмите 'Сохранить'\n"
                "5. Закройте Word\n"
                "6. Добавьте .docx файлы в программу вместо .doc\n"
                "7. Запустите обработку снова\n\n"
                "Список файлов для конвертации:\n"
            )
            for doc_file in doc_files:
                instruction += f"  • {doc_file}\n"
            
            messagebox.showinfo("Инструкция по конвертации", instruction)
            return False  # Остановить обработку
        
        else:  # cancel
            return False  # Остановить обработку
    
    def convert_doc_files_with_word(self, doc_files):
        """
        Конвертирует .doc файлы в .docx через Microsoft Word COM API
        
        Returns:
            True если успешно, False если ошибка
        """
        try:
            import win32com.client
        except ImportError:
            messagebox.showerror(
                "Ошибка",
                "Библиотека pywin32 не установлена!\n\n"
                "Установите командой:\n"
                "pip install pywin32\n\n"
                "Или используйте ручную конвертацию."
            )
            return False
        
        progress_dialog = tk.Toplevel(self)
        progress_dialog.title("Конвертация файлов")
        progress_dialog.geometry("500x200")
        progress_dialog.transient(self)
        progress_dialog.grab_set()
        
        # Центрируем
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (250)
        y = (progress_dialog.winfo_screenheight() // 2) - (100)
        progress_dialog.geometry(f"500x200+{x}+{y}")
        
        status_label = ttk.Label(progress_dialog, text="Инициализация...", font=("Arial", 12))
        status_label.pack(pady=20)
        
        progress_text = tk.Text(progress_dialog, height=6, wrap=tk.WORD, font=("Courier", 11))
        progress_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        success = True
        converted_files = []
        
        try:
            import os
            status_label.config(text="Запуск Microsoft Word...")
            progress_text.insert(tk.END, "Открытие Microsoft Word...\n")
            progress_dialog.update()
            
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            for i, doc_file in enumerate(doc_files, 1):
                status_label.config(text=f"Конвертация {i}/{len(doc_files)}: {os.path.basename(doc_file)}")
                progress_text.insert(tk.END, f"\n[{i}/{len(doc_files)}] {os.path.basename(doc_file)}\n")
                progress_dialog.update()
                
                doc_path = os.path.abspath(doc_file)
                docx_path = doc_path.replace('.doc', '.docx')
                
                try:
                    doc = word.Documents.Open(doc_path)
                    doc.SaveAs(docx_path, FileFormat=16)  # 16 = wdFormatXMLDocument
                    doc.Close()
                    
                    progress_text.insert(tk.END, f"  ✓ Создан: {os.path.basename(docx_path)}\n")
                    converted_files.append((doc_file, docx_path))
                    
                except Exception as e:
                    progress_text.insert(tk.END, f"  ✗ Ошибка: {str(e)}\n")
                    success = False
                
                progress_dialog.update()
            
            word.Quit()
            status_label.config(text="Готово!")
            progress_text.insert(tk.END, "\nКонвертация завершена.\n")
            
        except Exception as e:
            messagebox.showerror("Ошибка конвертации", f"Не удалось запустить Word:\n{str(e)}")
            success = False
        
        # Обновляем список файлов
        if success and converted_files:
            for old_file, new_file in converted_files:
                if old_file in self.input_files:
                    count = self.input_files[old_file]
                    del self.input_files[old_file]
                    self.input_files[new_file] = count
            
            self.update_listbox()
            self.update_output_filename()  # Обновляем имя выходного файла после конвертации
            progress_text.insert(tk.END, "\n✓ Список файлов обновлен\n")
        
        ttk.Button(progress_dialog, text="Закрыть", command=progress_dialog.destroy).pack(pady=10)
        progress_dialog.wait_window()
        
        return success
    
    def on_run(self):
        """Обработчик кнопки запуска обработки"""
        if not self.input_files:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один входной файл (XLSX/DOCX/DOC/TXT)")
            return
        
        # КРИТИЧНО: Проверяем и конвертируем .doc файлы
        if not self.check_and_convert_doc_files():
            return  # Пользователь отменил или нужна ручная конвертация
        
        args = self._build_args(self.output_xlsx.get())
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, f"Запуск: split_bom {' '.join(args)}\n\n")
        self.update_idletasks()

        def after_run(output_text):
            self.txt.insert(tk.END, output_text)
            self.txt.insert(tk.END, "\n\nГотово.\n")
            self.txt.see(tk.END)
            self.update_idletasks()
            
            # Извлекаем реальный путь выходного файла из вывода CLI
            import re
            match = re.search(r'XLSX written: (.+?)(?:\s+\(|$)', output_text)
            if match:
                actual_output_file = match.group(1).strip()
                self.check_and_offer_interactive_classification(actual_output_file)
            else:
                # Fallback на значение из поля
                self.check_and_offer_interactive_classification()
        
        run_cli_async(args, after_run)
    
    def check_and_offer_interactive_classification(self, output_file=None):
        """Проверяет наличие нераспределенных элементов и предлагает интерактивную классификацию"""
        if output_file is None:
            output_file = self.output_xlsx.get()
        if not output_file:
            return
        
        # Небольшая задержка для гарантии что файл записан
        import time
        time.sleep(0.5)
        
        if not os.path.exists(output_file):
            self.txt.insert(tk.END, f"\n⚠️ Выходной файл не найден: {output_file}\n")
            return
        
        try:
            import pandas as pd
            # Проверяем наличие листа "Не распределено"
            xls = pd.ExcelFile(output_file)
            
            self.txt.insert(tk.END, f"\n📊 Листы в файле: {', '.join(xls.sheet_names)}\n")
            
            if 'Не распределено' not in xls.sheet_names:
                self.txt.insert(tk.END, "✅ Все элементы успешно классифицированы!\n")
                return
            
            df_un = pd.read_excel(output_file, sheet_name='Не распределено')
            df_un_valid = df_un[df_un['Наименование ИВП'].notna()]
            
            if df_un_valid.empty:
                self.txt.insert(tk.END, "✅ Все элементы в листе 'Не распределено' пустые или уже классифицированы!\n")
                return
            
            # Есть нераспределенные элементы - предлагаем интерактивную классификацию
            count = len(df_un_valid)
            self.txt.insert(tk.END, f"\n⚠️ Обнаружено {count} нераспределённых элементов!\n")
            self.txt.see(tk.END)
            self.update_idletasks()
            
            response = messagebox.askyesno(
                "Интерактивная классификация",
                f"⚠️ Обнаружено {count} нераспределённых элементов!\n\n"
                f"Запустить интерактивный режим для их классификации?\n"
                f"Вы сможете вручную указать категорию для каждого элемента.",
                icon='warning'
            )
            
            if response:
                self.txt.insert(tk.END, f"\n🔄 Запуск интерактивной классификации для {count} элементов...\n")
                self.txt.see(tk.END)
                self.update_idletasks()
                self.open_classification_dialog(df_un_valid, output_file)
            else:
                self.txt.insert(tk.END, "ℹ️ Интерактивная классификация пропущена. Нераспределенные элементы остались в листе 'Не распределено'.\n")
        except Exception as e:
            # Показываем ошибку в лог
            self.txt.insert(tk.END, f"\n❌ Ошибка при проверке нераспределенных элементов: {e}\n")
            self.txt.see(tk.END)
            import traceback
            self.txt.insert(tk.END, f"Детали: {traceback.format_exc()}\n")

    def on_interactive_classify(self):
        """Обработчик кнопки интерактивной классификации"""
        # СНАЧАЛА проверяем наличие существующего выходного файла с листом "Не распределено"
        output_file = self.output_xlsx.get()
        
        if output_file and os.path.exists(output_file):
            # Проверяем наличие листа "Не распределено" в существующем файле
            try:
                import pandas as pd
                xls = pd.ExcelFile(output_file)
                
                if 'Не распределено' in xls.sheet_names:
                    df_un = pd.read_excel(output_file, sheet_name='Не распределено')
                    df_un_valid = df_un[df_un['Наименование ИВП'].notna()]
                    
                    if not df_un_valid.empty:
                        # Используем существующий файл!
                        self.txt.delete("1.0", tk.END)
                        self.txt.insert(tk.END, f"📂 Используется существующий файл: {output_file}\n")
                        self.txt.insert(tk.END, f"📊 Найдено {len(df_un_valid)} нераспределенных элементов\n\n")
                        self.update_idletasks()
                        
                        self.open_classification_dialog(df_un_valid, output_file)
                        return
            except Exception as e:
                # Если ошибка чтения существующего файла - продолжаем обработку заново
                self.txt.delete("1.0", tk.END)
                self.txt.insert(tk.END, f"⚠️ Не удалось использовать существующий файл: {e}\n")
                self.txt.insert(tk.END, "Создаем новый файл...\n\n")
                self.update_idletasks()
        
        # Если нет существующего файла с нераспределенными - создаем новый
        if not self.input_files:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один входной файл")
            return
        
        # Создаем временный выходной файл
        temp_output = "temp_for_classification.xlsx"
        
        # Запускаем обработку
        args = self._build_args(temp_output)
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, "Обработка файлов для определения нераспределенных элементов...\n")
        self.update_idletasks()
        
        def after_first_run(output_text):
            self.txt.insert(tk.END, output_text)
            self.update_idletasks()
            
            # Проверяем наличие нераспределенных элементов
            try:
                import pandas as pd
                df_un = pd.read_excel(temp_output, sheet_name='Не распределено')
                df_un_valid = df_un[df_un['Наименование ИВП'].notna()]
                
                if df_un_valid.empty:
                    messagebox.showinfo("Информация", "Все элементы успешно классифицированы!")
                    return
                
                # Открываем окно для интерактивной классификации
                self.open_classification_dialog(df_un_valid, temp_output)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось прочитать нераспределенные элементы: {e}")
        
        run_cli_async(args, after_first_run)
    
    def open_classification_dialog(self, df_unclassified, temp_output):
        """
        Открывает диалог для интерактивной классификации элементов
        
        Args:
            df_unclassified: DataFrame с нераспределенными элементами
            temp_output: Путь к временному выходному файлу
        """
        dialog = tk.Toplevel(self)
        dialog.title("Интерактивная классификация")
        dialog.geometry("900x650")
        dialog.grab_set()  # Модальное окно
        
        # Категории
        categories = [
            ("1", "Отладочные модули"),
            ("2", "Микросхемы"),
            ("3", "Резисторы"),
            ("4", "Конденсаторы"),
            ("5", "Индуктивности"),
            ("6", "Полупроводники"),
            ("7", "Разъемы"),
            ("8", "Оптические компоненты"),
            ("9", "Модули питания"),
            ("10", "Кабели"),
            ("11", "Другие"),
            ("12", "Не ИВП"),
            ("0", "Пропустить"),
        ]
        
        self.current_index = 0
        self.classifications = []
        unclassified_list = df_unclassified.to_dict('records')
        
        # Верхняя панель
        top_frame = ttk.Frame(dialog)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        progress_label = ttk.Label(top_frame, text="", font=("Arial", 12))
        progress_label.pack()
        
        # Средняя панель - информация об элементе
        info_frame = ttk.LabelFrame(dialog, text="Информация об элементе", padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        name_label = ttk.Label(info_frame, text="", font=("Arial", 14, "bold"), wraplength=850)
        name_label.pack(pady=10)
        
        details_frame = ttk.Frame(info_frame)
        details_frame.pack(fill=tk.X, pady=5)
        
        qty_label = ttk.Label(details_frame, text="", font=("Arial", 12))
        qty_label.pack(side=tk.LEFT, padx=10)
        
        source_label = ttk.Label(details_frame, text="", font=("Arial", 12))
        source_label.pack(side=tk.LEFT, padx=10)
        
        # Панель выбора категории
        cat_frame = ttk.LabelFrame(dialog, text="Выберите категорию (или нажмите 0-11 на клавиатуре)", padding=10)
        cat_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # Создаем 2 колонки кнопок
        left_col = ttk.Frame(cat_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        right_col = ttk.Frame(cat_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        def update_display():
            if self.current_index >= len(unclassified_list):
                # Все элементы классифицированы
                self.save_classifications_and_rerun(dialog, temp_output)
                return
            
            item = unclassified_list[self.current_index]
            progress_label.config(text=f"Элемент {self.current_index + 1} из {len(unclassified_list)}")
            name_label.config(text=f"{item.get('Наименование ИВП', 'N/A')}")
            qty_label.config(text=f"Количество: {item.get('Кол-во', 'N/A')}")
            source_label.config(text=f"Источник: {item.get('source_file', 'N/A')}")
        
        def on_category_select(cat_num):
            item = unclassified_list[self.current_index]
            if cat_num != "0":  # Не пропускать
                self.classifications.append({
                    "name": str(item.get('Наименование ИВП', '')),
                    "category_num": cat_num,
                    "category_name": dict(categories)[cat_num]
                })
            self.current_index += 1
            update_display()
        
        def on_key_press(event):
            key = event.char
            if key in dict(categories).keys():
                on_category_select(key)
        
        # Bind keyboard shortcuts
        dialog.bind('<Key>', on_key_press)
        
        # Создаем кнопки для каждой категории
        for i, (num, name) in enumerate(categories):
            col = left_col if i < len(categories) // 2 + 1 else right_col
            btn = ttk.Button(col, text=f"{num}. {name}", 
                            command=lambda n=num: on_category_select(n))
            btn.pack(fill=tk.X, pady=3)
        
        # Нижняя панель
        bottom_frame = ttk.Frame(dialog)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(bottom_frame, text=f"Правила будут сохранены в rules.json", 
                 font=("Arial", 11, "italic")).pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text="Отмена", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        update_display()
        dialog.focus_set()
    
    def save_classifications_and_rerun(self, dialog, temp_output):
        """
        Сохраняет классификации в rules.json и повторно запускает обработку
        
        Args:
            dialog: Диалоговое окно классификации
            temp_output: Путь к временному выходному файлу
        """
        dialog.destroy()
        
        if not self.classifications:
            messagebox.showinfo("Информация", "Никакие элементы не были классифицированы")
            return
        
        # Маппинг номеров категорий на внутренние имена
        cat_map = {
            "1": "dev_boards",
            "2": "ics",
            "3": "resistors",
            "4": "capacitors",
            "5": "inductors",
            "6": "semiconductors",
            "7": "connectors",
            "8": "optics",
            "9": "power_modules",
            "10": "cables",
            "11": "others",
            "12": "non_bom"
        }
        
        # Загружаем существующие правила
        rules_file = "rules.json"
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules = json.load(f)
        except:
            rules = []
        
        # Добавляем новые правила И сохраняем в базу данных
        added_count = 0
        db_added_count = 0
        for cls in self.classifications:
            # Извлекаем первое слово из названия как ключевое
            name = cls['name']
            category = cat_map.get(cls['category_num'], 'others')
            
            # Сохраняем полное наименование в базу данных (ПРИОРИТЕТ!)
            add_component_to_database(name, category)
            db_added_count += 1
            
            words = name.split()
            if words:
                keyword = words[0].lower().strip()
                
                # Проверяем, нет ли уже такого правила
                if not any(r.get('contains') == keyword and r.get('category') == category for r in rules):
                    rules.append({
                        "contains": keyword,
                        "category": category,
                        "comment": f"Добавлено пользователем для '{name}'"
                    })
                    added_count += 1
        
        # Сохраняем правила
        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        
        self.txt.insert(tk.END, f"\n\n✅ Сохранено {db_added_count} компонентов в базу данных (высший приоритет)\n")
        self.txt.insert(tk.END, f"✅ Сохранено {added_count} новых правил классификации в {rules_file}\n")
        self.txt.insert(tk.END, "Повторная обработка с новыми правилами...\n\n")
        self.update_idletasks()
        
        # Повторно запускаем обработку с учетом правил
        args = self._build_args(self.output_xlsx.get())
        args.extend(["--assign-json", rules_file])
        
        def after_rerun(output_text):
            self.txt.insert(tk.END, output_text)
            self.txt.insert(tk.END, "\n\n✅ Обработка завершена с учетом новых правил!\n")
            self.txt.see(tk.END)
            self.update_idletasks()
            messagebox.showinfo("Готово", f"Обработка завершена!\n\nПрименено {added_count} новых правил классификации.\nОбщее количество правил: {len(rules)}")
        
        run_cli_async(args, after_rerun)

    def lock_interface(self):
        """Блокирует все элементы управления"""
        for widget in self.lockable_widgets:
            try:
                widget.config(state='disabled')
            except:
                pass
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, "🔒 Приложение заблокировано\n\n")
        self.txt.insert(tk.END, "Для разблокировки сделайте двойной клик по имени разработчика внизу окна.\n")
        self.txt.config(state='disabled')
        self.dev_label.config(fg="#2E7D32")
    
    def unlock_interface(self):
        """Разблокирует все элементы управления"""
        for widget in self.lockable_widgets:
            try:
                widget.config(state='normal')
            except:
                pass
        self.txt.config(state='normal')
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, "✅ Приложение разблокировано!\n\n")
        self.txt.insert(tk.END, "Вы можете начать работу.\n")
        self.dev_label.config(fg="black")
        self.unlocked = True
    
    def on_developer_double_click(self, event):
        """Обработчик двойного клика по имени разработчика"""
        if self.unlocked:
            messagebox.showinfo("Информация", 
                              f"Приложение: {self.cfg.get('app_info', {}).get('description', 'N/A')}\n"
                              f"Версия: {self.cfg.get('app_info', {}).get('version', 'N/A')}\n"
                              f"Дата выпуска: {self.cfg.get('app_info', {}).get('release_date', 'N/A')}\n"
                              f"Разработчик: {self.cfg.get('app_info', {}).get('developer', 'N/A')}")
        else:
            self.show_pin_dialog()
    
    # ========== Обработчики управления базой данных ==========
    
    def on_show_db_stats(self):
        """Показать статистику базы данных"""
        try:
            stats = get_database_stats()
            db_path = get_database_path()
            
            # Формируем текст статистики
            metadata = stats.get("metadata", {})
            categories = stats.get("categories", {})
            
            stats_text = f"""📊 СТАТИСТИКА БАЗЫ ДАННЫХ

📁 Расположение:
{db_path}

ℹ️ Общая информация:
• Версия БД: {metadata.get('version', 'N/A')}
• Создана: {metadata.get('created', 'N/A')}
• Обновлена: {metadata.get('last_updated', 'N/A')}
• Всего компонентов: {metadata.get('total_components', 0)}

📦 Распределение по категориям:
"""
            
            # Добавляем статистику по категориям
            if categories:
                for cat_id, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    cat_name = stats.get("category_names", {}).get(cat_id, cat_id)
                    stats_text += f"• {cat_name}: {count}\n"
            else:
                stats_text += "• Нет данных\n"
            
            # Создаем диалог
            dialog = tk.Toplevel(self)
            dialog.title("Статистика базы данных")
            dialog.geometry("600x500")
            dialog.transient(self)
            dialog.grab_set()
            
            # Текстовое поле с прокруткой
            text_frame = ttk.Frame(dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=(self.monospace_font, 12))
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.insert("1.0", stats_text)
            text_widget.configure(state="disabled")
            
            # Кнопка закрытия
            ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=(0, 10))
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить статистику:\n{str(e)}")
    
    def on_export_database(self):
        """Экспорт базы данных в Excel"""
        try:
            # Выбор файла для сохранения
            from datetime import datetime
            default_name = f"component_database_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            file_path = filedialog.asksaveasfilename(
                title="Экспорт базы данных",
                defaultextension=".xlsx",
                initialfile=default_name,
                filetypes=[("Excel файлы", "*.xlsx")]
            )
            
            if not file_path:
                return
            
            # Экспортируем
            export_database_to_excel(file_path)
            
            messagebox.showinfo("Успех", 
                              f"База данных успешно экспортирована!\n\n"
                              f"Файл: {os.path.basename(file_path)}\n\n"
                              f"Теперь вы можете:\n"
                              f"• Отредактировать компоненты в Excel\n"
                              f"• Перенести на другой ПК\n"
                              f"• Сохранить как резервную копию")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать базу данных:\n{str(e)}")
    
    def on_backup_database(self):
        """Создать резервную копию базы данных"""
        try:
            backup_file = backup_database()
            
            messagebox.showinfo("Успех", 
                              f"Резервная копия создана!\n\n"
                              f"Файл: {os.path.basename(backup_file)}\n\n"
                              f"Резервные копии хранятся в папке 'database_backups' "
                              f"рядом с базой данных.")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать резервную копию:\n{str(e)}")
    
    def on_import_database(self):
        """Импорт базы данных из Excel"""
        try:
            # Выбор файла для импорта
            file_path = filedialog.askopenfilename(
                title="Импорт базы данных",
                filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")]
            )
            
            if not file_path:
                return
            
            # Спрашиваем о режиме импорта
            result = messagebox.askyesnocancel(
                "Режим импорта",
                "Выберите режим импорта:\n\n"
                "• ДА - Объединить с существующей базой (добавить новые)\n"
                "• НЕТ - Заменить всю базу данных (старые данные удалятся)\n"
                "• ОТМЕНА - Отменить импорт"
            )
            
            if result is None:  # Отмена
                return
            
            replace_mode = not result  # True если выбрали НЕТ
            
            # Автоматическое резервное копирование перед импортом
            backup_file = backup_database()
            
            # Импортируем
            added_count = import_database_from_excel(file_path, replace=replace_mode)
            
            mode_text = "заменена" if replace_mode else "обновлена"
            messagebox.showinfo("Успех", 
                              f"База данных успешно {mode_text}!\n\n"
                              f"Импортировано компонентов: {added_count}\n\n"
                              f"Резервная копия создана автоматически:\n"
                              f"{os.path.basename(backup_file)}\n\n"
                              f"Перезапустите приложение чтобы увидеть\n"
                              f"актуальные данные в футере.")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать базу данных:\n{str(e)}")
    
    def on_open_db_folder(self):
        """Открыть папку с базой данных в проводнике"""
        try:
            db_path = get_database_path()
            folder_path = os.path.dirname(db_path)
            
            # Открываем в проводнике Windows
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f'open "{folder_path}"')
            else:  # Linux
                os.system(f'xdg-open "{folder_path}"')
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{str(e)}")
    
    def on_open_db_folder_from_footer(self):
        """Открыть папку с базой данных из футера (без сообщений об успехе)"""
        try:
            db_path = get_database_path()
            folder_path = os.path.dirname(db_path)
            
            # Открываем в проводнике Windows
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f'open "{folder_path}"')
            else:  # Linux
                os.system(f'xdg-open "{folder_path}"')
                
        except Exception as e:
            # Тихо игнорируем ошибки при клике из футера
            pass
    
    def on_open_database_in_editor(self):
        """Открывает файл базы данных в текстовом редакторе по умолчанию"""
        try:
            db_path = get_database_path()
            
            if not os.path.exists(db_path):
                messagebox.showerror("Ошибка", f"Файл базы данных не найден:\n{db_path}")
                return
            
            # Открываем в текстовом редакторе по умолчанию для каждой ОС
            if sys.platform == "win32":
                # Windows: используем notepad или ассоциированный редактор
                os.startfile(db_path)
            elif sys.platform == "darwin":  # macOS
                # macOS: используем TextEdit или ассоциированный редактор
                os.system(f'open -e "{db_path}"')
            else:  # Linux
                # Linux: используем xdg-open (откроет в редакторе по умолчанию)
                os.system(f'xdg-open "{db_path}"')
            
            self.txt.insert(tk.END, f"\n📝 Открыт файл БД: {os.path.basename(db_path)}\n")
            self.txt.see(tk.END)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл базы данных:\n{str(e)}")
    
    def on_replace_database(self):
        """Заменить текущую базу данных на другую из JSON файла"""
        try:
            # Выбор файла базы данных
            file_path = filedialog.askopenfilename(
                title="Выберите файл базы данных (component_database.json)",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            
            if not file_path:
                return
            
            # Проверяем что файл существует и валиден
            if not os.path.exists(file_path):
                messagebox.showerror("Ошибка", f"Файл не найден:\n{file_path}")
                return
            
            # Проверяем формат файла
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Проверяем что это база данных компонентов
                if not isinstance(data, dict):
                    messagebox.showerror("Ошибка", "Неверный формат файла!\n\nОжидается JSON с данными компонентов.")
                    return
                
                # Определяем количество компонентов
                if "components" in data:
                    component_count = len(data["components"])
                elif "metadata" in data or "categories" in data:
                    messagebox.showerror("Ошибка", "Файл не содержит компонентов!")
                    return
                else:
                    # Старый формат - прямой словарь
                    component_count = len(data)
                
                if component_count == 0:
                    result = messagebox.askyesno(
                        "Предупреждение",
                        "⚠️ Выбранная база данных пустая (0 компонентов)!\n\n"
                        "Это удалит все компоненты из текущей базы.\n\n"
                        "Продолжить?",
                        icon='warning'
                    )
                    if not result:
                        return
                
            except json.JSONDecodeError:
                messagebox.showerror("Ошибка", "Файл поврежден или имеет неверный формат JSON!")
                return
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{str(e)}")
                return
            
            # Получаем информацию о текущей базе
            current_db_path = get_database_path()
            current_stats = get_database_stats()
            current_count = current_stats.get('total', 0)
            
            # Подтверждение замены
            result = messagebox.askyesno(
                "Подтверждение замены",
                f"🔄 ЗАМЕНА БАЗЫ ДАННЫХ\n\n"
                f"Текущая база данных:\n"
                f"  📊 Компонентов: {current_count}\n"
                f"  📁 Расположение: ...{current_db_path[-50:]}\n\n"
                f"Новая база данных:\n"
                f"  📊 Компонентов: {component_count}\n"
                f"  📁 Файл: {os.path.basename(file_path)}\n\n"
                f"⚠️ Текущая база будет заменена!\n"
                f"Резервная копия будет создана автоматически.\n\n"
                f"Продолжить?",
                icon='warning'
            )
            
            if not result:
                return
            
            # Создаем резервную копию текущей базы
            try:
                backup_file = backup_database()
                self.txt.insert(tk.END, f"\n💾 Резервная копия создана:\n")
                self.txt.insert(tk.END, f"   {os.path.basename(backup_file)}\n")
            except Exception as e:
                result = messagebox.askyesno(
                    "Ошибка резервного копирования",
                    f"Не удалось создать резервную копию:\n{str(e)}\n\n"
                    f"Продолжить без резервной копии?",
                    icon='error'
                )
                if not result:
                    return
            
            # Копируем новую базу данных
            import shutil
            shutil.copy2(file_path, current_db_path)
            
            # Проверяем что копирование прошло успешно
            new_stats = get_database_stats()
            new_count = new_stats.get('total', 0)
            
            self.txt.insert(tk.END, f"\n✅ База данных успешно заменена!\n")
            self.txt.insert(tk.END, f"   Новое количество компонентов: {new_count}\n")
            self.txt.insert(tk.END, f"   Расположение: {current_db_path}\n\n")
            self.txt.see(tk.END)
            self.update_idletasks()
            
            messagebox.showinfo(
                "Успех", 
                f"✅ База данных успешно заменена!\n\n"
                f"Компонентов в новой базе: {new_count}\n\n"
                f"Резервная копия старой базы сохранена.\n\n"
                f"Перезапустите приложение чтобы увидеть\n"
                f"актуальные данные в футере."
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось заменить базу данных:\n{str(e)}")
            import traceback
            self.txt.insert(tk.END, f"\n❌ Ошибка замены базы данных: {e}\n")
            self.txt.insert(tk.END, f"{traceback.format_exc()}\n")
    
    def on_import_from_output(self):
        """Импорт всех компонентов из выходного файла в базу данных"""
        try:
            # Проверяем есть ли выходной файл
            output_file = self.output_xlsx.get()
            
            if not output_file or not os.path.exists(output_file):
                messagebox.showerror("Ошибка", 
                                   "Выходной файл не найден!\n\n"
                                   "Сначала обработайте входные файлы, "
                                   "проверьте результат, а затем импортируйте компоненты в базу данных.")
                return
            
            # Подтверждение
            result = messagebox.askyesno(
                "Импорт из выходного файла",
                f"Вы хотите добавить ВСЕ компоненты из файла:\n\n"
                f"{os.path.basename(output_file)}\n\n"
                f"в базу данных?\n\n"
                f"Это позволит автоматически классифицировать эти компоненты "
                f"в будущем при обработке других файлов.\n\n"
                f"Продолжить?",
                icon='question'
            )
            
            if not result:
                return
            
            # Создаем диалог прогресса
            progress_dialog = tk.Toplevel(self)
            progress_dialog.title("Импорт из выходного файла")
            progress_dialog.geometry("600x400")
            progress_dialog.transient(self)
            progress_dialog.grab_set()
            
            # Текстовое поле для вывода прогресса
            text_frame = ttk.Frame(progress_dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            progress_text = tk.Text(text_frame, wrap=tk.WORD, font=(self.monospace_font, 12))
            scrollbar = ttk.Scrollbar(text_frame, command=progress_text.yview)
            progress_text.configure(yscrollcommand=scrollbar.set)
            
            progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            progress_text.insert(tk.END, "📥 Импорт компонентов из выходного файла...\n")
            progress_text.insert(tk.END, f"Файл: {output_file}\n\n")
            self.update_idletasks()
            
            # Импортируем компоненты
            import pandas as pd
            
            # Маппинг русских названий листов на ключи категорий
            SHEET_TO_CATEGORY = {
                'Резисторы': 'resistors',
                'Конденсаторы': 'capacitors',
                'Индуктивности': 'inductors',
                'Полупроводники': 'semiconductors',
                'Микросхемы': 'ics',
                'Разъемы': 'connectors',
                'Оптика': 'optics',
                'СВЧ модули': 'rf_modules',
                'Кабели': 'cables',
                'Модули питания': 'power_modules',
                'Отладочные платы': 'dev_boards',
                'Наши разработки': 'our_developments',
                'Другие': 'others',
            }
            
            # Читаем файл Excel
            xl_file = pd.ExcelFile(output_file, engine='openpyxl')
            
            added_count = 0
            skipped_count = 0
            total_sheets = 0
            
            progress_text.insert(tk.END, "📊 Обработка листов:\n\n")
            self.update_idletasks()
            
            # Обрабатываем каждый лист
            for sheet_name in xl_file.sheet_names:
                # Пропускаем служебные листы
                if sheet_name in ['SOURCES', 'SUMMARY', 'Не распределено', 'INFO']:
                    continue
                
                # Проверяем что это лист категории
                if sheet_name not in SHEET_TO_CATEGORY:
                    continue
                
                category_key = SHEET_TO_CATEGORY[sheet_name]
                total_sheets += 1
                
                # Читаем данные
                df = pd.read_excel(output_file, sheet_name=sheet_name, engine='openpyxl')
                
                if df.empty:
                    continue
                
                # Ищем колонку с наименованием
                name_col = None
                for col in ['Наименование ИВП', 'Наименование', 'наименование ивп', 'наименование']:
                    if col in df.columns:
                        name_col = col
                        break
                
                if not name_col:
                    progress_text.insert(tk.END, f"⚠️  {sheet_name}: не найдена колонка с наименованием\n")
                    continue
                
                sheet_added = 0
                
                # Добавляем каждый компонент в базу данных
                for idx, row in df.iterrows():
                    name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
                    
                    # Пропускаем пустые названия
                    if not name or name == 'nan':
                        skipped_count += 1
                        continue
                    
                    # Добавляем в базу данных
                    add_component_to_database(name, category_key)
                    added_count += 1
                    sheet_added += 1
                
                progress_text.insert(tk.END, f"✅ {sheet_name}: добавлено {sheet_added} компонентов\n")
                self.update_idletasks()
            
            progress_text.insert(tk.END, f"\n✅ Импорт завершен!\n\n")
            progress_text.insert(tk.END, f"📈 Статистика:\n")
            progress_text.insert(tk.END, f"   Обработано листов: {total_sheets}\n")
            progress_text.insert(tk.END, f"   Добавлено компонентов: {added_count}\n")
            progress_text.insert(tk.END, f"   Пропущено (пустые): {skipped_count}\n\n")
            
            # Показываем обновленную статистику базы данных
            stats = get_database_stats()
            progress_text.insert(tk.END, f"📊 База данных после импорта:\n")
            progress_text.insert(tk.END, f"   Всего компонентов: {stats['total']}\n")
            
            # Кнопка закрытия
            ttk.Button(progress_dialog, text="Закрыть", command=progress_dialog.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать компоненты:\n{str(e)}")
    
    # ========== Конец обработчиков управления БД ==========
    
    def show_pin_dialog(self):
        """Показывает диалог ввода PIN-кода"""
        dialog = tk.Toplevel(self)
        dialog.title("Авторизация")
        dialog.geometry("320x140")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.transient(self)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Основной фрейм с отступами
        main_frame = ttk.Frame(dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        ttk.Label(main_frame, text="Введите PIN-код:", 
                 font=("Arial", 12)).pack(pady=(0, 10))
        
        # Поле ввода PIN
        pin_var = tk.StringVar()
        pin_entry = ttk.Entry(main_frame, textvariable=pin_var, show="●", 
                             font=("Arial", 14), justify="center", width=15)
        pin_entry.pack(pady=(0, 5))
        pin_entry.focus_set()
        
        # Метка ошибки
        error_label = ttk.Label(main_frame, text="", foreground="red", 
                               font=("Arial", 11))
        error_label.pack(pady=(0, 10))
        
        def check_pin():
            entered_pin = pin_var.get().strip()
            if entered_pin == self.correct_pin:
                dialog.destroy()
                self.unlock_interface()
            else:
                error_label.config(text="Неверный PIN-код")
                pin_entry.delete(0, tk.END)
                pin_entry.focus_set()
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="OK", command=check_pin, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy, width=12).pack(side=tk.LEFT)
        
        # Обработка Enter и Escape
        pin_entry.bind("<Return>", lambda e: check_pin())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    def check_first_run_and_offer_import(self):
        """
        Проверяет первый запуск и предлагает импортировать существующую БД
        """
        # Инициализируем БД из шаблона если её еще нет
        initialize_database_from_template()
        
        # Проверяем, является ли это первым запуском
        if not is_first_run():
            return  # Не первый запуск, ничего не делаем
        
        # Показываем диалог импорта
        dialog = tk.Toplevel(self)
        dialog.title("База данных компонентов")
        dialog.geometry("500x350")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.transient(self)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Основной фрейм с отступами
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, 
                                text="🗄️ База данных компонентов", 
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 15))
        
        # Основной текст
        info_text = """У вас уже есть база данных компонентов?

Вы можете импортировать её для автоматической
классификации компонентов.

Поддерживаемые форматы:
  • JSON (component_database.json)
  • Excel (component_database.xlsx)

Если базы нет - вы можете начать с нуля.
База будет пополняться автоматически по мере работы."""
        
        info_label = ttk.Label(main_frame, text=info_text, 
                              font=("Arial", 12), justify=tk.LEFT)
        info_label.pack(pady=(0, 20))
        
        # Фрейм для кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        def on_import():
            """Обработчик импорта БД"""
            dialog.destroy()
            
            # Выбираем файл для импорта
            filetypes = [
                ("Все поддерживаемые", "*.json;*.xlsx"),
                ("JSON файлы", "*.json"),
                ("Excel файлы", "*.xlsx"),
                ("Все файлы", "*.*")
            ]
            
            file_path = filedialog.askopenfilename(
                title="Выберите файл базы данных",
                filetypes=filetypes
            )
            
            if not file_path:
                return
            
            try:
                # Импортируем БД
                if file_path.endswith('.json'):
                    # Импорт JSON
                    import shutil
                    db_path = get_database_path()
                    shutil.copy2(file_path, db_path)
                    stats = get_database_stats()
                    imported_count = stats.get('total_components', 0)
                elif file_path.endswith('.xlsx'):
                    # Импорт Excel
                    imported_count = import_database_from_excel(file_path, replace=True)
                else:
                    messagebox.showerror("Ошибка", "Неподдерживаемый формат файла")
                    return
                
                # Показываем результат
                messagebox.showinfo(
                    "Импорт завершен",
                    f"✅ Успешно импортировано компонентов: {imported_count}\n\n"
                    f"База данных: {get_database_path()}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Ошибка импорта",
                    f"Не удалось импортировать базу данных:\n{str(e)}"
                )
        
        def on_start_fresh():
            """Обработчик начала с нуля"""
            dialog.destroy()
            # БД уже инициализирована из шаблона, ничего делать не нужно
        
        # Кнопка импорта
        import_btn = ttk.Button(button_frame, text="📁 Импортировать", 
                               command=on_import, width=20)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка "Начать с нуля"
        fresh_btn = ttk.Button(button_frame, text="✨ Начать с нуля", 
                              command=on_start_fresh, width=20)
        fresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Обработка Escape
        dialog.bind("<Escape>", lambda e: on_start_fresh())


def launch_gui():
    """Точка входа для запуска GUI приложения"""
    app = BOMCategorizerApp()
    app.mainloop()
