# -*- coding: utf-8 -*-
"""
File handlers module for BOMCategorizer GUI.

This module contains mixin methods for file operations in the main window.
Following Lego Principle: single responsibility per module.
"""

import os
import platform
from typing import TYPE_CHECKING, Dict, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton,
    QFileDialog, QMessageBox, QListWidgetItem, QProgressDialog, QApplication
)
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from .main_window import BOMCategorizerMainWindow


class FileHandlersMixin:
    """Mixin class containing file operation methods for main window."""

    def on_add_files(self: 'BOMCategorizerMainWindow'):
        """Добавление файлов"""
        # Import file type detection from tru_rkm_processor
        from ..tru_rkm_processor import detect_file_type
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы",
            "",
            "Документы Word (*.docx *.doc);;Excel (*.xlsx *.xls);;Текст (*.txt);;Все BOM файлы (*.xlsx *.xls *.docx *.doc *.txt);;Все файлы (*)"
        )

        if files:
            tru_rkm_added = []
            bom_added = []
            
            for file_path in files:
                # Auto-detect RKM/TRU files by filename
                file_type = detect_file_type(os.path.basename(file_path))
                ext = os.path.splitext(file_path)[1].lower()
                
                if file_type in ('tpy', 'rkm') and ext in ('.xls', '.xlsx'):
                    # This is a TRU/RKM file - route to TRU/RKM list
                    exists = any(
                        existing.lower() == file_path.lower()
                        for existing in self.tru_rkm_files
                    )
                    if not exists:
                        self.tru_rkm_files.append(file_path)
                        tru_rkm_added.append(os.path.basename(file_path))
                else:
                    # Regular BOM file
                    exists = any(
                        existing.lower() == file_path.lower()
                        for existing in self.input_files
                    )
                    if not exists:
                        self.input_files[file_path] = 1
                        self.last_input_file = file_path
                        bom_added.append(os.path.basename(file_path))

            # Update both lists
            self.update_listbox()
            self.update_tru_rkm_listbox()
            self.update_output_filename()
            
            # Log what was auto-categorized
            if tru_rkm_added and hasattr(self, 'log_text') and self.log_text:
                self.log_text.append(f"📋 Авто-категоризация: {len(tru_rkm_added)} файлов → ТРУ/РКМ")
                for name in tru_rkm_added:
                    self.log_text.append(f"   • {name}")


    def on_clear_files(self: 'BOMCategorizerMainWindow'):
        """Очистка списка файлов"""
        self.input_files.clear()
        self.update_listbox()
        # Сбрасываем на имя по умолчанию (без пути)
        self.output_xlsx = "categorized.xlsx"
        self.output_entry.setText(self.output_xlsx)
        # Сбрасываем количество экземпляров в 1
        if hasattr(self, 'multiplier_spin'):
            self.multiplier_spin.setValue(1)

    def on_file_selected(self: 'BOMCategorizerMainWindow'):
        """Обработка выбора файла из списка"""
        items = self.files_list.selectedItems()
        if items:
            item = items[0]
            text = item.text()
            # Извлекаем путь к файлу из текста (формат: "путь (x количество)")
            file_path = text.split(" (x")[0]
            if file_path in self.input_files:
                self.multiplier_spin.setValue(self.input_files[file_path])

    def on_multiplier_changed(self: 'BOMCategorizerMainWindow'):
        """Применение множителя к выбранному файлу"""
        items = self.files_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Предупреждение", "Выберите файл из списка")
            return

        item = items[0]
        text = item.text()
        file_path = text.split(" (x")[0]

        if file_path in self.input_files:
            new_val = self.multiplier_spin.value()
            
            if new_val == 0:
                # Удаляем файл если количество 0
                del self.input_files[file_path]
                self.update_listbox()
                
                # Если список пуст - сбрасываем выходной файл
                if not self.input_files:
                    self.output_xlsx = "categorized.xlsx"
                    self.output_entry.setText(self.output_xlsx)
                else:
                    # Обновляем имя выходного файла (если удалили первый)
                    self.update_output_filename()
            else:
                # Обновляем количество
                self.input_files[file_path] = new_val
                self.update_listbox()
                
                # Восстанавливаем выделение
                for i in range(self.files_list.count()):
                    list_item = self.files_list.item(i)
                    if list_item.text().startswith(f"{file_path} (x"):
                        self.files_list.setCurrentItem(list_item)
                        break

    def on_add_tru_rkm_files(self: 'BOMCategorizerMainWindow'):
        """Добавление файлов ТРУ и РКМ (.xls и .xlsx)"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы ТРУ и РКМ",
            "",
            "Файлы Excel (*.xls *.xlsx);;Файлы Excel 97-2003 (*.xls);;Все файлы (*)"
        )

        if files:
            warned_about_tpy = False
            for file_path in files:
                # Проверяем расширение
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in ['.xls', '.xlsx']:
                    QMessageBox.warning(
                        self,
                        "Неверный формат",
                        f"Файл {os.path.basename(file_path)} не является Excel файлом.\nДобавляются только .xls и .xlsx файлы."
                    )
                    continue
                
                # Проверяем наличие файла (без учета регистра)
                exists = False
                for existing_path in self.tru_rkm_files:
                    if existing_path.lower() == file_path.lower():
                        exists = True
                        break
                
                if not exists:
                    self.tru_rkm_files.append(file_path)
                    # Подсказка: для режима BOM+ТРУ нужны обработанные *_tpy.xlsx
                    if not warned_about_tpy:
                        bn = os.path.basename(file_path).lower()
                        if ext == '.xls' or (ext == '.xlsx' and not bn.endswith('_tpy.xlsx')):
                            warned_about_tpy = True
                            QMessageBox.information(
                                self,
                                "Подсказка по ТРУ файлам",
                                "Для режима объединения BOM + ТРУ рекомендуется использовать только ТРУ файлы,\n"
                                "уже обработанные приложением: *_tpy.xlsx.\n\n"
                                "Исходные .xls можно добавлять для режима обработки ТРУ/РКМ, чтобы получить *_tpy.xlsx."
                            )

            self.update_tru_rkm_listbox()
            self.update_output_filename()  # Обновляем имя выходного файла

    def on_clear_tru_rkm_files(self: 'BOMCategorizerMainWindow'):
        """Очистка списка файлов ТРУ и РКМ"""
        self.tru_rkm_files.clear()
        self.update_tru_rkm_listbox()
        # Обновляем имя выходного файла или сбрасываем если нет BOM файлов
        if self.input_files:
            self.update_output_filename()
        else:
            self.output_xlsx = "categorized.xlsx"
            self.output_entry.setText(self.output_xlsx)

    def update_tru_rkm_listbox(self: 'BOMCategorizerMainWindow'):
        """Обновление списка ТРУ/РКМ файлов"""
        self.tru_rkm_files_list.clear()
        for file_path in self.tru_rkm_files:
            item = QListWidgetItem(file_path)
            item.setData(Qt.UserRole, file_path)  # Сохраняем полный путь
            self.tru_rkm_files_list.addItem(item)

    def update_listbox(self: 'BOMCategorizerMainWindow'):
        """Обновление списка файлов"""
        self.files_list.clear()
        for file_path, count in self.input_files.items():
            filename = os.path.basename(file_path)
            self.files_list.addItem(f"{file_path} (x{count})")

    def update_output_filename(self: 'BOMCategorizerMainWindow'):
        """Автоматическое обновление имени выходного файла"""
        # Проверяем, не изменил ли пользователь имя файла вручную
        # Если текущее значение отличается от последнего автоматически установленного - не перезаписываем
        current_value = self.output_entry.text().strip() if hasattr(self, 'output_entry') else ""
        if current_value and current_value != self.output_xlsx:
            # Пользователь изменил имя вручную - не перезаписываем
            return
        
        # Определяем какие файлы присутствуют
        has_bom_files = bool(self.input_files)
        has_tru_rkm_files = bool(self.tru_rkm_files)
        
        # Если нет никаких файлов - ничего не делаем
        if not has_bom_files and not has_tru_rkm_files:
            return
        
        # Определяем папку для выходного файла
        if has_bom_files:
            # Если есть BOM файлы - используем папку первого BOM файла
            first_file_path = list(self.input_files.keys())[0]
            folder_path = os.path.dirname(first_file_path)
        elif has_tru_rkm_files:
            # Если есть только ТРУ/РКМ файлы - используем папку первого ТРУ/РКМ файла
            first_file_path = self.tru_rkm_files[0]
            folder_path = os.path.dirname(first_file_path)
        else:
            return
        
        # Нормализуем путь для текущей ОС (Windows: \ , macOS/Linux: /)
        folder_path = os.path.normpath(folder_path)
        
        # Определяем имя выходного файла в зависимости от типа файлов
        if has_tru_rkm_files and not has_bom_files:
            # Только ТРУ/РКМ файлы
            if len(self.tru_rkm_files) == 1:
                base_name = os.path.splitext(os.path.basename(self.tru_rkm_files[0]))[0]
                output_name = f"{base_name}_tru_rkm.xlsx"
            else:
                output_name = "tru_rkm.xlsx"
        elif has_bom_files and not has_tru_rkm_files:
            # Только BOM файлы (как раньше)
            if len(self.input_files) == 1:
                base_name = os.path.splitext(os.path.basename(first_file_path))[0]
                output_name = f"{base_name}_categorized.xlsx"
            else:
                output_name = "categorized.xlsx"
        else:
            # Есть и BOM и ТРУ/РКМ файлы - смешанный режим
            output_name = "categorized_combined.xlsx"
        
        # Полный путь к выходному файлу
        output_path = os.path.join(folder_path, output_name)
        
        # Проверяем существование файла и добавляем _1, _2, и т.д.
        if os.path.exists(output_path):
            base_name = os.path.splitext(output_name)[0]
            ext = os.path.splitext(output_name)[1]
            counter = 1
            while True:
                new_output_path = os.path.join(folder_path, f"{base_name}_{counter}{ext}")
                if not os.path.exists(new_output_path):
                    output_path = new_output_path
                    break
                counter += 1
        
        # Нормализуем финальный путь для текущей ОС
        self.output_xlsx = os.path.normpath(output_path)
        self.output_entry.setText(self.output_xlsx)

    def on_pick_output(self: 'BOMCategorizerMainWindow'):
        """Выбор выходного файла"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат как",
            self.output_entry.text(),
            "Excel Files (*.xlsx)"
        )

        if file_path:
            # Нормализуем путь для текущей ОС
            self.output_entry.setText(os.path.normpath(file_path))

    def on_pick_txt_dir(self: 'BOMCategorizerMainWindow'):
        """Выбор папки для TXT"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для TXT файлов"
        )

        if dir_path:
            self.txt_entry.setText(dir_path)

    def on_select_compare_file1(self: 'BOMCategorizerMainWindow'):
        """Выбор первого файла для сравнения"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите первый файл (базовый)",
            "",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.compare_entry1.setText(file_path)

    def on_select_compare_file2(self: 'BOMCategorizerMainWindow'):
        """Выбор второго файла для сравнения"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите второй файл (новый)",
            "",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.compare_entry2.setText(file_path)

    def on_select_compare_output(self: 'BOMCategorizerMainWindow'):
        """Выбор файла результата сравнения"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат сравнения как",
            self.compare_output_entry.text(),
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.compare_output_entry.setText(file_path)
