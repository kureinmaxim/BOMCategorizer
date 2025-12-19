# -*- coding: utf-8 -*-
"""
Диалоговые окна для BOM Categorizer на базе PySide6
"""

import os
import sys
from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QMessageBox,
    QWidget, QListWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class PinDialog(QDialog):
    """Диалог ввода PIN-кода"""

    def __init__(self, correct_pin: str, parent=None):
        super().__init__(parent)
        self.correct_pin = correct_pin
        self.is_authenticated = False

        self.setWindowTitle("Авторизация")
        self.setFixedSize(380, 220)
        self.setModal(True)
        
        # Получаем scale_factor от родительского окна
        self.scale_factor = getattr(parent, 'scale_factor', 1.0) if parent else 1.0

        self._create_ui()

        # Центрируем окно
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)

    def _create_ui(self):
        """Создает элементы диалога"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("Введите PIN-код:")
        title_font = QFont()
        title_font.setPointSize(int(14 * self.scale_factor))
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Поле ввода PIN
        self.pin_entry = QLineEdit()
        self.pin_entry.setEchoMode(QLineEdit.Password)
        self.pin_entry.setAlignment(Qt.AlignCenter)
        pin_font = QFont()
        pin_font.setPointSize(int(18 * self.scale_factor))
        self.pin_entry.setFont(pin_font)
        self.pin_entry.setMaxLength(10)
        self.pin_entry.returnPressed.connect(self.check_pin)
        layout.addWidget(self.pin_entry)

        # Метка ошибки
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        error_font = QFont()
        error_font.setPointSize(12)
        self.error_label.setFont(error_font)
        self.error_label.setStyleSheet("color: #DE350B;")
        layout.addWidget(self.error_label)

        # Кнопки
        buttons_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.check_pin)
        ok_btn.setDefault(True)
        buttons_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Фокус на поле ввода
        self.pin_entry.setFocus()

    def check_pin(self):
        """Проверяет введенный PIN"""
        entered_pin = self.pin_entry.text().strip()

        if entered_pin == self.correct_pin:
            self.is_authenticated = True
            self.accept()
        else:
            self.error_label.setText("Неверный PIN-код")
            self.pin_entry.clear()
            self.pin_entry.setFocus()

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class DatabaseStatsDialog(QDialog):
    """Диалог статистики базы данных"""

    def __init__(self, stats: dict, parent=None):
        super().__init__(parent)
        self.stats = stats
        
        # Получаем scale_factor от родительского окна
        self.scale_factor = getattr(parent, 'scale_factor', 1.0) if parent else 1.0

        self.setWindowTitle("Статистика базы данных")
        # Масштабируем размер диалога пропорционально scale_factor
        min_width = max(600, int(650 * self.scale_factor))
        min_height = max(500, int(550 * self.scale_factor))
        self.setMinimumSize(min_width, min_height)
        self.setModal(True)

        self._create_ui()

    def _create_ui(self):
        """Создает элементы диалога"""
        layout = QVBoxLayout()

        # Текстовое поле с информацией
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Применяем моноширинный шрифт с учётом scale_factor для лучшего отображения
        font = QFont("Menlo" if sys.platform == "darwin" else "Consolas" if sys.platform == "win32" else "Monospace")
        font.setPointSize(max(10, int(12 * self.scale_factor)))
        text_edit.setFont(font)

        # Формируем текст статистики
        stats_text = self._format_stats()
        text_edit.setPlainText(stats_text)

        layout.addWidget(text_edit)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        button_font = QFont()
        button_font.setPointSize(max(10, int(12 * self.scale_factor)))
        close_btn.setFont(button_font)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _format_stats(self) -> str:
        """Форматирует статистику в текст"""
        metadata = self.stats.get('metadata', {})
        
        text = "📊 СТАТИСТИКА БАЗЫ ДАННЫХ\n"
        text += "═" * 60 + "\n\n"
        
        # Общая информация
        text += "ℹ️  Общая информация:\n"
        text += f"   • Версия БД: {metadata.get('version', 'N/A')}\n"
        text += f"   • Последнее обновление: {metadata.get('last_updated', 'N/A')}\n"
        text += f"   • Всего компонентов: {metadata.get('total_components', 0)}\n\n"

        # Разбивка по категориям
        categories = self.stats.get('by_category', {})
        if categories:
            text += "📦 Распределение по категориям:\n"
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                # Визуальный прогресс-бар
                bar_length = int((count / metadata.get('total_components', 1)) * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)
                percentage = (count / metadata.get('total_components', 1)) * 100 if metadata.get('total_components', 0) > 0 else 0
                text += f"   • {category}: {count} ({percentage:.1f}%)\n"
                text += f"     {bar}\n"
        else:
            text += "⚠️  Категории не определены\n"

        return text


class FirstRunImportDialog(QDialog):
    """Диалог импорта БД при первом запуске"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.import_selected = False

        self.setWindowTitle("База данных компонентов")
        self.setFixedSize(450, 300)
        self.setModal(True)

        self._create_ui()

    def _create_ui(self):
        """Создает элементы диалога"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("Первый запуск")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Описание
        desc_label = QLabel(
            "Обнаружен первый запуск приложения.\n\n"
            "У вас уже есть существующая база данных компонентов?\n"
            "Если да, вы можете импортировать её сейчас."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Кнопки
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)

        import_btn = QPushButton("📥 Импортировать существующую БД")
        import_btn.setMinimumHeight(32)
        import_btn.clicked.connect(self.on_import)
        buttons_layout.addWidget(import_btn)

        fresh_btn = QPushButton("✨ Начать с чистой БД")
        fresh_btn.setMinimumHeight(32)
        fresh_btn.clicked.connect(self.on_fresh_start)
        buttons_layout.addWidget(fresh_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def on_import(self):
        """Пользователь выбрал импорт"""
        self.import_selected = True
        self.accept()

    def on_fresh_start(self):
        """Пользователь выбрал начать с чистой БД"""
        self.import_selected = False
        self.accept()


class ClassificationDialog(QDialog):
    """Диалог интерактивной классификации компонентов"""

    # Категории компонентов
    # Импортируем категории из базы данных
    from ..component_database import CATEGORY_NAMES

    # Формируем список категорий для диалога с горячими клавишами
    # (key, name, emoji)
    CATEGORIES = []
    
    # Маппинг категорий на горячие клавиши
    _HOTKEYS = "1234567890abcd"
    _ORDERED_KEYS = [
        "resistors", "capacitors", "inductors", "ics", "semiconductors",
        "connectors", "cables", "dev_boards", "optics", "rf_modules",
        "power_modules", "our_developments", "others", "non_bom"
    ]
    
    for i, cat_key in enumerate(_ORDERED_KEYS):
        if cat_key in CATEGORY_NAMES and i < len(_HOTKEYS):
            hotkey = _HOTKEYS[i]
            name = CATEGORY_NAMES[cat_key]
            CATEGORIES.append((hotkey, name, cat_key))
            
    CATEGORIES.append(("s", "Пропустить", ""))

    classification_complete = Signal(dict)  # {component: category}

    def __init__(self, components: List[Tuple[str, str, str]], parent=None):
        """
        Args:
            components: Список кортежей (обозначение, наименование, параметры)
        """
        super().__init__(parent)
        self.components = components
        self.current_index = 0
        self.classifications = {}

        self.setWindowTitle("Интерактивная классификация")
        self.setMinimumSize(900, 650)
        self.setModal(True)

        self._create_ui()
        self._show_current_component()

    def _create_ui(self):
        """Создает элементы диалога"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Прогресс
        self.progress_label = QLabel()
        progress_font = QFont()
        progress_font.setPointSize(12)
        progress_font.setBold(True)
        self.progress_label.setFont(progress_font)
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        # Информация о компоненте
        component_group = QWidget()
        component_layout = QVBoxLayout(component_group)

        self.designation_label = QLabel()
        self.name_label = QLabel()
        self.params_label = QLabel()

        for label in [self.designation_label, self.name_label, self.params_label]:
            label_font = QFont()
            label_font.setPointSize(11)
            label.setFont(label_font)
            label.setWordWrap(True)
            component_layout.addWidget(label)

        layout.addWidget(component_group)

        # Кнопки категорий
        categories_group = QWidget()
        categories_layout = QGridLayout(categories_group)
        categories_layout.setSpacing(6)

        self.category_buttons = {}

        for i, (key, name, cat_key) in enumerate(self.CATEGORIES):
            row = i // 2
            col = i % 2

            btn = QPushButton(f"{name} ({key})")
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, k=key: self.classify_current(k))

            categories_layout.addWidget(btn, row, col)
            self.category_buttons[key] = btn

        layout.addWidget(categories_group)

        # Кнопка закрытия
        close_btn = QPushButton("Завершить классификацию")
        close_btn.clicked.connect(self.finish_classification)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _show_current_component(self):
        """Отображает текущий компонент"""
        if self.current_index >= len(self.components):
            self.finish_classification()
            return

        designation, name, params = self.components[self.current_index]

        self.progress_label.setText(
            f"Компонент {self.current_index + 1} из {len(self.components)}"
        )
        self.designation_label.setText(f"Обозначение: {designation}")
        self.name_label.setText(f"Наименование: {name}")
        self.params_label.setText(f"Параметры: {params}")

    def classify_current(self, hotkey: str):
        """Классифицирует текущий компонент"""
        if self.current_index >= len(self.components):
            return

        component = self.components[self.current_index]

        if hotkey == 's':  # Пропустить
            pass
        else:
            # Находим реальный ключ категории по горячей клавише
            real_category = None
            for k, _, cat in self.CATEGORIES:
                if k == hotkey:
                    real_category = cat
                    break
            
            if real_category:
                # Сохраняем классификацию по ИМЕНИ компонента (не по обозначению!)
                # component[1] = имя, component[0] = обозначение (часто пустое)
                self.classifications[component[1]] = real_category

        # Переходим к следующему компоненту
        self.current_index += 1
        self._show_current_component()

    def finish_classification(self):
        """Завершает классификацию"""
        self.classification_complete.emit(self.classifications)
        self.accept()

    def keyPressEvent(self, event):
        """Обработка горячих клавиш"""
        key = event.text().lower()

        # Проверяем, есть ли такая категория
        for cat_key, _, _ in self.CATEGORIES:
            if key == cat_key:
                self.classify_current(cat_key)
                return

        if event.key() == Qt.Key_Escape:
            self.finish_classification()
        else:
            super().keyPressEvent(event)


