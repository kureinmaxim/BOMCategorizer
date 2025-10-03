import os
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
        self.geometry("720x520")

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
        self.listbox = tk.Listbox(frm, height=6)
        self.listbox.grid(row=row+1, column=0, columnspan=3, sticky="nsew", **pad)
        frm.grid_rowconfigure(row+1, weight=1)
        frm.grid_columnconfigure(2, weight=1)

        row += 2
        ttk.Label(frm, text="Листы (например: 3,4). Для DOC/DOCX/TXT не требуется:").grid(row=row, column=0, columnspan=3, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.sheet_spec).grid(row=row+1, column=0, columnspan=3, sticky="ew", **pad)

        row += 2
        ttk.Label(frm, text="Существующий XLSX для добавления (опционально):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.merge_into).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Выбрать...", command=self.on_pick_merge).grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Label(frm, text="Выходной XLSX:").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.output_xlsx).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Сохранить как...", command=self.on_pick_output).grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Label(frm, text="JSON с правилами автоклассификации (опционально):").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.assign_json).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Выбрать...", command=self.on_pick_assign).grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Checkbutton(frm, text="Создать TXT по категориям", variable=self.create_txt, command=self.on_toggle_txt).grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.txt_dir).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Выбрать папку...", command=self.on_pick_txt_dir).grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Checkbutton(frm, text="Интерактивная разметка", variable=self.interactive).grid(row=row, column=0, sticky="w", **pad)
        ttk.Checkbutton(frm, text="Суммарная комплектация (SUMMARY)", variable=self.combine).grid(row=row, column=1, sticky="w", **pad)
        ttk.Checkbutton(frm, text="Более свободные эвристики", variable=self.loose).grid(row=row, column=2, sticky="w", **pad)

        row += 1
        ttk.Button(frm, text="Запустить", command=self.on_run).grid(row=row, column=0, sticky="w", **pad)

        row += 1
        ttk.Label(frm, text="Лог:").grid(row=row, column=0, sticky="w", **pad)
        self.txt = tk.Text(frm, height=12)
        self.txt.grid(row=row+1, column=0, columnspan=3, sticky="nsew", **pad)
        frm.grid_rowconfigure(row+1, weight=1)

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

    def on_pick_merge(self):
        f = filedialog.askopenfilename(title="Выберите существующий XLSX", filetypes=[("Excel", "*.xlsx")])
        if f:
            self.merge_into.set(f)

    def on_pick_output(self):
        f = filedialog.asksaveasfilename(title="Выберите выходной XLSX", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if f:
            self.output_xlsx.set(f)

    def on_pick_txt_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Выберите папку для TXT файлов")
        if d:
            self.txt_dir.set(d)
            self.create_txt.set(True)

    def on_toggle_txt(self):
        if self.create_txt.get() and not self.txt_dir.get().strip():
            # Auto-suggest directory name based on output XLSX
            import os
            xlsx_path = self.output_xlsx.get().strip()
            if xlsx_path:
                base_dir = os.path.dirname(xlsx_path) or "."
                base_name = os.path.splitext(os.path.basename(xlsx_path))[0]
                suggested_dir = os.path.join(base_dir, f"{base_name}_txt")
                self.txt_dir.set(suggested_dir)

    def on_run(self):
        if not self.input_files:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один входной файл (XLSX/DOCX/DOC/TXT)")
            return
        args = []
        args += ["--inputs"] + list(self.input_files)
        if self.sheet_spec.get().strip():
            args += ["--sheets", self.sheet_spec.get().strip()]
        args += ["--xlsx", self.output_xlsx.get().strip()]
        if self.merge_into.get().strip():
            args += ["--merge-into", self.merge_into.get().strip()]
        if self.combine.get():
            args += ["--combine"]
        if self.interactive.get():
            messagebox.showwarning("Предупреждение", "Интерактивный режим не поддерживается в GUI. Используйте командную строку для интерактивной классификации.")
            return
        if self.loose.get():
            args += ["--loose"]
        if self.assign_json.get().strip():
            args += ["--assign-json", self.assign_json.get().strip()]
        if self.create_txt.get() and self.txt_dir.get().strip():
            args += ["--txt-dir", self.txt_dir.get().strip()]

        self.txt.insert(tk.END, f"Запуск: split_bom {" ".join(args)}\n")
        self.txt.see(tk.END)

        def on_finish(output: str):
            self.txt.insert(tk.END, output + "\n")
            self.txt.insert(tk.END, "Готово.\n")
            self.txt.see(tk.END)

        run_cli_async(args, on_finish)

    def on_pick_assign(self):
        f = filedialog.askopenfilename(title="Выберите JSON", filetypes=[("JSON", "*.json")])
        if f:
            self.assign_json.set(f)


if __name__ == "__main__":
    app = App()
    app.mainloop()
