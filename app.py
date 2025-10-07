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
        cfg = load_config()
        ver = cfg.get("app_info", {}).get("version", "dev")
        name = cfg.get("app_info", {}).get("description", "BOM Categorizer")
        self.title(f"{name} v{ver}")
        self.geometry("720x560")

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

        self.create_widgets()

    def create_widgets(self):
        pad = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="Входные файлы (XLSX/DOCX/DOC/TXT):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Button(frm, text="Добавить файлы", command=self.on_add_files).grid(row=row, column=1, sticky="w", **pad)
        ttk.Button(frm, text="Очистить", command=self.on_clear_files).grid(row=row, column=2, sticky="w", **pad)
        self.listbox = tk.Listbox(frm, height=5)
        self.listbox.grid(row=row+1, column=0, columnspan=3, sticky="nsew", **pad)
        frm.grid_rowconfigure(row+1, weight=1)
        frm.grid_columnconfigure(2, weight=1)

        row += 2
        ttk.Label(frm, text="Листы (например: Лист1,Лист2 или оставьте пустым для всех):").grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.sheet_spec).grid(row=row+1, column=0, columnspan=3, sticky="ew", **pad)

        row += 2
        ttk.Label(frm, text="Выходной XLSX:").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.output_xlsx).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Сохранить как...", command=self.on_pick_output).grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Label(frm, text="Папка для TXT файлов (опционально):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.txt_dir).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Выбрать...", command=self.on_pick_txt_dir).grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Checkbutton(frm, text="Суммарная комплектация (SUMMARY)", variable=self.combine).grid(row=row, column=0, sticky="w", **pad)
        ttk.Checkbutton(frm, text="Более свободные эвристики", variable=self.loose).grid(row=row, column=1, sticky="w", **pad)

        row += 1
        ttk.Button(frm, text="Запустить обработку", command=self.on_run).grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        ttk.Button(frm, text="Интерактивная классификация", command=self.on_interactive_classify).grid(row=row, column=2, sticky="ew", **pad)

        row += 1
        ttk.Label(frm, text="Лог:").grid(row=row, column=0, sticky="w", **pad)
        self.txt = tk.Text(frm, height=10, wrap=tk.WORD)
        self.txt.grid(row=row+1, column=0, columnspan=3, sticky="nsew", **pad)
        frm.grid_rowconfigure(row+1, weight=2)

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
        
        run_cli_async(args, after_run)

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


if __name__ == "__main__":
    app = App()
    app.mainloop()

