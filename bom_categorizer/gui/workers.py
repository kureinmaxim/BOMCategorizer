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
        captured_output = StringIO()
        try:
            from ..main import main as cli_main
            
            # Перехватываем stdout для получения прогресса
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_stdin = sys.stdin
            old_argv = sys.argv
            
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
            # CLI может вызывать sys.exit(); код 0 — успех, иначе показываем лог CLI
            output_text = captured_output.getvalue()
            if output_text:
                try:
                    self.progress.emit(output_text)
                except Exception:
                    pass
            if e.code in (0, None):
                self.finished.emit("✅ Обработка завершена!", True, self.output_file)
            else:
                # Берём последние строки ошибки из CLI (не только «код N»)
                tail = ""
                if output_text:
                    lines = [ln for ln in output_text.strip().splitlines() if ln.strip()]
                    tail = "\n".join(lines[-12:])
                error_msg = f"❌ Ошибка при обработке (код {e.code})"
                if tail:
                    error_msg = f"{error_msg}\n\n{tail}"
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
            from ..main import compare_processed_files, compare_flat_files, detect_comparison_file_type
            
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
                
                self.progress.emit("🔍 Определение типа файлов...\n")
                
                # Определяем тип файлов
                type1 = detect_comparison_file_type(self.file1)
                type2 = detect_comparison_file_type(self.file2)
                
                self.progress.emit(f"   Файл 1: {type1}\n")
                self.progress.emit(f"   Файл 2: {type2}\n\n")
                
                # Выбираем алгоритм сравнения
                if type1 == 'flat' or type2 == 'flat':
                    # Хотя бы один файл плоский — используем сравнение плоских файлов
                    self.progress.emit("📊 Используем алгоритм сравнения плоских файлов (РКМ/Ostatki/Zapas)\n\n")
                    success = compare_flat_files(self.file1, self.file2, self.output)
                elif type1 == 'bom' and type2 == 'bom':
                    # Оба файла — BOM с категориями
                    self.progress.emit("📊 Используем алгоритм сравнения BOM файлов (по категориям)\n\n")
                    success = compare_processed_files(self.file1, self.file2, self.output)
                else:
                    # Неизвестные типы — пробуем как плоские
                    self.progress.emit("⚠️ Тип файлов не определён, пробуем сравнить как плоские...\n\n")
                    success = compare_flat_files(self.file1, self.file2, self.output)
                
                if not success:
                    # Сравнение не удалось
                    self.progress.emit("\n❌ Сравнение не удалось\n")
                    self.finished.emit(
                        "⚠️ Ошибка: не удалось сравнить файлы!\n\n"
                        "Проверьте:\n"
                        "• Оба файла существуют и доступны\n"
                        "• Файлы содержат данные с колонкой 'Наименование'", 
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


from ..tru_rkm_processor import process_tru_rkm_files

class TruRkmWorker(QThread):
    """
    Фоновый воркер для обработки ТРУ/РКМ файлов
    """
    progress = Signal(int, int, str, bool) # current, total, filename, success
    finished = Signal(dict) # results dict

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        # Используем callback для отправки сигналов прогресса
        def progress_callback(current, total, filename, success):
            self.progress.emit(current, total, filename, success)
            
        results = process_tru_rkm_files(self.file_paths, progress_callback)
        self.finished.emit(results)