class DocConversionDialog(QDialog):
    """Диалог выбора способа конвертации .doc файлов"""

    def __init__(self, doc_files: List[str], parent=None):
        super().__init__(parent)
        self.doc_files = doc_files
        self.conversion_method = None  # 'word', 'manual', или None

        self.setWindowTitle("Обнаружены .doc файлы")
        self.setFixedSize(600, 360)
        self.setModal(True)

        self._create_ui()

    def _create_ui(self):
        """Создает элементы диалога"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("Обнаружены файлы в формате .doc")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Описание
        desc_label = QLabel(
            "Следующие файлы требуют конвертации в .docx:"
        )
        layout.addWidget(desc_label)

        # Список файлов
        files_list = QTextEdit()
        files_list.setReadOnly(True)
        files_list.setMaximumHeight(150)
        files_list.setPlainText("\n".join(self.doc_files))
        layout.addWidget(files_list)

        # Кнопки выбора
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)

        # Кнопка автоматической конвертации
        import platform
        if platform.system() == 'Windows':
            auto_btn = QPushButton("Конвертировать с помощью Word")
            auto_btn.setMinimumHeight(32)
            auto_btn.setToolTip("Использует Microsoft Word для конвертации")
            auto_btn.clicked.connect(self.on_word_conversion)
            buttons_layout.addWidget(auto_btn)
        else:
            # На macOS/Linux используем LibreOffice
            auto_btn = QPushButton("Конвертировать с помощью LibreOffice")
            auto_btn.setMinimumHeight(32)
            auto_btn.setToolTip(
                "Использует LibreOffice для конвертации\n"
                "(Бесплатный офисный пакет, если установлен)"
            )
            auto_btn.clicked.connect(self.on_word_conversion)  # Та же функция
            buttons_layout.addWidget(auto_btn)

        manual_btn = QPushButton("Конвертировать вручную и продолжить")
        manual_btn.setMinimumHeight(32)
        manual_btn.clicked.connect(self.on_manual_conversion)
        buttons_layout.addWidget(manual_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def on_word_conversion(self):
        """Выбрана конвертация через Word"""
        self.conversion_method = 'word'
        self.accept()

    def on_manual_conversion(self):
        """Выбрана ручная конвертация"""
        self.conversion_method = 'manual'
        self.accept()