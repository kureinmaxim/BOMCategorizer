# -*- coding: utf-8 -*-
"""
GUI для BOM Categorizer на базе PySide6

PySide6-интерфейс с поддержкой:
- Выбора входных файлов (XLSX, DOCX, TXT)
- Настройки параметров обработки
- Интерактивной классификации нераспределенных элементов
- PIN-защиты интерфейса
"""

import os
import json
import sys
import platform
from typing import Dict, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QPushButton, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QSpinBox, QCheckBox, QTextEdit,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QDialog
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QFont, QColor, QPalette

from .component_database import (
    add_component_to_database,
    get_database_path,
    get_database_stats,
    export_database_to_excel,
    import_database_from_excel,
    backup_database,
    is_first_run,
    initialize_database_from_template,
    format_history_tooltip
)

from .dialogs_qt import (
    PinDialog,
    DatabaseStatsDialog,
    FirstRunImportDialog,
    ClassificationDialog,
    DocConversionDialog
)


def load_config() -> dict:
    """Загружает конфигурацию из config_qt.json (Modern Edition)"""
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_qt.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"app_info": {"version": "4.0.0", "edition": "Modern Edition", "description": "BOM Categorizer Modern Edition"}}


def get_system_font() -> str:
    """
    Возвращает подходящий системный шрифт для текущей ОС

    Returns:
        str: Название шрифта
    """
    system = platform.system()

    if system == 'Darwin':  # macOS
        return 'SF Pro Text'
    elif system == 'Windows':
        return 'Segoe UI'
    else:  # Linux и другие
        return 'DejaVu Sans'


