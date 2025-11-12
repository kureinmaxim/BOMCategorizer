# -*- coding: utf-8 -*-
"""
Модуль улучшенного Drag & Drop для GUI

Поддерживает:
- Перетаскивание файлов из проводника
- Перетаскивание между списками
- Изменение порядка файлов
- Визуальные индикаторы
"""

import os
import platform
import subprocess
from typing import Optional, List
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QApplication, QMenu
from PySide6.QtCore import Qt, QMimeData, QPoint, Signal
from PySide6.QtGui import QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent, QPalette, QAction


class DragDropListWidget(QListWidget):
    """Улучшенный QListWidget с поддержкой Drag & Drop"""
    
    # Сигналы
    files_dropped = Signal(list)  # Список файлов из проводника
    items_reordered = Signal()  # Порядок изменен
    items_moved_to = Signal(str, list)  # (target_list_id, items)
    
    def __init__(self, list_id: str = "", parent=None):
        super().__init__(parent)
        self.list_id = list_id
        self.drag_start_position = QPoint()
        
        # Настройки Drag & Drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        
        # Визуальные эффекты
        self._setup_visual_effects()
    
    def _setup_visual_effects(self):
        """Настраивает визуальные эффекты для D&D"""
        self.setStyleSheet("""
            QListWidget {
                border: 2px solid #45475a;
                border-radius: 5px;
                background-color: #1e1e2e;
            }
            QListWidget:focus {
                border-color: #89b4fa;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #cdd6f4;
            }
            QListWidget::item:hover {
                background-color: #313244;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обработка входа перетаскиваемого объекта"""
        mime_data = event.mimeData()
        
        # Файлы из проводника
        if mime_data.hasUrls():
            # Проверяем расширения файлов
            urls = mime_data.urls()
            supported_extensions = ['.xlsx', '.docx', '.doc', '.txt']
            has_supported = any(
                url.toLocalFile().lower().endswith(tuple(supported_extensions))
                for url in urls if url.isLocalFile()
            )
            
            if has_supported:
                event.acceptProposedAction()
                self._highlight_drop_zone(True)
                return
        
        # Элементы из другого списка или этого же
        if mime_data.hasFormat('application/x-qabstractitemmodeldatalist'):
            event.acceptProposedAction()
            self._highlight_drop_zone(True)
            return
        
        event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """Обработка движения при перетаскивании"""
        event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Обработка выхода перетаскиваемого объекта"""
        self._highlight_drop_zone(False)
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """Обработка сброса объекта"""
        self._highlight_drop_zone(False)
        mime_data = event.mimeData()
        
        # Файлы из проводника
        if mime_data.hasUrls():
            urls = mime_data.urls()
            supported_extensions = ['.xlsx', '.docx', '.doc', '.txt']
            
            files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if any(file_path.lower().endswith(ext) for ext in supported_extensions):
                        files.append(file_path)
            
            if files:
                self.files_dropped.emit(files)
                event.acceptProposedAction()
                return
        
        # Элементы из списков (внутреннее перетаскивание или между списками)
        if mime_data.hasFormat('application/x-qabstractitemmodeldatalist'):
            source = event.source()
            
            if source == self:
                # Перетаскивание внутри одного списка - изменение порядка
                super().dropEvent(event)
                self.items_reordered.emit()
            else:
                # Перетаскивание между разными списками
                if isinstance(source, DragDropListWidget):
                    selected_items = source.selectedItems()
                    items_data = []
                    
                    for item in selected_items:
                        items_data.append({
                            'text': item.text(),
                            'data': item.data(Qt.UserRole)
                        })
                    
                    if items_data:
                        # Добавляем элементы в этот список
                        for item_data in items_data:
                            new_item = QListWidgetItem(item_data['text'])
                            new_item.setData(Qt.UserRole, item_data['data'])
                            self.addItem(new_item)
                        
                        # Удаляем из исходного списка
                        for item in selected_items:
                            row = source.row(item)
                            source.takeItem(row)
                        
                        self.items_moved_to.emit(self.list_id, items_data)
                        event.acceptProposedAction()
            return
        
        event.ignore()
    
    def _highlight_drop_zone(self, highlight: bool):
        """Подсвечивает зону сброса"""
        if highlight:
            self.setStyleSheet("""
                QListWidget {
                    border: 3px dashed #89b4fa;
                    border-radius: 5px;
                    background-color: rgba(137, 180, 250, 0.1);
                }
                QListWidget::item {
                    padding: 5px;
                    border-radius: 3px;
                }
                QListWidget::item:selected {
                    background-color: #45475a;
                    color: #cdd6f4;
                }
                QListWidget::item:hover {
                    background-color: #313244;
                }
            """)
        else:
            self._setup_visual_effects()
    
    def mousePressEvent(self, event):
        """Обработка нажатия мыши"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Обработка движения мыши для начала перетаскивания"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # Начинаем перетаскивание
        selected_items = self.selectedItems()
        if not selected_items:
            return
        
        # Создаем MIME данные
        mime_data = QMimeData()
        
        # Используем стандартный формат Qt для элементов списка
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Устанавливаем курсор
        drag.setDragCursor(Qt.CursorShape.DragMoveCursor.bitmap(), Qt.MoveAction)
        
        # Выполняем перетаскивание
        result = drag.exec(Qt.MoveAction | Qt.CopyAction)
        
        super().mouseMoveEvent(event)
    
    def contextMenuEvent(self, event):
        """Контекстное меню (ПКМ)"""
        item = self.itemAt(event.pos())
        if not item:
            return
        
        menu = QMenu(self)
        
        # Открыть файл
        open_action = QAction("📄 Открыть файл", self)
        open_action.triggered.connect(lambda: self._open_file(item))
        menu.addAction(open_action)
        
        # Открыть папку
        folder_action = QAction("📁 Показать в проводнике", self)
        folder_action.triggered.connect(lambda: self._open_folder(item))
        menu.addAction(folder_action)
        
        menu.addSeparator()
        
        # Копировать путь
        copy_path_action = QAction("📋 Копировать путь", self)
        copy_path_action.triggered.connect(lambda: self._copy_path(item))
        menu.addAction(copy_path_action)
        
        menu.addSeparator()
        
        # Удалить
        delete_action = QAction("🗑️ Удалить из списка", self)
        delete_action.triggered.connect(lambda: self._delete_item(item))
        menu.addAction(delete_action)
        
        menu.exec(event.globalPos())
    
    def _open_file(self, item: QListWidgetItem):
        """Открывает файл в системном приложении"""
        file_path = self._get_file_path(item)
        if file_path and os.path.exists(file_path):
            try:
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', file_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', file_path])
            except Exception as e:
                print(f"Ошибка открытия файла: {e}")
    
    def _open_folder(self, item: QListWidgetItem):
        """Открывает папку с файлом в проводнике"""
        file_path = self._get_file_path(item)
        if file_path and os.path.exists(file_path):
            try:
                if platform.system() == 'Windows':
                    subprocess.Popen(f'explorer /select,"{file_path}"')
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', '-R', file_path])
                else:  # Linux
                    folder = os.path.dirname(file_path)
                    subprocess.Popen(['xdg-open', folder])
            except Exception as e:
                print(f"Ошибка открытия папки: {e}")
    
    def _copy_path(self, item: QListWidgetItem):
        """Копирует путь к файлу в буфер обмена"""
        file_path = self._get_file_path(item)
        if file_path:
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
    
    def _delete_item(self, item: QListWidgetItem):
        """Удаляет элемент из списка"""
        row = self.row(item)
        self.takeItem(row)
        self.items_reordered.emit()  # Уведомляем об изменении
    
    def _get_file_path(self, item: QListWidgetItem) -> Optional[str]:
        """Извлекает путь к файлу из элемента списка"""
        # Путь может быть в тексте или в UserRole
        user_data = item.data(Qt.UserRole)
        if user_data:
            return user_data
        
        # Извлекаем из текста (формат: "путь (x количество)")
        text = item.text()
        if " (x" in text:
            return text.split(" (x")[0]
        return text


