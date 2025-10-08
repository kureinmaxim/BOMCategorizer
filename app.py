import os
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import subprocess
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

from split_bom import main as cli_main


def run_cli_async(args_list, on_finish):
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
    cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"app_info": {"version": "dev", "description": "BOM Categorizer"}}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        ver = self.cfg.get("app_info", {}).get("version", "dev")
        name = self.cfg.get("app_info", {}).get("description", "BOM Categorizer")
        self.title(f"{name} v{ver}")
        self.geometry("720x600")

        self.input_files: list[str] = []
        self.sheet_spec = tk.StringVar()
        self.output_xlsx = tk.StringVar(value="categorized.xlsx")
        self.merge_into = tk.StringVar()
        self.combine = tk.BooleanVar(value=True)
        self.loose = tk.BooleanVar(value=False)
        self.interactive = tk.BooleanVar(value=False)
        self.assign_json = tk.StringVar()
        self.txt_dir = tk.StringVar()
        self.create_txt = tk.BooleanVar(value=False)
        
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
        pad = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="Входные файлы (XLSX/DOCX/DOC/TXT):").grid(row=row, column=0, sticky="w", **pad)
        btn1 = ttk.Button(frm, text="Добавить файлы", command=self.on_add_files)
        btn1.grid(row=row, column=1, sticky="w", **pad)
        self.lockable_widgets.append(btn1)
        
        btn2 = ttk.Button(frm, text="Очистить", command=self.on_clear_files)
        btn2.grid(row=row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn2)
        
        self.listbox = tk.Listbox(frm, height=5)
        self.listbox.grid(row=row+1, column=0, columnspan=3, sticky="nsew", **pad)
        self.lockable_widgets.append(self.listbox)
        frm.grid_rowconfigure(row+1, weight=1)
        frm.grid_columnconfigure(2, weight=1)

        row += 2
        ttk.Label(frm, text="Листы (например: Лист1,Лист2 или оставьте пустым для всех):").grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        entry1 = ttk.Entry(frm, textvariable=self.sheet_spec)
        entry1.grid(row=row+1, column=0, columnspan=3, sticky="ew", **pad)
        self.lockable_widgets.append(entry1)

        row += 2
        ttk.Label(frm, text="Выходной XLSX:").grid(row=row, column=0, sticky="w", **pad)
        entry2 = ttk.Entry(frm, textvariable=self.output_xlsx)
        entry2.grid(row=row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry2)
        
        btn3 = ttk.Button(frm, text="Сохранить как...", command=self.on_pick_output)
        btn3.grid(row=row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn3)

        row += 1
        ttk.Label(frm, text="Папка для TXT файлов (опционально):").grid(row=row, column=0, sticky="w", **pad)
        entry3 = ttk.Entry(frm, textvariable=self.txt_dir)
        entry3.grid(row=row, column=1, sticky="ew", **pad)
        self.lockable_widgets.append(entry3)
        
        btn4 = ttk.Button(frm, text="Выбрать...", command=self.on_pick_txt_dir)
        btn4.grid(row=row, column=2, sticky="w", **pad)
        self.lockable_widgets.append(btn4)

        row += 1
        chk1 = ttk.Checkbutton(frm, text="Суммарная комплектация (SUMMARY)", variable=self.combine)
        chk1.grid(row=row, column=0, sticky="w", **pad)
        self.lockable_widgets.append(chk1)
        
        chk2 = ttk.Checkbutton(frm, text="Более свободные эвристики", variable=self.loose)
        chk2.grid(row=row, column=1, sticky="w", **pad)
        self.lockable_widgets.append(chk2)

        row += 1
        btn5 = ttk.Button(frm, text="Запустить обработку", command=self.on_run)
        btn5.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        self.lockable_widgets.append(btn5)
        
        btn6 = ttk.Button(frm, text="Интерактивная классификация", command=self.on_interactive_classify)
        btn6.grid(row=row, column=2, sticky="ew", **pad)
        self.lockable_widgets.append(btn6)

        row += 1
        ttk.Label(frm, text="Лог:").grid(row=row, column=0, sticky="w", **pad)
        self.txt = tk.Text(frm, height=10, wrap=tk.WORD)
        self.txt.grid(row=row+1, column=0, columnspan=3, sticky="nsew", **pad)
        self.lockable_widgets.append(self.txt)
        frm.grid_rowconfigure(row+1, weight=2)
        
        # Футер с информацией о разработчике
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
                self.input_files.append(f)
                self.listbox.insert(tk.END, f)

    def on_clear_files(self):
        self.input_files.clear()
        self.listbox.delete(0, tk.END)

    def on_pick_output(self):
        f = filedialog.asksaveasfilename(title="Выберите выходной XLSX", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if f:
            self.output_xlsx.set(f)

    def on_pick_txt_dir(self):
        d = filedialog.askdirectory(title="Выберите папку для TXT файлов")
        if d:
            self.txt_dir.set(d)

    def _build_args(self, output_file):
        """Формирует список аргументов для CLI"""
        args = []
        if self.input_files:
            args.extend(["--inputs"] + self.input_files)
        sheet_txt = self.sheet_spec.get().strip()
        if sheet_txt:
            args.extend(["--sheets", sheet_txt])
        args.extend(["--xlsx", output_file])
        if self.combine.get():
            args.append("--combine")
        if self.loose.get():
            args.append("--loose")
        td = self.txt_dir.get().strip()
        if td:
            args.extend(["--txt-dir", td])
        # Всегда отключаем автоматический интерактивный режим в GUI
        args.append("--no-interactive")
        return args

    def on_run(self):
        if not self.input_files:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один входной файл (XLSX/DOCX/DOC/TXT)")
            return
        
        args = self._build_args(self.output_xlsx.get())
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, f"Запуск: split_bom {' '.join(args)}\n\n")
        self.update_idletasks()

        def after_run(output_text):
            self.txt.insert(tk.END, output_text)
            self.txt.insert(tk.END, "\n\nГотово.\n")
            self.txt.see(tk.END)
            self.update_idletasks()
            
            # Проверяем наличие нераспределенных элементов и предлагаем интерактивную классификацию
            self.check_and_offer_interactive_classification()
        
        run_cli_async(args, after_run)
    
    def check_and_offer_interactive_classification(self):
        """Проверяет наличие нераспределенных элементов и предлагает интерактивную классификацию"""
        output_file = self.output_xlsx.get()
        if not output_file or not os.path.exists(output_file):
            return
        
        try:
            import pandas as pd
            # Проверяем наличие листа "Не распределено"
            xls = pd.ExcelFile(output_file)
            if 'Не распределено' not in xls.sheet_names:
                return
            
            df_un = pd.read_excel(output_file, sheet_name='Не распределено')
            df_un_valid = df_un[df_un['Наименование ИВП'].notna()]
            
            if df_un_valid.empty:
                return
            
            # Есть нераспределенные элементы - предлагаем интерактивную классификацию
            count = len(df_un_valid)
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
        except Exception as e:
            # Если не удалось прочитать - ничего страшного, просто пропускаем
            pass

    def on_interactive_classify(self):
        """Интерактивная классификация нераспределенных элементов"""
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
        """Открывает диалог для классификации элементов"""
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
        """Сохраняет классификации в rules.json и повторно запускает обработку"""
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
        dialog.title("Ввод PIN-кода")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg='white')
        
        # Центрируем окно
        dialog.transient(self)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Заголовок
        tk.Label(dialog, text="🔐 Введите PIN-код для разблокировки:", 
                font=("Arial", 11, "bold"), bg='white').pack(pady=(20, 15))
        
        # Поле ввода PIN
        pin_var = tk.StringVar()
        pin_entry = tk.Entry(dialog, textvariable=pin_var, show="●", 
                            font=("Arial", 16), justify="center", width=12,
                            relief=tk.SOLID, bd=2)
        pin_entry.pack(pady=(0, 10))
        pin_entry.focus_set()
        
        # Метка ошибки
        error_label = tk.Label(dialog, text="", foreground="red", 
                              font=("Arial", 9), bg='white')
        error_label.pack(pady=(0, 15))
        
        def check_pin():
            entered_pin = pin_var.get().strip()
            if entered_pin == self.correct_pin:
                dialog.destroy()
                self.unlock_interface()
            else:
                error_label.config(text="❌ Неверный PIN-код!")
                pin_entry.delete(0, tk.END)
                pin_entry.focus_set()
                # Тряска окна для визуального эффекта ошибки
                original_x = dialog.winfo_x()
                for i in range(3):
                    dialog.geometry(f"+{original_x-10}+{y}")
                    dialog.update()
                    dialog.after(50)
                    dialog.geometry(f"+{original_x+10}+{y}")
                    dialog.update()
                    dialog.after(50)
                dialog.geometry(f"+{original_x}+{y}")
        
        # Кнопки
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Button(btn_frame, text="Разблокировать", command=check_pin,
                 font=("Arial", 10, "bold"), bg='#4CAF50', fg='white',
                 relief=tk.RAISED, bd=2, padx=10, pady=8, width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy,
                 font=("Arial", 10), bg='#f0f0f0',
                 relief=tk.RAISED, bd=2, padx=10, pady=8, width=10).pack(side=tk.LEFT, padx=5)
        
        # Обработка Enter
        pin_entry.bind("<Return>", lambda e: check_pin())
        dialog.bind("<Escape>", lambda e: dialog.destroy())


if __name__ == "__main__":
    app = App()
    app.mainloop()

