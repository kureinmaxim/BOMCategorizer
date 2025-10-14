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
        self.geometry("750x700")  # Стандартный размер с прокруткой

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
        self.exclude_items_text = None  # Текстовое поле для исключения элементов
        
        # Сравнение файлов
        self.compare_file1 = tk.StringVar()
        self.compare_file2 = tk.StringVar()
        self.compare_output = tk.StringVar(value="comparison.xlsx")
        
        # PIN protection
        self.unlocked = False
        self.require_pin = self.cfg.get("security", {}).get("require_pin", False)
        self.correct_pin = self.cfg.get("security", {}).get("pin", "5421")
        
        # Список виджетов для блокировки/разблокировки
        self.lockable_widgets = []

        self.create_widgets()
        
        # Блокируем интерфейс если требуется PIN
        if self.require_pin:
            self.lock_interface()

    def create_widgets(self):
        """Создает все виджеты интерфейса"""
        pad = {"padx": 8, "pady": 6}

        # Создать Canvas с вертикальной прокруткой
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_container)
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
        # Стиль для LabelFrame с жирным шрифтом
        style = ttk.Style()
        style.configure('Bold.TLabelframe.Label', font=('TkDefaultFont', 11, 'bold'))
        
        main_work_frame = ttk.LabelFrame(frm, text=" Основные настройки ", padding=10, style='Bold.TLabelframe')
        main_work_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        
        # Сбросить счетчик строк для рамки
        work_row = 0
        ttk.Label(main_work_frame, text="Входные файлы (XLSX/DOCX/DOC/TXT):").grid(row=work_row, column=0, sticky="w", **pad)
        btn1 = ttk.Button(main_work_frame, text="Добавить файлы", command=self.on_add_files)
        btn1.grid(row=work_row, column=1, sticky="w", **pad)
        self.lockable_widgets.append(btn1)
        
        btn2 = ttk.Button(main_work_frame, text="Очистить", command=self.on_clear_files)
        btn2.grid(row=work_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn2)
        
        self.listbox = tk.Listbox(main_work_frame, height=5)
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
                  font=('TkDefaultFont', 8), foreground='gray').pack(side="left", padx=(10, 0))

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
                               font=('TkDefaultFont', 8), 
                               foreground='gray',
                               wraplength=680)
        sheets_hint.grid(row=work_row, column=0, columnspan=3, sticky="w", **pad)
        self.sheets_warning_label = sheets_hint

        work_row += 1
        ttk.Label(main_work_frame, text="Выходной XLSX:").grid(row=work_row, column=0, sticky="w", **pad)
        entry2 = ttk.Entry(main_work_frame, textvariable=self.output_xlsx)
        entry2.grid(row=work_row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry2)
        
        btn3 = ttk.Button(main_work_frame, text="Сохранить как...", command=self.on_pick_output)
        btn3.grid(row=work_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn3)

        work_row += 1
        ttk.Label(main_work_frame, text="Папка для TXT файлов (опционально):").grid(row=work_row, column=0, sticky="w", **pad)
        entry3 = ttk.Entry(main_work_frame, textvariable=self.txt_dir)
        entry3.grid(row=work_row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry3)
        
        btn4 = ttk.Button(main_work_frame, text="Выбрать...", command=self.on_pick_txt_dir)
        btn4.grid(row=work_row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn4)

        work_row += 1
        chk1 = ttk.Checkbutton(main_work_frame, text="Суммарная комплектация (SUMMARY)", variable=self.combine)
        chk1.grid(row=work_row, column=0, columnspan=2, sticky="w", **pad)
        self.lockable_widgets.append(chk1)

        work_row += 1
        # Кнопки запуска - выделяем цветом и крупнее
        btn5 = ttk.Button(main_work_frame, text="▶ Запустить обработку", command=self.on_run)
        btn5.grid(row=work_row, column=0, columnspan=2, sticky="ew", **pad)
        self.lockable_widgets.append(btn5)
        
        btn6 = ttk.Button(main_work_frame, text="Интерактивная классификация", command=self.on_interactive_classify)
        btn6.grid(row=work_row, column=2, sticky="ew", **pad)
        self.lockable_widgets.append(btn6)
        
        # Продолжаем с основным фреймом
        # Секция для сравнения двух BOM файлов
        row += 1
        ttk.Separator(frm, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        
        row += 1
        ttk.Label(frm, text="Сравнение двух BOM файлов:", font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        ttk.Label(frm, text="Первый файл (базовый):").grid(row=row, column=0, sticky="w", **pad)
        entry_cmp1 = ttk.Entry(frm, textvariable=self.compare_file1)
        entry_cmp1.grid(row=row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry_cmp1)
        btn_cmp1 = ttk.Button(frm, text="Выбрать...", command=self.on_select_compare_file1)
        btn_cmp1.grid(row=row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn_cmp1)
        
        row += 1
        ttk.Label(frm, text="Второй файл (новый):").grid(row=row, column=0, sticky="w", **pad)
        entry_cmp2 = ttk.Entry(frm, textvariable=self.compare_file2)
        entry_cmp2.grid(row=row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry_cmp2)
        btn_cmp2 = ttk.Button(frm, text="Выбрать...", command=self.on_select_compare_file2)
        btn_cmp2.grid(row=row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn_cmp2)
        
        row += 1
        ttk.Label(frm, text="Файл результата:").grid(row=row, column=0, sticky="w", **pad)
        entry_cmp_out = ttk.Entry(frm, textvariable=self.compare_output)
        entry_cmp_out.grid(row=row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry_cmp_out)
        btn_cmp_out = ttk.Button(frm, text="Сохранить как...", command=self.on_select_compare_output)
        btn_cmp_out.grid(row=row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn_cmp_out)
        
        row += 1
        btn_compare = ttk.Button(frm, text="Сравнить файлы", command=self.on_compare_files)
        btn_compare.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        self.lockable_widgets.append(btn_compare)

        # Секция для исключения элементов из BOM
        row += 1
        ttk.Separator(frm, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        
        row += 1
        ttk.Label(frm, text="Исключение элементов из BOM:", font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        help_text_exclude = "Элементы будут удалены из входных данных в процессе обработки. Входной файл не изменяется, выходной файл создается уже без исключенных элементов."
        ttk.Label(frm, text=help_text_exclude, wraplength=700, justify='left').grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        ttk.Label(frm, text="Формат: Название ИВП, количество (по одному на строку). Пример: AD9221AR, 2").grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        ttk.Label(frm, text="После ввода элементов нажмите кнопку 'Запустить обработку' выше").grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        self.exclude_items_text = tk.Text(frm, height=4, wrap=tk.WORD)
        self.exclude_items_text.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        self.lockable_widgets.append(self.exclude_items_text)
        frm.grid_rowconfigure(row, weight=1)

        # Секция Лог
        row += 1
        ttk.Separator(frm, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        
        row += 1
        ttk.Label(frm, text="Лог:", font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, sticky="w", **pad)
        self.txt = tk.Text(frm, height=10, wrap=tk.WORD)
        self.txt.grid(row=row+1, column=0, columnspan=3, sticky="nsew", **pad)
        self.lockable_widgets.append(self.txt)
        frm.grid_rowconfigure(row+1, weight=2)
        
        # Секция для переноса компонентов в "Не распределено" (внизу)
        row += 2
        ttk.Separator(frm, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        
        row += 1
        ttk.Label(frm, text="Перенос компонентов в 'Не распределено':", font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        help_text = ("Эта функция работает с ВЫХОДНЫМ файлом, созданным ранее. Она перемещает указанные "
                     "компоненты из их текущих категорий (Резисторы, Конденсаторы и т.д.) в категорию "
                     "'Не распределено'. Используйте, если некоторые компоненты были ошибочно "
                     "классифицированы и нужно их вернуть для повторной обработки.")
        ttk.Label(frm, text=help_text, wraplength=700, justify='left').grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        ttk.Label(frm, text="Введите названия компонентов (по одному на строку, частичное совпадение):").grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        
        row += 1
        self.reclassify_text = tk.Text(frm, height=4, wrap=tk.WORD)
        self.reclassify_text.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        self.lockable_widgets.append(self.reclassify_text)
        frm.grid_rowconfigure(row, weight=1)
        
        row += 1
        btn7 = ttk.Button(frm, text="Перенести в 'Не распределено'", command=self.on_move_to_unclassified)
        btn7.grid(row=row, column=0, columnspan=3, sticky="ew", **pad)
        self.lockable_widgets.append(btn7)
        
        # Футер с информацией о разработчике
        self._create_footer()

    def _create_footer(self):
        """Создает футер с информацией о разработчике"""
        footer = ttk.Frame(self)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        ttk.Separator(footer, orient='horizontal').pack(fill=tk.X, pady=(0, 5))
        
        footer_text = ttk.Frame(footer)
        footer_text.pack()
        
        ttk.Label(footer_text, text="Разработчик: ", 
                 font=("Arial", 9)).pack(side=tk.LEFT)
        
        self.dev_label = tk.Label(footer_text, 
                                  text=self.cfg.get("app_info", {}).get("developer", "Н/Д"),
                                  font=("Arial", 9, "bold"),
                                  fg="#2E7D32",
                                  cursor="hand2")
        self.dev_label.pack(side=tk.LEFT)
        self.dev_label.bind("<Double-Button-1>", self.on_developer_double_click)
        
        ttk.Label(footer_text, text=" | ", 
                 font=("Arial", 9)).pack(side=tk.LEFT)
        
        ttk.Label(footer_text, 
                 text=f"Дата выпуска: {self.cfg.get('app_info', {}).get('release_date', 'N/A')}", 
                 font=("Arial", 9)).pack(side=tk.LEFT)

    def on_add_files(self):
        """Обработчик кнопки добавления файлов"""
        files = filedialog.askopenfilenames(
            title="Выберите файлы",
            filetypes=[
                ("Excel", "*.xlsx"),
                ("Документы Word", "*.docx *.doc"),
                ("Текст", "*.txt"),
            ],
        )
        if not files:
            return
        for f in files:
            if f not in self.input_files:
                self.input_files[f] = 1  # По умолчанию 1 экземпляр
        self.update_listbox()

    def on_clear_files(self):
        """Обработчик кнопки очистки списка файлов"""
        self.input_files.clear()
        self.listbox.delete(0, tk.END)
        self.current_file_multiplier.set(1)
        self.selected_file_index = None
    
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
        
        # Обработка исключений элементов
        if self.exclude_items_text:
            exclude_text = self.exclude_items_text.get("1.0", tk.END).strip()
            
            if exclude_text:
                # Создать временный файл с исключениями
                import tempfile
                temp_exclude_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                                                  suffix='.txt', delete=False)
                temp_exclude_file.write(exclude_text)
                temp_exclude_file.close()
                args.extend(["--exclude-items", temp_exclude_file.name])
        
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
        
        files_text = tk.Text(info_frame, height=5, wrap=tk.WORD, font=("Courier", 9))
        files_text.pack(fill=tk.BOTH, expand=True)
        for doc_file in doc_files:
            files_text.insert(tk.END, f"  • {os.path.basename(doc_file)}\n")
        files_text.config(state=tk.DISABLED)
        
        # Пояснение
        explanation = ttk.Label(dialog, 
                               text="Библиотека python-docx работает только с новым форматом .docx\n"
                                    "Необходимо конвертировать файлы перед обработкой.",
                               font=("Arial", 9), foreground="gray")
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
                 font=("Arial", 8), foreground="gray").pack()
        
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="📝 Конвертировать вручную (инструкция)", 
                  command=on_manual, width=40).pack(pady=5)
        
        ttk.Label(buttons_frame, text="Откроет инструкцию и остановит обработку", 
                 font=("Arial", 8), foreground="gray").pack()
        
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
        
        status_label = ttk.Label(progress_dialog, text="Инициализация...", font=("Arial", 10))
        status_label.pack(pady=20)
        
        progress_text = tk.Text(progress_dialog, height=6, wrap=tk.WORD, font=("Courier", 9))
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
            ("0", "Пропустить"),
        ]
        
        self.current_index = 0
        self.classifications = []
        unclassified_list = df_unclassified.to_dict('records')
        
        # Верхняя панель
        top_frame = ttk.Frame(dialog)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        progress_label = ttk.Label(top_frame, text="", font=("Arial", 10))
        progress_label.pack()
        
        # Средняя панель - информация об элементе
        info_frame = ttk.LabelFrame(dialog, text="Информация об элементе", padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        name_label = ttk.Label(info_frame, text="", font=("Arial", 12, "bold"), wraplength=850)
        name_label.pack(pady=10)
        
        details_frame = ttk.Frame(info_frame)
        details_frame.pack(fill=tk.X, pady=5)
        
        qty_label = ttk.Label(details_frame, text="", font=("Arial", 10))
        qty_label.pack(side=tk.LEFT, padx=10)
        
        source_label = ttk.Label(details_frame, text="", font=("Arial", 10))
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
                 font=("Arial", 9, "italic")).pack(side=tk.LEFT)
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
            "11": "others"
        }
        
        # Загружаем существующие правила
        rules_file = "rules.json"
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules = json.load(f)
        except:
            rules = []
        
        # Добавляем новые правила
        added_count = 0
        for cls in self.classifications:
            # Извлекаем первое слово из названия как ключевое
            name = cls['name']
            words = name.split()
            if words:
                keyword = words[0].lower().strip()
                category = cat_map.get(cls['category_num'], 'others')
                
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
        
        self.txt.insert(tk.END, f"\n\n✅ Сохранено {added_count} новых правил классификации в {rules_file}\n")
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
    
    def on_move_to_unclassified(self):
        """Обработчик переноса компонентов в 'Не распределено'"""
        # Проверяем наличие выходного файла
        output_file = self.output_xlsx.get()
        if not output_file or not os.path.exists(output_file):
            messagebox.showerror("Ошибка", 
                               f"Выходной файл не найден: {output_file}\n\n" +
                               "Сначала запустите обработку для создания файла.")
            return
        
        # Получаем список компонентов для переноса
        components_text = self.reclassify_text.get("1.0", tk.END).strip()
        if not components_text:
            messagebox.showwarning("Внимание", "Введите хотя бы один компонент для переноса.")
            return
        
        component_names = [line.strip() for line in components_text.split('\n') if line.strip()]
        
        try:
            import pandas as pd
            from openpyxl import load_workbook
            from openpyxl.utils.dataframe import dataframe_to_rows
            
            self.txt.insert(tk.END, f"\n\n🔄 Перенос компонентов в 'Не распределено'...\n")
            self.txt.insert(tk.END, f"Файл: {output_file}\n")
            self.txt.insert(tk.END, f"Компонентов для переноса: {len(component_names)}\n\n")
            self.update_idletasks()
            
            # Читаем все листы из Excel
            xls = pd.ExcelFile(output_file)
            all_sheets = {}
            for sheet_name in xls.sheet_names:
                all_sheets[sheet_name] = pd.read_excel(output_file, sheet_name=sheet_name)
            
            # Список для хранения найденных компонентов
            found_components = []
            moved_count = 0
            
            # Ищем компоненты во всех листах (кроме "Не распределено")
            for sheet_name in all_sheets.keys():
                if sheet_name == "Не распределено":
                    continue
                
                df = all_sheets[sheet_name]
                
                # Ищем компоненты по частичному совпадению в колонке "Наименование ИВП"
                if 'Наименование ИВП' not in df.columns:
                    continue
                
                for comp_name in component_names:
                    # Ищем строки, содержащие искомый текст (регистронезависимый поиск)
                    mask = df['Наименование ИВП'].astype(str).str.contains(comp_name, case=False, na=False)
                    matching_rows = df[mask]
                    
                    if not matching_rows.empty:
                        self.txt.insert(tk.END, f"  ✓ Найдено {len(matching_rows)} совпадений для '{comp_name}' в листе '{sheet_name}'\n")
                        self.update_idletasks()
                        
                        # Добавляем найденные строки к списку для переноса
                        for idx, row in matching_rows.iterrows():
                            found_components.append(row.to_dict())
                            moved_count += 1
                        
                        # Удаляем найденные строки из исходного листа
                        all_sheets[sheet_name] = df[~mask]
            
            if moved_count == 0:
                self.txt.insert(tk.END, "\n⚠️ Ни один компонент не найден в выходном файле.\n")
                self.txt.insert(tk.END, "Проверьте правильность написания названий компонентов.\n")
                messagebox.showwarning("Внимание", "Ни один компонент не найден в выходном файле.")
                return
            
            # Добавляем найденные компоненты в лист "Не распределено"
            if "Не распределено" not in all_sheets:
                # Создаем новый DataFrame для "Не распределено" с теми же колонками
                first_sheet_df = list(all_sheets.values())[0]
                all_sheets["Не распределено"] = pd.DataFrame(columns=first_sheet_df.columns)
            
            df_unclassified = all_sheets["Не распределено"]
            new_rows = pd.DataFrame(found_components)
            all_sheets["Не распределено"] = pd.concat([df_unclassified, new_rows], ignore_index=True)
            
            # Сохраняем изменения в файл
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for sheet_name, df in all_sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            self.txt.insert(tk.END, f"\n✅ Успешно перенесено {moved_count} компонентов в 'Не распределено'!\n")
            self.txt.insert(tk.END, "\nТеперь вы можете запустить 'Интерактивную классификацию' для правильной категоризации.\n")
            self.txt.see(tk.END)
            self.update_idletasks()
            
            # Очищаем текстовое поле
            self.reclassify_text.delete("1.0", tk.END)
            
            messagebox.showinfo("Готово", 
                              f"Успешно перенесено {moved_count} компонентов в 'Не распределено'!\n\n" +
                              "Теперь вы можете запустить 'Интерактивную классификацию'.")
            
        except Exception as e:
            error_msg = f"Ошибка при переносе компонентов: {e}"
            self.txt.insert(tk.END, f"\n❌ {error_msg}\n")
            self.txt.see(tk.END)
            import traceback
            self.txt.insert(tk.END, f"Детали: {traceback.format_exc()}\n")
            messagebox.showerror("Ошибка", error_msg)
    
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
                 font=("Arial", 10)).pack(pady=(0, 10))
        
        # Поле ввода PIN
        pin_var = tk.StringVar()
        pin_entry = ttk.Entry(main_frame, textvariable=pin_var, show="●", 
                             font=("Arial", 12), justify="center", width=15)
        pin_entry.pack(pady=(0, 5))
        pin_entry.focus_set()
        
        # Метка ошибки
        error_label = ttk.Label(main_frame, text="", foreground="red", 
                               font=("Arial", 9))
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


def launch_gui():
    """Точка входа для запуска GUI приложения"""
    app = BOMCategorizerApp()
    app.mainloop()
