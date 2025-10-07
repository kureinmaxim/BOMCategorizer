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
        self.update_input_files()
        if not self.output_xlsx.get():
            self.autofill_output_path()
        self.update_terminal_commands()

    def on_clear_files(self):
        self.listbox.delete(0, tk.END)
        self.update_input_files()
        self.update_terminal_commands()

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

    def on_pick_assign(self):
        f = filedialog.askopenfilename(title="Выберите JSON", filetypes=[("JSON", "*.json")])
        if f:
            self.assign_json.set(f)

    def get_base_args(self, interactive_mode=False):
        args = []
        
        # Inputs
        inputs = list(self.input_files)
        if not inputs:
            return None

        if interactive_mode:
            args += ["--input", f'"{inputs[0]}"'] # Interactive script uses --input for a single file
        else:
            args += ["--inputs"] + [f'"{f}"' for f in inputs]

        # Outputs
        output_xlsx = self.output_xlsx.get().strip()
        if output_xlsx:
            if interactive_mode:
                args += ["--output", f'"{output_xlsx}"']
            else:
                args += ["--xlsx", f'"{output_xlsx}"']
        
        # Sheets
        sheets = self.sheet_spec.get().strip()
        if sheets:
            args += ["--sheets", f'"{sheets}"']

        # Rules
        assign_json = self.assign_json.get().strip()
        if assign_json:
            if interactive_mode:
                args += ["--rules", f'"{assign_json}"']
            else:
                args += ["--assign-json", f'"{assign_json}"']

        return args

    def update_terminal_commands(self, *args):
        # --- Command for split_bom.py ---
        base_args = self.get_base_args(interactive_mode=False)
        if not base_args:
            full_command = "# Добавьте входные файлы для генерации команды"
            interactive_command = "# Добавьте входной файл для генерации команды"
        else:
            # Standard command
            args_split_bom = base_args[:]
            if self.txt_dir.get().strip():
                args_split_bom += ["--txt-dir", f'"{self.txt_dir.get().strip()}"']
            if self.merge_into.get().strip():
                args_split_bom += ["--merge-into", f'"{self.merge_into.get().strip()}"']
            if self.combine.get():
                args_split_bom.append("--combine")
            if self.loose.get():
                args_split_bom.append("--loose")
            
            full_command = f".\\.venv\\Scripts\\python.exe split_bom.py {' '.join(args_split_bom)}"

            # --- Command for interactive_classify.py ---
            # Interactive mode only uses the first input file and a subset of args
            args_interactive = self.get_base_args(interactive_mode=True)
            interactive_command = f".\\.venv\\Scripts\\python.exe interactive_classify.py {' '.join(args_interactive)}"

        content = (
            "# Обычная обработка (автоматический режим):\n"
            f"{full_command}\n\n"
            "# Интерактивная классификация (для обучения):\n"
            f"{interactive_command}"
        )
        
        self.cmd_text.config(state=tk.NORMAL)
        self.cmd_text.delete("1.0", tk.END)
        self.cmd_text.insert("1.0", content)
        self.cmd_text.config(state=tk.DISABLED)


    def on_run(self):
        if not self.input_files:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один входной файл (XLSX/DOCX/DOC/TXT)")
            return
        
        base_args = self.get_base_args(interactive_mode=False)
        if not base_args: return # Should not happen due to check above
        
        # Start with base args and add the rest
        args = base_args[1:] # Remove --inputs prefix as it is handled differently by the list
        args = [arg.strip('"') for arg in args] # Remove quotes for subprocess
        
        run_args = ["--inputs"]

        # Find the end of input files list
        try:
            xlsx_index = args.index('--xlsx')
            run_args.extend(args[:xlsx_index])
            remaining_args = args[xlsx_index:]
        except ValueError:
            run_args.extend(args)
            remaining_args = []
        
        if self.txt_dir.get().strip():
            remaining_args += ["--txt-dir", self.txt_dir.get().strip()]
        if self.merge_into.get().strip():
            remaining_args += ["--merge-into", self.merge_into.get().strip()]
        if self.combine.get():
            remaining_args += ["--combine"]
        if self.loose.get():
            remaining_args += ["--loose"]
        
        # Re-add --assign-json if it was in remaining_args
        if "--assign-json" in remaining_args:
             pass # it is already there
        elif self.assign_json.get().strip():
             # it might have been consumed by get_base_args but we need it for split_bom
             if "--rules" not in remaining_args:
                 remaining_args += ["--assign-json", self.assign_json.get().strip()]

        final_args = run_args + remaining_args
        
        # Clear log and add new command
        self.txt.delete("1.0", tk.END)
        
        # Ensure all args are strings
        final_args = [str(arg) for arg in final_args]
        
        try:
            cmd_str = f"Запуск: split_bom {' '.join(final_args)}\n"
            self.txt.insert(tk.END, cmd_str)
            self.txt.see(tk.END)
            self.update()
        except Exception as e:
            self.txt.insert(tk.END, f"Ошибка формирования команды: {e}\n")
            return

        try:
            # Use a list of args for subprocess
            result = subprocess.run(
                [".\\.venv\\Scripts\\python.exe", "split_bom.py"] + final_args,
                capture_output=True, text=True, check=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.stdout:
                self.txt.insert(tk.END, result.stdout)
            self.txt.insert(tk.END, "\nГотово.\n")
        except subprocess.CalledProcessError as e:
            self.txt.insert(tk.END, f"Ошибка выполнения: {e.stderr}\n")
        except Exception as e:
            self.txt.insert(tk.END, f"Непредвиденная ошибка: {e}\n")
        
        self.txt.see(tk.END)


if __name__ == "__main__":
    app = App()
    app.mainloop()
