# -*- coding: utf-8 -*-
"""
Database handlers module for BOMCategorizer GUI.

This module contains mixin methods for database operations in the main window.
Following Lego Principle: single responsibility per module.
"""

import os
import sys
import platform
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QFileDialog, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..component_database import (
    get_database_path,
    get_database_stats,
    get_database_history,
    export_database_to_excel,
    import_database_from_excel,
    backup_database as db_backup,
    clear_database,
    set_database_version,
)
from ..shared.fonts import get_system_font

if TYPE_CHECKING:
    from .main_window import BOMCategorizerMainWindow


class DatabaseHandlersMixin:
    """Mixin class containing database operation methods for main window."""

    def on_show_db_stats(self: 'BOMCategorizerMainWindow'):
        """Показывает статистику базы данных"""
        self.show_database_stats()

    def show_database_stats(self: 'BOMCategorizerMainWindow'):
        """Показывает статистику базы данных"""
        try:
            stats = get_database_stats()
            db_path = get_database_path()
            
            # Формируем текст статистики
            metadata = stats.get("metadata", {})
            by_category = stats.get("by_category", {})
            category_names = stats.get("category_names", {})
            
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
            if by_category:
                for cat_id, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                    cat_name = category_names.get(cat_id, cat_id)
                    stats_text += f"• {cat_name}: {count}\n"
            else:
                stats_text += "• Нет данных\n"
            
            # Создаем диалог
            dialog = QDialog(self)
            dialog.setWindowTitle("Статистика базы данных")
            dialog.resize(650, 550)
            
            layout = QVBoxLayout()
            
            # Текстовое поле с прокруткой
            text_widget = QTextEdit()
            text_widget.setReadOnly(True)
            text_widget.setPlainText(stats_text)
            # Крупный фиксированный шрифт для читаемости
            stats_font = QFont("Menlo" if sys.platform == "darwin" else "Consolas" if sys.platform == "win32" else "Monospace")
            stats_font.setPointSize(14)
            text_widget.setFont(stats_font)
            layout.addWidget(text_widget)
            
            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            button_font = QFont()
            button_font.setPointSize(12)
            close_btn.setFont(button_font)
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось показать статистику базы данных:\n{str(e)}"
            )

    def on_clear_database(self: 'BOMCategorizerMainWindow'):
        """Очищает базу данных компонентов"""
        # Получаем текущую статистику
        stats = get_database_stats()
        total = stats.get('total', 0)
        
        # Подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение очистки",
            f"⚠️ Вы уверены, что хотите очистить базу данных?\n\n"
            f"Текущее количество компонентов: {total}\n\n"
            f"❗ Это действие создаст резервную копию старой базы,\n"
            f"но все компоненты будут удалены из основной базы.\n\n"
            f"Продолжить?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Очищаем базу данных
                success = clear_database()
                
                if success:
                    # Обновляем информацию в футере
                    self.update_database_info()
                    
                    self.log_text.append("\n✅ База данных успешно очищена!")
                    self.log_text.append("   Резервная копия сохранена в папке backups\n")
                    
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"✅ База данных успешно очищена!\n\n"
                        f"Удалено компонентов: {total}\n\n"
                        f"Резервная копия старой базы сохранена в папке:\n"
                        f"{os.path.join(os.path.dirname(get_database_path()), 'backups')}\n\n"
                        f"Информация в футере обновлена!"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        "❌ Не удалось очистить базу данных.\nПодробности в логе."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось очистить базу данных:\n{str(e)}"
                )

    def on_change_database_version(self: 'BOMCategorizerMainWindow'):
        """Диалог для ручного изменения версии БД"""
        from PySide6.QtWidgets import QInputDialog, QLineEdit
        
        # Получаем текущую версию
        stats = get_database_stats()
        current_version = stats.get('metadata', {}).get('version', '1.0')
        
        # Показываем диалог ввода
        text, ok = QInputDialog.getText(
            self,
            "Изменить версию БД",
            f"Текущая версия: {current_version}\n\n"
            f"Введите новую версию в формате X.Y:\n"
            f"(X увеличивается при импорте из файлов,\n"
            f"Y увеличивается при ручном добавлении элементов)\n"
            f"Версия 0.0 означает пустую базу после очистки.",
            QLineEdit.Normal,
            current_version
        )
        
        if ok and text:
            # Проверяем формат
            if '.' not in text:
                QMessageBox.warning(
                    self,
                    "Неверный формат",
                    "Версия должна быть в формате X.Y (например, 2.5)"
                )
                return
            
            try:
                parts = text.split('.')
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
                
                if major < 0 or minor < 0:
                    QMessageBox.warning(
                        self,
                        "Неверное значение",
                        "Версия должна быть >= 0.0"
                    )
                    return
                
                # Устанавливаем новую версию
                success = set_database_version(text)
                
                if success:
                    # Обновляем информацию в футере
                    self.update_database_info()
                    
                    self.log_text.append(f"\n✅ Версия БД изменена: {current_version} → {text}\n")
                    
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"✅ Версия БД успешно изменена!\n\n"
                        f"Старая версия: {current_version}\n"
                        f"Новая версия: {text}\n\n"
                        f"Запись добавлена в историю БД.\n"
                        f"Информация в футере обновлена!"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        "❌ Не удалось изменить версию БД.\nПодробности в логе."
                    )
                    
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Неверный формат",
                    "Версия должна содержать числа (например, 2.5)"
                )

    def export_database(self: 'BOMCategorizerMainWindow'):
        """Экспорт базы данных в Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт базы данных",
            "component_database.xlsx",
            "Excel файлы (*.xlsx)"
        )

        if file_path:
            try:
                row_count = export_database_to_excel(file_path)
                QMessageBox.information(
                    self,
                    "Экспорт завершен",
                    f"✅ База данных успешно экспортирована!\n\n"
                    f"Файл: {file_path}\n"
                    f"Компонентов: {row_count}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка экспорта",
                    f"Не удалось экспортировать базу данных:\n{str(e)}"
                )

    def import_database(self: 'BOMCategorizerMainWindow'):
        """Импорт базы данных из Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт базы данных",
            "",
            "Поддерживаемые файлы (*.xlsx *.json);;Excel файлы (*.xlsx);;JSON файлы (*.json)"
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    import shutil
                    db_path = get_database_path()
                    # Создаем резервную копию
                    db_backup()
                    # Копируем новый файл
                    shutil.copy2(file_path, db_path)
                    stats = get_database_stats()
                    imported_count = stats.get('total', 0)
                elif file_path.endswith('.xlsx'):
                    # Создаем резервную копию
                    db_backup()
                    # Импортируем из Excel
                    imported_count = import_database_from_excel(file_path, replace=True)
                else:
                    QMessageBox.warning(
                        self,
                        "Неподдерживаемый формат",
                        "Поддерживаются только файлы .xlsx и .json"
                    )
                    return

                # Обновляем футер после импорта
                self.update_database_info()
                
                QMessageBox.information(
                    self,
                    "Импорт завершен",
                    f"✅ База данных успешно импортирована!\n\n"
                    f"Компонентов импортировано: {imported_count}\n"
                    f"База данных: {get_database_path()}\n\n"
                    f"Информация в футере обновлена!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка импорта",
                    f"Не удалось импортировать базу данных:\n{str(e)}"
                )

    def backup_database(self: 'BOMCategorizerMainWindow'):
        """Создает резервную копию базы данных"""
        try:
            backup_file = db_backup()
            QMessageBox.information(
                self,
                "Резервное копирование",
                f"✅ Резервная копия создана успешно!\n\n"
                f"Файл: {backup_file}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось создать резервную копию:\n{str(e)}"
            )

    def open_database_folder(self: 'BOMCategorizerMainWindow'):
        """Открывает папку с базой данных в проводнике с выделенным файлом"""
        try:
            db_path = get_database_path()
            if not self.reveal_in_file_manager(db_path, select=True):
                raise RuntimeError("Не удалось открыть проводник.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть папку:\n{str(e)}")

    def on_view_database(self: 'BOMCategorizerMainWindow'):
        """Открывает диалог для просмотра содержимого базы данных"""
        import json
        
        try:
            db_path = get_database_path()
            
            if not os.path.exists(db_path):
                QMessageBox.warning(
                    self,
                    "База данных не найдена",
                    f"Файл базы данных не существует:\n{db_path}"
                )
                return
            
            # Загружаем данные из JSON
            with open(db_path, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
            
            components = db_data.get('components', {})
            metadata = db_data.get('metadata', {})
            
            # Создаем диалог
            dialog = QDialog(self)
            dialog.setWindowTitle("Просмотр базы данных")
            dialog.resize(900, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Информация о БД
            info_label = QLabel(
                f"📦 Версия: {metadata.get('version', 'N/A')} | "
                f"📊 Компонентов: {sum(len(v) for v in components.values())} | "
                f"📁 Путь: {db_path}"
            )
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Таблица с компонентами
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Наименование", "Категория", "Ключевые слова", "Источник"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            
            # Получаем имена категорий
            from ..component_database import CATEGORY_NAMES
            
            # Заполняем таблицу
            all_rows = []
            for category_id, items in components.items():
                category_name = CATEGORY_NAMES.get(category_id, category_id)
                for item in items:
                    if isinstance(item, dict):
                        name = item.get('name', str(item))
                        keywords = ', '.join(item.get('keywords', [])) if item.get('keywords') else ''
                        source = item.get('source', '')
                    else:
                        name = str(item)
                        keywords = ''
                        source = ''
                    all_rows.append((name, category_name, keywords, source))
            
            table.setRowCount(len(all_rows))
            for row_idx, (name, cat, kw, src) in enumerate(all_rows):
                table.setItem(row_idx, 0, QTableWidgetItem(name))
                table.setItem(row_idx, 1, QTableWidgetItem(cat))
                table.setItem(row_idx, 2, QTableWidgetItem(kw))
                table.setItem(row_idx, 3, QTableWidgetItem(src))
            
            layout.addWidget(table)
            
            # Кнопки
            buttons_layout = QHBoxLayout()
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось открыть базу данных:\n{str(e)}"
            )
