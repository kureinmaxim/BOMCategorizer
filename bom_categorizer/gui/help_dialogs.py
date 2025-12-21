# -*- coding: utf-8 -*-
"""
Help dialogs module for BOMCategorizer GUI.

This module contains mixin methods for help and about dialogs in the main window.
Following Lego Principle: single responsibility per module.
"""

import os
import re
import sys
import platform
import subprocess
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QTextBrowser,
    QPushButton, QMessageBox, QLineEdit, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor

from ..component_database import get_database_path, get_database_stats
from ..shared.fonts import get_system_font

if TYPE_CHECKING:
    from .main_window import BOMCategorizerMainWindow


class HelpDialogsMixin:
    """Mixin class containing help and about dialog methods for main window."""

    def show_about(self: 'BOMCategorizerMainWindow'):
        """Показывает информацию о программе"""
        ver = self.cfg.get("app_info", {}).get("version", "dev")
        edition = self.cfg.get("app_info", {}).get("edition", "Modern Edition")
        
        about_text = f"""
<h2>BOM Categorizer {edition}</h2>
<p><b>Версия:</b> {ver}</p>
<p><b>Разработчик:</b> Куреин М.Н. / Kurein M.N.</p>
<p><b>Дата выпуска:</b> {self.cfg.get('app_info', {}).get('release_date', 'N/A')}</p>

<p><b>Возможности:</b></p>
<ul>
<li>📋 Обработка файлов: XLSX, DOCX, TXT</li>
<li>🤖 Автоматическая классификация компонентов</li>
<li>🎨 Форматирование и сортировка</li>
<li>🗄️ База данных компонентов с версионированием</li>
<li>🖥️ Современный темный/светлый интерфейс</li>
<li>🔒 PIN защита</li>
<li>💾 Экспорт в Excel и TXT</li>
<li>📊 Сравнение BOM файлов</li>
<li>🔍 Контекстная помощь (F1)</li>
</ul>

<p><b>Горячие клавиши:</b></p>
<ul>
<li><b>Ctrl+O</b> - Открыть файлы</li>
<li><b>Ctrl+R</b> - Запустить обработку</li>
<li><b>Ctrl+Q</b> - Выход</li>
<li><b>F1</b> - Контекстная помощь</li>
<li><b>Ctrl+T</b> - Переключить тему</li>
<li><b>Ctrl+Plus/Minus</b> - Изменить масштаб</li>
</ul>

<p><b>Лицензия:</b></p>
<p style="font-size: 10pt;">
Copyright © 2025 Куреин М.Н. / Kurein M.N.<br><br>
Все права защищены.
</p>

<p style="color: #7287fd;"><b>Modern Edition</b> на основе PySide6 (Qt)</p>
        """

        # Создаем кастомный диалог
        dialog = QDialog(self)
        dialog.setWindowTitle("О программе")
        dialog.resize(600, 650)
        
        layout = QVBoxLayout()
        
        text_widget = QTextBrowser()
        text_widget.setOpenExternalLinks(True)
        text_widget.setHtml(about_text)
        layout.addWidget(text_widget)
        
        # GitHub ссылка
        github_layout = QHBoxLayout()
        github_label = QLabel('<a href="https://github.com/kureinmaxim/BOMCategorizer" style="color: #0066cc; font-weight: bold; font-size: 14px; text-decoration: underline;">🔗 GitHub репозиторий</a>')
        github_label.setOpenExternalLinks(True)
        github_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        github_layout.addStretch()
        github_layout.addWidget(github_label)
        github_layout.addStretch()
        layout.addLayout(github_layout)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

    def show_context_help(self: 'BOMCategorizerMainWindow'):
        """Показывает контекстную помощь для текущего элемента"""
        cursor_pos = QCursor.pos()
        widget_under_cursor = QApplication.widgetAt(cursor_pos)
        
        if widget_under_cursor is None:
            widget_under_cursor = self.focusWidget()
        
        if widget_under_cursor is None:
            widget_under_cursor = self
        
        help_text = self._get_context_help(widget_under_cursor)
        
        if help_text:
            QMessageBox.information(self, "Контекстная помощь", help_text)
        else:
            QMessageBox.information(
                self,
                "Контекстная помощь",
                "📖 <b>Контекстная помощь</b><br><br>"
                "Наведите курсор на элемент интерфейса и нажмите <b>F1</b> для получения справки."
            )
    
    def _get_context_help(self: 'BOMCategorizerMainWindow', widget) -> str:
        """Возвращает текст помощи для конкретного виджета"""
        if widget is None:
            return ""
        
        widget_type = type(widget).__name__
        widget_text = ""
        
        if hasattr(widget, 'text'):
            widget_text = widget.text()
        elif hasattr(widget, 'toolTip'):
            widget_text = widget.toolTip()
        
        # Упрощенная карта помощи
        help_map = {
            'QPushButton': {
                'Добавить файлы': '📂 <b>Добавить файлы</b><br>Добавляет BOM файлы для обработки.',
                'Очистить список': '🗑️ <b>Очистить список</b><br>Удаляет все файлы из списка.',
                'Запустить обработку': '🚀 <b>Запустить обработку</b><br>Начинает обработку BOM файлов.',
            },
            'QListWidget': {
                '': '📋 <b>Список файлов</b><br>Список выбранных файлов для обработки.',
            },
            'QTextEdit': {
                '': '📝 <b>Лог выполнения</b><br>Отображает информацию о процессе обработки.',
            },
        }
        
        # Ищем подходящую справку
        if widget_type in help_map:
            for key, value in help_map[widget_type].items():
                if key and key.lower() in widget_text.lower():
                    return value
            if '' in help_map[widget_type]:
                return help_map[widget_type]['']
        
        return ""

    def show_system_info(self: 'BOMCategorizerMainWindow'):
        """Показывает системную информацию для диагностики"""
        system_info = f"""
<h2>💻 Системная информация</h2>

<h3>Операционная система:</h3>
<p><b>Платформа:</b> {platform.system()} {platform.release()}</p>
<p><b>Архитектура:</b> {platform.machine()}</p>

<h3>Python:</h3>
<p><b>Версия:</b> {sys.version.split()[0]}</p>

<h3>Приложение:</h3>
<p><b>Версия:</b> {self.cfg.get('app_info', {}).get('version', 'N/A')}</p>
<p><b>Редакция:</b> {self.cfg.get('app_info', {}).get('edition', 'N/A')}</p>
<p><b>Тема:</b> {self.current_theme}</p>
<p><b>Масштаб:</b> {int(self.scale_factor * 100)}%</p>
"""
        try:
            stats = get_database_stats()
            metadata = stats.get('metadata', {})
            system_info += f"""
<h3>База данных:</h3>
<p><b>Версия БД:</b> {metadata.get('version', 'N/A')}</p>
<p><b>Компонентов:</b> {stats.get('total', 0)}</p>
"""
        except:
            pass
        
        dialog = QDialog(self)
        dialog.setWindowTitle("💻 Системная информация")
        dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        
        text_widget = QTextBrowser()
        text_widget.setOpenExternalLinks(True)
        text_widget.setHtml(system_info)
        layout.addWidget(text_widget)
        
        button_layout = QHBoxLayout()
        copy_btn = QPushButton("📋 Копировать")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(system_info))
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _copy_to_clipboard(self: 'BOMCategorizerMainWindow', text: str):
        """Копирует текст в буфер обмена"""
        clipboard = QApplication.clipboard()
        plain_text = re.sub('<[^<]+?>', '', text)
        clipboard.setText(plain_text)
        self.statusBar().showMessage("✓ Информация скопирована в буфер обмена", 3000)