class BOMCategorizerMainWindow(QMainWindow):
    """Главное окно приложения BOM Categorizer на PySide6"""

    def __init__(self):
        super().__init__()

        # Загружаем конфигурацию
        self.cfg = load_config()
        ver = self.cfg.get("app_info", {}).get("version", "dev")
        name = self.cfg.get("app_info", {}).get("description", "BOM Categorizer")

        # Устанавливаем заголовок окна
        self.setWindowTitle(f"{name} v{ver}")

        # Загружаем размер окна из конфигурации
        window_cfg = self.cfg.get("window", {})
        width = window_cfg.get("width", 660)
        height = window_cfg.get("height", 1000)
        self.resize(width, height)

        # Переменные состояния
        self.input_files: Dict[str, int] = {}  # {путь_к_файлу: количество}
        self.output_xlsx = "categorized.xlsx"
        self.txt_dir = ""
        self.combine = True
        self.interactive = False
        self.create_txt = False
        self.current_file_multiplier = 1
        self.selected_file_index: Optional[int] = None

        # Сравнение файлов
        self.compare_file1 = ""
        self.compare_file2 = ""
        self.compare_output = "comparison.xlsx"

        # PIN защита
        self.unlocked = False
        self.require_pin = self.cfg.get("security", {}).get("require_pin", True)
        self.correct_pin = self.cfg.get("security", {}).get("pin", "1234")
        self.lockable_widgets = []

        # Применяем стили
        self._setup_styles()

        # Создаем UI
        self._create_ui()

        # Применяем блокировку интерфейса при необходимости
        if self.require_pin:
            self.lock_interface()

    def _setup_styles(self):
        """Настраивает стили приложения - современный лаконичный дизайн"""
        # Устанавливаем системный шрифт с увеличенным размером
        font = QFont(get_system_font(), 12)
        self.setFont(font)

        # Приглушенная цветовая палитра с хорошим контрастом текста
        # Primary: #5B9BD5 (спокойный синий), Success: #67B279 (мягкий зеленый), Danger: #D9534F (приглушенный красный)
        # Background: #F5F6F7, Surface: #FFFFFF, Border: #D0D5DD, Text: темные для контраста
        
        self.setStyleSheet("""
            /* Главное окно */
            QMainWindow {
                background-color: #F5F6F7;
            }
            
            /* Группы (секции) - единый шрифт */
            QGroupBox {
                font-size: 14pt;
                font-weight: 600;
                border: 1px solid #D0D5DD;
                border-radius: 8px;
                margin-top: 8px;
                margin-bottom: 8px;
                padding: 16px 12px 12px 12px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2C3E50;
                font-size: 14pt;
                font-weight: 600;
            }
            
            /* Кнопки - основной стиль (приглушенный синий) */
            QPushButton {
                background-color: #5B9BD5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 13pt;
                font-weight: 600;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #4A8FC7;
            }
            QPushButton:pressed {
                background-color: #3B7FB8;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #9E9E9E;
            }
            
            /* Кнопки - акцентные (приглушенный зеленый) */
            QPushButton.accent {
                background-color: #67B279;
                font-weight: 600;
            }
            QPushButton.accent:hover {
                background-color: #5AA66C;
            }
            QPushButton.accent:pressed {
                background-color: #4D995F;
            }
            
            /* Кнопки - вторичные действия (нейтральный серый) */
            QPushButton.danger {
                background-color: #95A5A6;
                color: white;
            }
            QPushButton.danger:hover {
                background-color: #7F8C8D;
            }
            QPushButton.danger:pressed {
                background-color: #6C7A7B;
            }
            
            /* Поля ввода */
            QLineEdit, QSpinBox {
                border: 1px solid #D0D5DD;
                border-radius: 4px;
                padding: 10px 12px;
                background-color: #FFFFFF;
                font-size: 13pt;
                color: #2C3E50;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #5B9BD5;
                background-color: #FFFFFF;
            }
            QLineEdit:disabled, QSpinBox:disabled {
                background-color: #F4F5F7;
                color: #7A869A;
            }
            
            /* Списки */
            QListWidget {
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                background-color: #FFFFFF;
                font-size: 13pt;
                padding: 4px;
            }
            QListWidget::item {
                border-radius: 4px;
                padding: 8px 10px;
                margin: 2px;
                color: #2C3E50;
            }
            QListWidget::item:selected {
                background-color: #D6E9F8;
                color: #2C5F8D;
                font-weight: 600;
            }
            QListWidget::item:hover {
                background-color: #F4F5F7;
            }
            
            /* Текстовые области (лог) */
            QTextEdit {
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                background-color: #FAFBFC;
                font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
                font-size: 11pt;
                padding: 10px;
                color: #2C3E50;
            }
            
            /* Чекбоксы */
            QCheckBox {
                font-size: 13pt;
                spacing: 10px;
                color: #2C3E50;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #D0D5DD;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #5B9BD5;
                border-color: #5B9BD5;
            }
            QCheckBox::indicator:hover {
                border-color: #5B9BD5;
            }
            
            /* Метки */
            QLabel {
                font-size: 13pt;
                color: #2C3E50;
            }
            QLabel.bold {
                font-weight: 600;
                font-size: 14pt;
                color: #2C3E50;
            }
            QLabel.section {
                font-size: 14pt;
                font-weight: 600;
                color: #2C3E50;
            }
            QLabel.hint {
                font-size: 12pt;
                color: #5A6C7D;
            }
            
            /* Область прокрутки */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            /* Полоса прокрутки */
            QScrollBar:vertical {
                background: #F4F5F7;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #A5ADBA;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7A869A;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _create_ui(self):
        """Создает элементы интерфейса"""
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Создаем главный layout с прокруткой
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Контейнер для содержимого
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # Добавляем секции
        scroll_layout.addWidget(self._create_main_section())
        scroll_layout.addWidget(self._create_comparison_section())
        scroll_layout.addWidget(self._create_log_section())
        scroll_layout.addWidget(self._create_database_section())
        scroll_layout.addStretch()
        scroll_layout.addWidget(self._create_footer())

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _create_main_section(self) -> QGroupBox:
        """Создает секцию основных настроек"""
        group = QGroupBox("Основные настройки")
        layout = QVBoxLayout()

        # Кнопки управления файлами
        buttons_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить файлы")
        add_btn.clicked.connect(self.on_add_files)
        self.lockable_widgets.append(add_btn)
        buttons_layout.addWidget(add_btn)

        clear_btn = QPushButton("Очистить список")
        clear_btn.setProperty("class", "danger")
        clear_btn.clicked.connect(self.on_clear_files)
        self.lockable_widgets.append(clear_btn)
        buttons_layout.addWidget(clear_btn)

        layout.addLayout(buttons_layout)

        # Список файлов
        files_label = QLabel("Входные файлы:")
        files_label.setProperty("class", "bold")
        layout.addWidget(files_label)

        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(150)
        self.files_list.itemSelectionChanged.connect(self.on_file_selected)
        self.lockable_widgets.append(self.files_list)
        layout.addWidget(self.files_list)

        # Количество экземпляров
        multiplier_layout = QHBoxLayout()
        multiplier_layout.addWidget(QLabel("Количество экземпляров:"))

        self.multiplier_spin = QSpinBox()
        self.multiplier_spin.setMinimum(1)
        self.multiplier_spin.setMaximum(999)
        self.multiplier_spin.setValue(1)
        self.lockable_widgets.append(self.multiplier_spin)
        multiplier_layout.addWidget(self.multiplier_spin)

        apply_mult_btn = QPushButton("Применить")
        apply_mult_btn.clicked.connect(self.on_multiplier_changed)
        self.lockable_widgets.append(apply_mult_btn)
        multiplier_layout.addWidget(apply_mult_btn)

        multiplier_layout.addWidget(QLabel("(выберите файл из списка)"))
        multiplier_layout.addStretch()

        layout.addLayout(multiplier_layout)

        # Листы Excel
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("Листы (через запятую):"))

        self.sheet_entry = QLineEdit()
        self.sheet_entry.setPlaceholderText("Оставьте пустым для всех листов")
        self.lockable_widgets.append(self.sheet_entry)
        sheet_layout.addWidget(self.sheet_entry)

        layout.addLayout(sheet_layout)

        # Выходной файл XLSX
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Выходной XLSX:"))

        self.output_entry = QLineEdit()
        self.output_entry.setText(self.output_xlsx)
        self.lockable_widgets.append(self.output_entry)
        output_layout.addWidget(self.output_entry)

        pick_output_btn = QPushButton("Выбрать...")
        pick_output_btn.clicked.connect(self.on_pick_output)
        self.lockable_widgets.append(pick_output_btn)
        output_layout.addWidget(pick_output_btn)

        layout.addLayout(output_layout)

        # Папка для TXT
        txt_layout = QHBoxLayout()
        txt_layout.addWidget(QLabel("Папка для TXT:"))

        self.txt_entry = QLineEdit()
        self.txt_entry.setPlaceholderText("Опционально")
        self.lockable_widgets.append(self.txt_entry)
        txt_layout.addWidget(self.txt_entry)

        pick_txt_btn = QPushButton("Выбрать...")
        pick_txt_btn.clicked.connect(self.on_pick_txt_dir)
        self.lockable_widgets.append(pick_txt_btn)
        txt_layout.addWidget(pick_txt_btn)

        layout.addLayout(txt_layout)

        # Чекбокс суммарной комплектации
        self.combine_check = QCheckBox("Суммарная комплектация")
        self.combine_check.setChecked(self.combine)
        self.combine_check.stateChanged.connect(
            lambda state: setattr(self, 'combine', state == Qt.Checked)
        )
        self.lockable_widgets.append(self.combine_check)
        layout.addWidget(self.combine_check)

        # Кнопки запуска
        action_layout = QHBoxLayout()

        run_btn = QPushButton("▶ Запустить обработку")
        run_btn.setProperty("class", "accent")
        run_btn.clicked.connect(self.on_run)
        self.lockable_widgets.append(run_btn)
        action_layout.addWidget(run_btn)

        interactive_btn = QPushButton("Интерактивная классификация")
        interactive_btn.clicked.connect(self.on_interactive_classify)
        self.lockable_widgets.append(interactive_btn)
        action_layout.addWidget(interactive_btn)

        layout.addLayout(action_layout)

        group.setLayout(layout)
        return group

    def _create_comparison_section(self) -> QGroupBox:
        """Создает секцию сравнения файлов"""
        group = QGroupBox("Сравнение BOM файлов")
        layout = QVBoxLayout()

        # Первый файл
        file1_layout = QHBoxLayout()
        file1_layout.addWidget(QLabel("Первый файл (базовый):"))

        self.compare_entry1 = QLineEdit()
        self.lockable_widgets.append(self.compare_entry1)
        file1_layout.addWidget(self.compare_entry1)

        pick_file1_btn = QPushButton("Выбрать...")
        pick_file1_btn.clicked.connect(self.on_select_compare_file1)
        self.lockable_widgets.append(pick_file1_btn)
        file1_layout.addWidget(pick_file1_btn)

        layout.addLayout(file1_layout)

        # Второй файл
        file2_layout = QHBoxLayout()
        file2_layout.addWidget(QLabel("Второй файл (новый):"))

        self.compare_entry2 = QLineEdit()
        self.lockable_widgets.append(self.compare_entry2)
        file2_layout.addWidget(self.compare_entry2)

        pick_file2_btn = QPushButton("Выбрать...")
        pick_file2_btn.clicked.connect(self.on_select_compare_file2)
        self.lockable_widgets.append(pick_file2_btn)
        file2_layout.addWidget(pick_file2_btn)

        layout.addLayout(file2_layout)

        # Выходной файл
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Файл результата:"))

        self.compare_output_entry = QLineEdit()
        self.compare_output_entry.setText(self.compare_output)
        self.lockable_widgets.append(self.compare_output_entry)
        output_layout.addWidget(self.compare_output_entry)

        pick_output_btn = QPushButton("Выбрать...")
        pick_output_btn.clicked.connect(self.on_select_compare_output)
        self.lockable_widgets.append(pick_output_btn)
        output_layout.addWidget(pick_output_btn)

        layout.addLayout(output_layout)

        # Кнопка сравнения
        compare_btn = QPushButton("⚡ Сравнить файлы")
        compare_btn.setProperty("class", "accent")
        compare_btn.clicked.connect(self.on_compare_files)
        self.lockable_widgets.append(compare_btn)
        layout.addWidget(compare_btn)

        group.setLayout(layout)
        return group

    def _create_log_section(self) -> QGroupBox:
        """Создает секцию лога выполнения"""
        group = QGroupBox("Лог выполнения")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def _create_database_section(self) -> QGroupBox:
        """Создает секцию управления базой данных"""
        group = QGroupBox("База данных")
        layout = QGridLayout()

        # Первая строка кнопок
        stats_btn = QPushButton("Статистика")
        stats_btn.clicked.connect(self.on_show_db_stats)
        self.lockable_widgets.append(stats_btn)
        layout.addWidget(stats_btn, 0, 0)

        export_btn = QPushButton("Экспорт")
        export_btn.clicked.connect(self.on_export_database)
        self.lockable_widgets.append(export_btn)
        layout.addWidget(export_btn, 0, 1)

        backup_btn = QPushButton("Резервная копия")
        backup_btn.clicked.connect(self.on_backup_database)
        self.lockable_widgets.append(backup_btn)
        layout.addWidget(backup_btn, 0, 2)

        # Вторая строка кнопок
        import_btn = QPushButton("Импорт")
        import_btn.clicked.connect(self.on_import_database)
        self.lockable_widgets.append(import_btn)
        layout.addWidget(import_btn, 1, 0)

        open_folder_btn = QPushButton("Открыть")
        open_folder_btn.clicked.connect(self.on_open_db_folder)
        self.lockable_widgets.append(open_folder_btn)
        layout.addWidget(open_folder_btn, 1, 1)

        replace_btn = QPushButton("Заменить БД")
        replace_btn.clicked.connect(self.on_replace_database)
        self.lockable_widgets.append(replace_btn)
        layout.addWidget(replace_btn, 1, 2)

        # Третья строка
        import_output_btn = QPushButton("Добавить все из выходного файла")
        import_output_btn.clicked.connect(self.on_import_from_output)
        self.lockable_widgets.append(import_output_btn)
        layout.addWidget(import_output_btn, 2, 0, 1, 3)

        group.setLayout(layout)
        return group

    def _create_footer(self) -> QWidget:
        """Создает футер с информацией"""
        footer = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Информация о разработчике
        dev_layout = QHBoxLayout()

        dev_label = QLabel("Разработчик: Куреин М.Н.")
        dev_label.setProperty("class", "bold")
        dev_label.mouseDoubleClickEvent = lambda event: self.on_developer_double_click()
        dev_layout.addWidget(dev_label)

        dev_layout.addStretch()

        date_label = QLabel(f"Дата: {self.cfg.get('app_info', {}).get('release_date', 'N/A')}")
        dev_layout.addWidget(date_label)

        layout.addLayout(dev_layout)

        # Информация о БД и размере окна
        info_layout = QHBoxLayout()

        # БД статистика
        try:
            stats = get_database_stats()
            db_version = stats.get('version', 'N/A')
            total_components = stats.get('total_components', 0)
            self.db_info_label = QLabel(f"БД: v{db_version} ({total_components} компонентов)")
        except Exception:
            self.db_info_label = QLabel("БД: Не загружена")

        info_layout.addWidget(self.db_info_label)

        info_layout.addStretch()

        # Информация о расположении
        db_path = get_database_path()
        if "%APPDATA%" in db_path or "AppData" in db_path:
            location_label = QLabel("Установка (%APPDATA%)")
        else:
            location_label = QLabel("Локальная")
        info_layout.addWidget(location_label)

        # Размер окна
        self.size_label = QLabel(f"{self.width()}×{self.height()}")
        self.size_label.mouseDoubleClickEvent = lambda event: self.on_show_size_menu(event)
        info_layout.addWidget(self.size_label)

        layout.addLayout(info_layout)

        footer.setLayout(layout)
        return footer

    # ==================== Обработчики событий ====================

    def on_add_files(self):
        """Добавление файлов"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите BOM файлы",
            "",
            "BOM Files (*.xlsx *.docx *.txt);;All Files (*)"
        )

        if files:
            for file_path in files:
                if file_path not in self.input_files:
                    self.input_files[file_path] = 1

            self.update_listbox()
            self.update_output_filename()

    def on_clear_files(self):
        """Очистка списка файлов"""
        self.input_files.clear()
        self.update_listbox()
        self.output_entry.setText("categorized.xlsx")

    def on_file_selected(self):
        """Обработка выбора файла из списка"""
        items = self.files_list.selectedItems()
        if items:
            item = items[0]
            text = item.text()
            # Извлекаем путь к файлу из текста (формат: "путь (x количество)")
            file_path = text.split(" (x")[0]
            if file_path in self.input_files:
                self.multiplier_spin.setValue(self.input_files[file_path])

    def on_multiplier_changed(self):
        """Применение множителя к выбранному файлу"""
        items = self.files_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Предупреждение", "Выберите файл из списка")
            return

        item = items[0]
        text = item.text()
        file_path = text.split(" (x")[0]

        if file_path in self.input_files:
            self.input_files[file_path] = self.multiplier_spin.value()
            self.update_listbox()

    def update_listbox(self):
        """Обновление списка файлов"""
        self.files_list.clear()
        for file_path, count in self.input_files.items():
            filename = os.path.basename(file_path)
            self.files_list.addItem(f"{file_path} (x{count})")

    def update_output_filename(self):
        """Автоматическое обновление имени выходного файла"""
        if len(self.input_files) == 1:
            file_path = list(self.input_files.keys())[0]
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_xlsx = f"{base_name}_categorized.xlsx"
            self.output_entry.setText(self.output_xlsx)

    def on_pick_output(self):
        """Выбор выходного файла"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат как",
            self.output_entry.text(),
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.output_entry.setText(file_path)

    def on_pick_txt_dir(self):
        """Выбор папки для TXT"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для TXT файлов"
        )

        if dir_path:
            self.txt_entry.setText(dir_path)

    def on_select_compare_file1(self):
        """Выбор первого файла для сравнения"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите первый файл (базовый)",
            "",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.compare_entry1.setText(file_path)

    def on_select_compare_file2(self):
        """Выбор второго файла для сравнения"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите второй файл (новый)",
            "",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.compare_entry2.setText(file_path)

    def on_select_compare_output(self):
        """Выбор файла результата сравнения"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат сравнения как",
            self.compare_output_entry.text(),
            "Excel Files (*.xlsx)"
        )

        if file_path:
            self.compare_output_entry.setText(file_path)

    def on_run(self):
        """Запуск обработки"""
        # TODO: Реализовать асинхронный запуск через QThread
        QMessageBox.information(self, "В разработке", "Функция обработки будет реализована")

    def on_compare_files(self):
        """Сравнение файлов"""
        # TODO: Реализовать сравнение
        QMessageBox.information(self, "В разработке", "Функция сравнения будет реализована")

    def on_interactive_classify(self):
        """Интерактивная классификация"""
        # TODO: Реализовать интерактивную классификацию
        QMessageBox.information(self, "В разработке", "Интерактивная классификация будет реализована")

    def on_show_db_stats(self):
        """Показать статистику БД"""
        try:
            stats = get_database_stats()
            dialog = DatabaseStatsDialog(stats, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить статистику: {e}")

    def on_export_database(self):
        """Экспорт БД"""
        # TODO: Реализовать экспорт
        QMessageBox.information(self, "В разработке", "Функция экспорта будет реализована")

    def on_backup_database(self):
        """Резервная копия БД"""
        # TODO: Реализовать резервное копирование
        QMessageBox.information(self, "В разработке", "Функция резервного копирования будет реализована")

    def on_import_database(self):
        """Импорт БД"""
        # TODO: Реализовать импорт
        QMessageBox.information(self, "В разработке", "Функция импорта будет реализована")

    def on_open_db_folder(self):
        """Открыть папку БД"""
        # TODO: Реализовать открытие папки
        QMessageBox.information(self, "В разработке", "Функция открытия папки будет реализована")

    def on_replace_database(self):
        """Заменить БД"""
        # TODO: Реализовать замену БД
        QMessageBox.information(self, "В разработке", "Функция замены БД будет реализована")

    def on_import_from_output(self):
        """Импорт из выходного файла"""
        # TODO: Реализовать импорт из выходного файла
        QMessageBox.information(self, "В разработке", "Функция импорта из выходного файла будет реализована")

    def on_developer_double_click(self):
        """Двойной клик на имени разработчика - PIN диалог"""
        if not self.unlocked and self.require_pin:
            dialog = PinDialog(self.correct_pin, self)
            if dialog.exec() == QDialog.Accepted and dialog.is_authenticated:
                self.unlock_interface()
                self.log_text.append("✅ Интерфейс разблокирован")
            else:
                self.log_text.append("❌ Авторизация отменена")

    def on_show_size_menu(self, event):
        """Показать меню размеров окна"""
        # TODO: Реализовать меню размеров
        pass

    def lock_interface(self):
        """Блокировка интерфейса"""
        for widget in self.lockable_widgets:
            widget.setEnabled(False)

    def unlock_interface(self):
        """Разблокировка интерфейса"""
        for widget in self.lockable_widgets:
            widget.setEnabled(True)
        self.unlocked = True

    def resizeEvent(self, event):
        """Обработка изменения размера окна"""
        super().resizeEvent(event)
        if hasattr(self, 'size_label'):
            self.size_label.setText(f"📐 {self.width()}×{self.height()}")


def main():
    """Точка входа для PySide6 приложения"""
    app = QApplication(sys.argv)

    # Устанавливаем имя приложения
    app.setApplicationName("BOM Categorizer")
    app.setOrganizationName("Kurein M.N.")

    # Создаем и показываем главное окно
    window = BOMCategorizerMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()