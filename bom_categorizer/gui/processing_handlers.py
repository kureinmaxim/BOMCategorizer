# -*- coding: utf-8 -*-
"""
Processing handlers module for BOMCategorizer GUI.

This module contains mixin methods for BOM processing callbacks in the main window.
Following Lego Principle: single responsibility per module.
"""

import os
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from .main_window import BOMCategorizerMainWindow


class ProcessingHandlersMixin:
    """Mixin class containing BOM processing callback methods for main window."""

    def on_processing_progress(self: 'BOMCategorizerMainWindow', message: str):
        """Обработка прогресса обработки"""
        self.log_text.append(message)
    
    def on_processing_finished(self: 'BOMCategorizerMainWindow', message: str, success: bool, output_file: str):
        """Обработка завершения обработки"""
        # Закрываем progress dialog
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        # Добавляем сообщение в лог
        self.log_text.append("\n" + message)
        
        # Показываем результат
        if success:
            # Сохраняем путь для экспорта
            if output_file:
                self.last_generated_output = output_file
            
            # Удаляем промежуточные файлы конвертации (doc -> docx)
            self.cleanup_converted_files()
                
            QMessageBox.information(self, "Готово", message)
            
            # Проверяем наличие нераспределенных элементов
            if output_file:
                self.check_and_offer_interactive_classification(output_file)
                
                # Автоматический экспорт в PDF (если включен)
                if self.auto_export_pdf and os.path.exists(output_file):
                    self._auto_export_to_pdf(output_file)
                
                if self.auto_open_output and os.path.exists(output_file):
                    if self.reveal_in_file_manager(output_file, select=True):
                        self.log_text.append("📂 Автоматически открыт проводник с результатом")
                    else:
                        self.log_text.append("⚠️ Не удалось автоматически открыть папку результата")
        else:
            QMessageBox.critical(self, "Ошибка", message)
    
    def _auto_export_to_pdf(self: 'BOMCategorizerMainWindow', output_file: str):
        """Автоматический экспорт в PDF"""
        try:
            from ..pdf_exporter import export_bom_to_pdf
            
            # Создаем путь для PDF
            pdf_path = os.path.splitext(output_file)[0] + ".pdf"
            
            # Собираем сводную информацию
            summary_info = {
                "Исходных файлов": len(self.input_files) if hasattr(self, 'input_files') else 0,
                "Выходной файл": os.path.basename(output_file),
                "Версия БД": self.db.get_version() if hasattr(self, 'db') else "N/A",
                "Программа": f"BOM Categorizer {self.cfg.get('app_info', {}).get('version', 'dev')}"
            }
            
            if self.log_text:
                self.log_text.append(f"📄 Автоматический экспорт в PDF: {os.path.basename(pdf_path)}")
            
            # Выполняем экспорт
            result_pdf = export_bom_to_pdf(
                output_file,
                pdf_path,
                with_summary=True,
                summary_info=summary_info
            )
            
            if self.log_text:
                self.log_text.append(f"✅ PDF создан автоматически: {result_pdf}")
        
        except ImportError as e:
            if self.log_text:
                self.log_text.append(f"⚠️ Не удалось выполнить автоматический экспорт в PDF: библиотека reportlab не установлена")
            QMessageBox.warning(
                self,
                "Автоэкспорт в PDF",
                f"Не удалось выполнить автоматический экспорт в PDF.\n"
                f"Библиотека reportlab не установлена.\n\n"
                f"Установите: pip install reportlab\n\n"
                f"Ошибка: {e}"
            )
        except Exception as e:
            if self.log_text:
                self.log_text.append(f"⚠️ Ошибка автоматического экспорта в PDF: {e}")
    
    def _regenerate_pdf_after_classification(self: 'BOMCategorizerMainWindow', output_file: str):
        """Регенерирует PDF после интерактивной классификации"""
        try:
            from ..pdf_exporter import export_bom_to_pdf
            
            # Создаем путь для PDF
            pdf_path = os.path.splitext(output_file)[0] + ".pdf"
            
            # Собираем сводную информацию
            summary_info = {
                "Исходных файлов": len(self.input_files) if hasattr(self, 'input_files') else 0,
                "Выходной файл": os.path.basename(output_file),
                "Версия БД": self.db.get_version() if hasattr(self, 'db') else "N/A",
                "Программа": f"BOM Categorizer {self.cfg.get('app_info', {}).get('version', 'dev')}"
            }
            
            if self.log_text:
                self.log_text.append(f"📄 Регенерация PDF после классификации: {os.path.basename(pdf_path)}")
            
            # Выполняем экспорт
            result_pdf = export_bom_to_pdf(
                output_file,
                pdf_path,
                with_summary=True,
                summary_info=summary_info
            )
            
            if self.log_text:
                self.log_text.append(f"✅ PDF обновлен: {result_pdf}")
        
        except ImportError as e:
            if self.log_text:
                self.log_text.append(f"⚠️ Не удалось регенерировать PDF: библиотека reportlab не установлена")
        except Exception as e:
            if self.log_text:
                self.log_text.append(f"⚠️ Ошибка регенерации PDF: {e}")
    
    def check_and_offer_interactive_classification(self: 'BOMCategorizerMainWindow', output_file: str):
        """Проверяет наличие нераспределенных элементов и предлагает интерактивную классификацию"""
        if not output_file or not os.path.exists(output_file):
            return
        
        try:
            import pandas as pd
            # Проверяем наличие листа "Не распределено"
            xls = pd.ExcelFile(output_file, engine='openpyxl')
            
            self.log_text.append(f"\n📊 Листы в файле: {', '.join(xls.sheet_names)}\n")
            
            if 'Не распределено' not in xls.sheet_names:
                self.log_text.append("✅ Все элементы успешно классифицированы!\n")
                return
            
            df_un = pd.read_excel(output_file, sheet_name='Не распределено', engine='openpyxl')
            df_un_valid = df_un[df_un['Наименование ИВП'].notna()]
            
            unclassified_count = len(df_un_valid)
            
            if unclassified_count == 0:
                self.log_text.append("✅ Все элементы успешно классифицированы!\n")
                return
            
            self.log_text.append(f"\n⚠️ Найдено нераспределенных элементов: {unclassified_count}\n")
            
            # Предлагаем интерактивную классификацию
            reply = QMessageBox.question(
                self,
                "Интерактивная классификация",
                f"Найдено {unclassified_count} нераспределенных элементов.\n\n"
                f"Хотите классифицировать их вручную?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.run_interactive_classification(output_file)
                
        except Exception as e:
            self.log_text.append(f"⚠️ Не удалось проверить нераспределенные элементы: {e}")
