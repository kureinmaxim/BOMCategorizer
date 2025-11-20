# -*- coding: utf-8 -*-
"""
Worker потоки для фоновых задач GUI

Содержит классы для выполнения длительных операций в отдельных потоках:
- ProcessingWorker: обработка BOM файлов
- ComparisonWorker: сравнение BOM файлов
"""

import os
import sys
from io import StringIO
from PySide6.QtCore import QThread, Signal


class ProcessingWorker(QThread):
    """Worker thread для обработки BOM файлов"""
    finished = Signal(str, bool, str)  # (message, success, output_file)
    progress = Signal(str)  # progress message
    
    def __init__(self, args: list):
        super().__init__()
        self.args = args
        self.output_file = ""
    
    def run(self):
        """Выполняет обработку в отдельном потоке"""
        try:
            from .main import main as cli_main
            
            # Перехватываем stdout для получения прогресса
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_stdin = sys.stdin
            old_argv = sys.argv
            
            captured_output = StringIO()
            
            try:
                sys.stdout = captured_output
                sys.stderr = captured_output
                # КРИТИЧНО: Перенаправляем stdin на пустой StringIO, чтобы input() сразу вызывал EOFError
                sys.stdin = StringIO()
                sys.argv = ["split_bom.py"] + self.args
                
                # Отправляем начальное сообщение
                self.progress.emit("⏳ Начинаем обработку файлов...\n")
                self.progress.emit(f"Команда: split_bom {' '.join(self.args)}\n\n")
                self.progress.emit("🔧 Запуск CLI...\n")
                
                # Запускаем обработку
                cli_main()
                
                self.progress.emit("✅ CLI завершен успешно\n")
                
                # Восстанавливаем
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.argv = old_argv
                
                # Получаем вывод
                output_text = captured_output.getvalue()
                
                # Фильтруем проблемные символы
                output_text = output_text.replace('\u2192', '->')
                output_text = output_text.encode('utf-8', errors='replace').decode('utf-8')
                
                if output_text:
                    self.progress.emit(output_text)
                
                # Извлекаем путь к выходному файлу
                import re
                match = re.search(r'XLSX written: (.+?)(?:\s+\(|$)', output_text)
                if match:
                    self.output_file = match.group(1).strip()
                else:
                    # Ищем в аргументах
                    if "--xlsx" in self.args:
                        idx = self.args.index("--xlsx")
                        if idx + 1 < len(self.args):
                            self.output_file = self.args[idx + 1]
                
                # Проверяем что файл создан
                if self.output_file and os.path.exists(self.output_file):
                    self.finished.emit(f"✅ Обработка завершена!\nФайл сохранен: {self.output_file}", True, self.output_file)
                else:
                    self.finished.emit("⚠️ Обработка завершена, но выходной файл не найден", False, "")
                    
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin = old_stdin
                sys.argv = old_argv
                
        except SystemExit as e:
            # CLI может вызывать sys.exit(), это нормально
            if e.code == 0:
                self.finished.emit("✅ Обработка завершена!", True, self.output_file)
            else:
                error_msg = f"❌ Ошибка при обработке (код {e.code})"
                self.finished.emit(error_msg, False, "")
        except Exception as e:
            import traceback
            error_msg = f"❌ Ошибка при обработке:\n{str(e)}\n\n{traceback.format_exc()}"
            self.finished.emit(error_msg, False, "")


class ComparisonWorker(QThread):
    """Worker thread для сравнения BOM файлов"""
    finished = Signal(str, bool)  # (message, success)
    progress = Signal(str)  # progress message
    
    def __init__(self, file1: str, file2: str, output: str):
        super().__init__()
        self.file1 = file1
        self.file2 = file2
        self.output = output
    
    def run(self):
        """Выполняет сравнение в отдельном потоке"""
        try:
            from .main import compare_processed_files
            
            # Перехватываем stdout для получения прогресса с правильной кодировкой
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            # Создаем StringIO который поддерживает Unicode
            captured_output = StringIO()
            
            try:
                # Используем UTF-8 для вывода
                sys.stdout = captured_output
                sys.stderr = captured_output
                
                # Отправляем начальное сообщение
                self.progress.emit("⏳ Начинаем сравнение файлов...\n")
                self.progress.emit(f"📄 Файл 1: {os.path.basename(self.file1)}\n")
                self.progress.emit(f"📄 Файл 2: {os.path.basename(self.file2)}\n\n")
                
                self.progress.emit("🔍 Проверка формата файлов...\n")
                
                # Пытаемся сравнить как обработанные файлы
                success = compare_processed_files(self.file1, self.file2, self.output)
                
                if not success:
                    # Файлы не обработанные - показываем предупреждение
                    self.progress.emit("\n⚠️ ВНИМАНИЕ: Файлы не являются обработанными BOM файлами!\n")
                    self.progress.emit("   Обработанные файлы должны содержать листы с категориями:\n")
                    self.progress.emit("   (Резисторы, Конденсаторы, Микросхемы и т.д.)\n\n")
                    self.progress.emit("❌ Для сравнения необходимо:\n")
                    self.progress.emit("   1. Сначала обработать исходные BOM файлы\n")
                    self.progress.emit("   2. Затем сравнить полученные результаты\n\n")
                    self.progress.emit("💡 Или используйте исходные (необработанные) файлы для сравнения\n")
                    self.finished.emit(
                        "⚠️ Ошибка: файлы не являются обработанными BOM файлами!\n\n"
                        "Для сравнения используйте:\n"
                        "• Обработанные файлы (с листами категорий)\n"
                        "• Или исходные BOM файлы (.docx, .xlsx)", 
                        False
                    )
                    return
                
                # Восстанавливаем stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                # Получаем вывод
                output_text = captured_output.getvalue()
                
                # Фильтруем и очищаем вывод от проблемных символов
                output_text = output_text.replace('\u2192', '->')  # Заменяем стрелку
                output_text = output_text.encode('utf-8', errors='replace').decode('utf-8')
                
                if output_text:
                    self.progress.emit(output_text)
                
                # Проверяем что файл создан
                if os.path.exists(self.output):
                    self.finished.emit(f"✅ Сравнение завершено!\nФайл сохранен: {self.output}", True)
                else:
                    self.finished.emit("⚠️ Файл результата не создан", False)
                    
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
        except Exception as e:
            import traceback
            error_msg = f"❌ Ошибка при сравнении:\n{str(e)}\n\n{traceback.format_exc()}"
            self.finished.emit(error_msg, False)