class FileListManager:
    """Менеджер для управления списками файлов с D&D"""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.lists = {}  # {list_id: widget}
    
    def register_list(self, list_id: str, widget: DragDropListWidget):
        """Регистрирует список для управления"""
        self.lists[list_id] = widget
        
        # Подключаем сигналы
        widget.files_dropped.connect(lambda files: self.on_files_dropped(list_id, files))
        widget.items_reordered.connect(lambda: self.on_items_reordered(list_id))
        widget.items_moved_to.connect(self.on_items_moved)
    
    def on_files_dropped(self, list_id: str, files: List[str]):
        """Обработка сброса файлов из проводника"""
        if list_id == "input_files":
            # Добавляем в входные файлы
            for file_path in files:
                if file_path not in self.parent_window.input_files:
                    self.parent_window.input_files[file_path] = 1
            self.parent_window.update_listbox()
            self.parent_window.update_output_filename()
            
        elif list_id in ["compare_file1", "compare_file2"]:
            # Для файлов сравнения берем только первый файл
            if files:
                if list_id == "compare_file1":
                    self.parent_window.compare_entry1.setText(files[0])
                else:
                    self.parent_window.compare_entry2.setText(files[0])
    
    def on_items_reordered(self, list_id: str):
        """Обработка изменения порядка элементов"""
        if list_id == "input_files":
            # Обновляем порядок файлов в словаре
            widget = self.lists[list_id]
            new_order = {}
            
            for i in range(widget.count()):
                item = widget.item(i)
                text = item.text()
                # Извлекаем путь к файлу из текста
                file_path = text.split(" (x")[0]
                if file_path in self.parent_window.input_files:
                    new_order[file_path] = self.parent_window.input_files[file_path]
            
            self.parent_window.input_files = new_order
    
    def on_items_moved(self, target_list_id: str, items_data: List[dict]):
        """Обработка перемещения элементов между списками"""
        # Можно добавить дополнительную логику при необходимости
        pass


def enable_drag_drop_improvements(window):
    """
    Активирует улучшенный Drag & Drop для окна
    
    Args:
        window: Главное окно приложения
    """
    # Заменяем стандартный QListWidget на DragDropListWidget
    if hasattr(window, 'files_list'):
        # Сохраняем текущие элементы
        old_list = window.files_list
        items = []
        for i in range(old_list.count()):
            item = old_list.item(i)
            items.append(item.text())
        
        # Создаем новый список с D&D
        parent = old_list.parent()
        layout = parent.layout()
        
        new_list = DragDropListWidget("input_files", window)
        new_list.setMaximumHeight(old_list.maximumHeight())
        
        # Восстанавливаем элементы
        for item_text in items:
            new_list.addItem(item_text)
        
        # Подключаем обработчики
        new_list.itemSelectionChanged.connect(window.on_file_selected)
        
        # Заменяем в layout
        index = layout.indexOf(old_list)
        layout.removeWidget(old_list)
        old_list.deleteLater()
        layout.insertWidget(index, new_list)
        
        window.files_list = new_list
        
        # Создаем менеджер и регистрируем список
        if not hasattr(window, 'file_list_manager'):
            window.file_list_manager = FileListManager(window)
        window.file_list_manager.register_list("input_files", new_list)
    
    return True

