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
    QFileDialog, QMessageBox, QScrollArea, QFrame, QDialog, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QAction

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

from .styles import DARK_THEME, LIGHT_THEME


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

        # Тема интерфейса
        self.current_theme = self.cfg.get("ui", {}).get("theme", "dark")  # "dark" или "light"

        # Применяем стили
        self._setup_styles()

        # Создаем UI
        self._create_ui()

        # Создаем меню
        self._create_menu()

        # Применяем блокировку интерфейса при необходимости
        if self.require_pin:
            self.lock_interface()

    def _setup_styles(self):
        """Настраивает стили приложения с поддержкой темной и светлой темы"""
        # Устанавливаем системный шрифт с увеличенным размером
        font = QFont(get_system_font(), 12)
        self.setFont(font)

        # Применяем тему
        self.apply_theme()

    def apply_theme(self):
        """Применяет выбранную тему к приложению"""
        if self.current_theme == "dark":
            self.setStyleSheet(DARK_THEME)
        else:
            self.setStyleSheet(LIGHT_THEME)

    def toggle_theme(self):
        """Переключает между темной и светлой темой"""
        # Переключаем тему
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        
        # Применяем новую тему
        self.apply_theme()
        
        # Сохраняем выбор в конфиг
        self.save_theme_preference()
        
        # Показываем уведомление
        theme_name = "Темная" if self.current_theme == "dark" else "Светлая"
        QMessageBox.information(
            self,
            "Тема изменена",
            f"{theme_name} тема применена успешно!"
        )

    def save_theme_preference(self):
        """Сохраняет выбор темы в конфигурационный файл"""
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_qt.json")
        try:
            # Обновляем конфиг в памяти
            if "ui" not in self.cfg:
                self.cfg["ui"] = {}
            self.cfg["ui"]["theme"] = self.current_theme
            
            # Сохраняем в файл
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Не удалось сохранить настройку темы: {e}")

    def _create_menu(self):
        """Создает меню приложения"""
        menubar = self.menuBar()
        
        # Меню "Вид"
        view_menu = menubar.addMenu("Вид")
        
        # Пункт переключения темы
        theme_action = QAction("🌓 Переключить тему", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Меню "База данных"
        db_menu = menubar.addMenu("База данных")
        
        # Статистика БД
        stats_action = QAction("📊 Статистика", self)
        stats_action.triggered.connect(self.show_database_stats)
        db_menu.addAction(stats_action)
        
        # Экспорт БД
        export_action = QAction("📤 Экспорт в Excel", self)
        export_action.triggered.connect(self.export_database)
        db_menu.addAction(export_action)
        
        # Импорт БД
        import_action = QAction("📥 Импорт из Excel", self)
        import_action.triggered.connect(self.import_database)
        db_menu.addAction(import_action)
        
        db_menu.addSeparator()
        
        # Резервное копирование
        backup_action = QAction("💾 Резервное копирование", self)
        backup_action.triggered.connect(self.backup_database)
        db_menu.addAction(backup_action)
        
        # Открыть папку БД
        folder_action = QAction("📁 Открыть папку БД", self)
        folder_action.triggered.connect(self.open_database_folder)
        db_menu.addAction(folder_action)
        
        db_menu.addSeparator()
        
        # Заменить БД
        replace_action = QAction("🔄 Заменить БД", self)
        replace_action.triggered.connect(self.on_replace_database)
        db_menu.addAction(replace_action)
        
        # Добавить все из выходного файла
        import_output_action = QAction("📋 Добавить из выходного файла", self)
        import_output_action.triggered.connect(self.on_import_from_output)
        db_menu.addAction(import_output_action)
        
        # Меню "Помощь"
        help_menu = menubar.addMenu("Помощь")
        
        # О программе
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_ui(self):
        """Создает элементы интерфейса"""
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Создаем главный layout с прокруткой
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Контейнер для содержимого
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)

        # Добавляем секции
        scroll_layout.addWidget(self._create_main_section())
        scroll_layout.addWidget(self._create_comparison_section())
        scroll_layout.addWidget(self._create_log_section())
        # scroll_layout.addWidget(self._create_database_section())  # Перенесено в меню
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

        add_btn = QPushButton("➕ Добавить файлы")
        add_btn.clicked.connect(self.on_add_files)
        self.lockable_widgets.append(add_btn)
        buttons_layout.addWidget(add_btn)

        clear_btn = QPushButton("🗑️ Очистить список")
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
        self.files_list.setMaximumHeight(100)
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

        run_btn = QPushButton("▶️ Запустить обработку")
        run_btn.setProperty("class", "accent")
        run_btn.clicked.connect(self.on_run)
        self.lockable_widgets.append(run_btn)
        action_layout.addWidget(run_btn)

        interactive_btn = QPushButton("🔄 Интерактивная классификация")
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
        self.log_text.setMaximumHeight(80)
        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def _create_database_section(self) -> QGroupBox:
        """Создает секцию управления базой данных"""
        group = QGroupBox("База данных")
        layout = QGridLayout()

        # Первая строка кнопок
        stats_btn = QPushButton("📊 Статистика")
        stats_btn.clicked.connect(self.on_show_db_stats)
        self.lockable_widgets.append(stats_btn)
        layout.addWidget(stats_btn, 0, 0)

        export_btn = QPushButton("📤 Экспорт")
        export_btn.clicked.connect(self.on_export_database)
        self.lockable_widgets.append(export_btn)
        layout.addWidget(export_btn, 0, 1)

        backup_btn = QPushButton("💾 Резервная копия")
        backup_btn.clicked.connect(self.on_backup_database)
        self.lockable_widgets.append(backup_btn)
        layout.addWidget(backup_btn, 0, 2)

        # Вторая строка кнопок
        import_btn = QPushButton("📥 Импорт")
        import_btn.clicked.connect(self.on_import_database)
        self.lockable_widgets.append(import_btn)
        layout.addWidget(import_btn, 1, 0)

        open_folder_btn = QPushButton("📁 Открыть папку")
        open_folder_btn.clicked.connect(self.on_open_db_folder)
        self.lockable_widgets.append(open_folder_btn)
        layout.addWidget(open_folder_btn, 1, 1)

        replace_btn = QPushButton("🔄 Заменить БД")
        replace_btn.clicked.connect(self.on_replace_database)
        self.lockable_widgets.append(replace_btn)
        layout.addWidget(replace_btn, 1, 2)

        # Третья строка
        import_output_btn = QPushButton("📋 Добавить из выходного файла")
        import_output_btn.clicked.connect(self.on_import_from_output)
        self.lockable_widgets.append(import_output_btn)
        layout.addWidget(import_output_btn, 2, 0, 1, 3)

        group.setLayout(layout)
        return group

    def _create_footer(self) -> QWidget:
        """Создает футер с информацией"""
        footer = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)

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
        """Открыть папку с базой данных в проводнике"""
        try:
            db_path = get_database_path()
            folder_path = os.path.dirname(db_path)
            
            # Открываем в проводнике
            import sys
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f'open "{folder_path}"')
            else:  # Linux
                os.system(f'xdg-open "{folder_path}"')
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть папку:\n{str(e)}")

    def on_replace_database(self):
        """Заменить текущую базу данных на другую из JSON файла"""
        try:
            # Выбор файла базы данных
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите файл базы данных (component_database.json)",
                "",
                "JSON файлы (*.json);;Все файлы (*.*)"
            )
            
            if not file_path:
                return
            
            # Проверяем что файл существует и валиден
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "Ошибка", f"Файл не найден:\n{file_path}")
                return
            
            # Проверяем формат файла
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Проверяем что это база данных компонентов
                if not isinstance(data, dict):
                    QMessageBox.critical(self, "Ошибка", "Неверный формат файла!\n\nОжидается JSON с данными компонентов.")
                    return
                
                # Определяем количество компонентов
                if "components" in data:
                    component_count = len(data["components"])
                elif "metadata" in data or "categories" in data:
                    QMessageBox.critical(self, "Ошибка", "Файл не содержит компонентов!")
                    return
                else:
                    # Старый формат - прямой словарь
                    component_count = len(data)
                
                if component_count == 0:
                    reply = QMessageBox.question(
                        self,
                        "Предупреждение",
                        "⚠️ Выбранная база данных пустая (0 компонентов)!\n\n"
                        "Это удалит все компоненты из текущей базы.\n\n"
                        "Продолжить?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
                
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Ошибка", "Файл поврежден или имеет неверный формат JSON!")
                return
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл:\n{str(e)}")
                return
            
            # Получаем информацию о текущей базе
            current_db_path = get_database_path()
            current_stats = get_database_stats()
            current_count = current_stats.get('total', 0)
            
            # Подтверждение замены
            reply = QMessageBox.question(
                self,
                "Подтверждение замены",
                f"🔄 ЗАМЕНА БАЗЫ ДАННЫХ\n\n"
                f"Текущая база данных:\n"
                f"  📊 Компонентов: {current_count}\n"
                f"  📁 Расположение: ...{current_db_path[-50:]}\n\n"
                f"Новая база данных:\n"
                f"  📊 Компонентов: {component_count}\n"
                f"  📁 Файл: {os.path.basename(file_path)}\n\n"
                f"⚠️ Текущая база будет заменена!\n"
                f"Резервная копия будет создана автоматически.\n\n"
                f"Продолжить?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Создаем резервную копию текущей базы
            try:
                backup_file = backup_database()
                self.log_text.append(f"\n💾 Резервная копия создана:")
                self.log_text.append(f"   {os.path.basename(backup_file)}\n")
            except Exception as e:
                reply = QMessageBox.question(
                    self,
                    "Ошибка резервного копирования",
                    f"Не удалось создать резервную копию:\n{str(e)}\n\n"
                    f"Продолжить без резервной копии?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # Копируем новую базу данных
            import shutil
            shutil.copy2(file_path, current_db_path)
            
            # Проверяем что копирование прошло успешно
            new_stats = get_database_stats()
            new_count = new_stats.get('total', 0)
            
            self.log_text.append(f"\n✅ База данных успешно заменена!")
            self.log_text.append(f"   Новое количество компонентов: {new_count}")
            self.log_text.append(f"   Расположение: {current_db_path}\n")
            
            QMessageBox.information(
                self,
                "Успех",
                f"✅ База данных успешно заменена!\n\n"
                f"Компонентов в новой базе: {new_count}\n\n"
                f"Резервная копия старой базы сохранена.\n\n"
                f"Перезапустите приложение чтобы увидеть\n"
                f"актуальные данные в футере."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось заменить базу данных:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def on_import_from_output(self):
        """Импорт всех компонентов из выходного файла в базу данных"""
        try:
            # Проверяем есть ли выходной файл
            output_file = self.output_entry.text()
            
            if not output_file or not os.path.exists(output_file):
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Выходной файл не найден!\n\n"
                    "Сначала обработайте входные файлы, "
                    "проверьте результат, а затем импортируйте компоненты в базу данных."
                )
                return
            
            # Подтверждение
            reply = QMessageBox.question(
                self,
                "Импорт из выходного файла",
                f"Вы хотите добавить ВСЕ компоненты из файла:\n\n"
                f"{os.path.basename(output_file)}\n\n"
                f"в базу данных?\n\n"
                f"Это позволит автоматически классифицировать эти компоненты "
                f"в будущем при обработке других файлов.\n\n"
                f"Продолжить?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Создаем диалог прогресса
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle("Импорт из выходного файла")
            progress_dialog.setMinimumSize(600, 400)
            progress_dialog.setModal(True)
            
            layout = QVBoxLayout(progress_dialog)
            
            progress_text = QTextEdit()
            progress_text.setReadOnly(True)
            layout.addWidget(progress_text)
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(progress_dialog.accept)
            close_btn.setEnabled(False)
            layout.addWidget(close_btn)
            
            progress_text.append("📥 Импорт компонентов из выходного файла...")
            progress_text.append(f"Файл: {output_file}\n")
            
            progress_dialog.show()
            QApplication.processEvents()
            
            # Импортируем компоненты
            import pandas as pd
            
            # Маппинг русских названий листов на ключи категорий
            SHEET_TO_CATEGORY = {
                'Резисторы': 'resistors',
                'Конденсаторы': 'capacitors',
                'Индуктивности': 'inductors',
                'Полупроводники': 'semiconductors',
                'Микросхемы': 'ics',
                'Разъемы': 'connectors',
                'Оптика': 'optics',
                'СВЧ модули': 'rf_modules',
                'Кабели': 'cables',
                'Модули питания': 'power_modules',
                'Отладочные платы': 'dev_boards',
                'Наши разработки': 'our_developments',
                'Другие': 'others',
            }
            
            # Читаем файл Excel
            xl_file = pd.ExcelFile(output_file, engine='openpyxl')
            
            added_count = 0
            skipped_count = 0
            total_sheets = 0
            
            progress_text.append("📊 Обработка листов:\n")
            QApplication.processEvents()
            
            # Обрабатываем каждый лист
            for sheet_name in xl_file.sheet_names:
                # Пропускаем служебные листы
                if sheet_name in ['SOURCES', 'SUMMARY', 'Не распределено', 'INFO']:
                    continue
                
                # Проверяем что это лист категории
                if sheet_name not in SHEET_TO_CATEGORY:
                    continue
                
                category_key = SHEET_TO_CATEGORY[sheet_name]
                total_sheets += 1
                
                # Читаем данные
                df = pd.read_excel(output_file, sheet_name=sheet_name, engine='openpyxl')
                
                if df.empty:
                    continue
                
                # Ищем колонку с наименованием
                name_col = None
                for col in ['Наименование ИВП', 'Наименование', 'наименование ивп', 'наименование']:
                    if col in df.columns:
                        name_col = col
                        break
                
                if not name_col:
                    progress_text.append(f"⚠️  {sheet_name}: не найдена колонка с наименованием")
                    continue
                
                sheet_added = 0
                
                # Добавляем каждый компонент в базу данных
                for idx, row in df.iterrows():
                    name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
                    
                    # Пропускаем пустые названия
                    if not name or name == 'nan':
                        skipped_count += 1
                        continue
                    
                    # Добавляем в базу данных
                    add_component_to_database(name, category_key)
                    added_count += 1
                    sheet_added += 1
                
                progress_text.append(f"✅ {sheet_name}: добавлено {sheet_added} компонентов")
                QApplication.processEvents()
            
            progress_text.append(f"\n✅ Импорт завершен!\n")
            progress_text.append(f"📈 Статистика:")
            progress_text.append(f"   Обработано листов: {total_sheets}")
            progress_text.append(f"   Добавлено компонентов: {added_count}")
            progress_text.append(f"   Пропущено (пустые): {skipped_count}\n")
            
            # Показываем обновленную статистику базы данных
            stats = get_database_stats()
            progress_text.append(f"📊 База данных после импорта:")
            progress_text.append(f"   Всего компонентов: {stats['total']}")
            
            close_btn.setEnabled(True)
            progress_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать компоненты:\n{str(e)}")
            import traceback
            traceback.print_exc()

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

    # =======================
    # Методы меню
    # =======================

    def show_database_stats(self):
        """Показывает статистику базы данных"""
        try:
            dialog = DatabaseStatsDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось показать статистику базы данных:\n{str(e)}"
            )

    def export_database(self):
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

    def import_database(self):
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
                    backup_database()
                    # Копируем новый файл
                    shutil.copy2(file_path, db_path)
                    stats = get_database_stats()
                    imported_count = stats.get('total_components', 0)
                elif file_path.endswith('.xlsx'):
                    # Создаем резервную копию
                    backup_database()
                    # Импортируем из Excel
                    imported_count = import_database_from_excel(file_path, replace=True)
                else:
                    QMessageBox.warning(
                        self,
                        "Неподдерживаемый формат",
                        "Поддерживаются только файлы .xlsx и .json"
                    )
                    return

                QMessageBox.information(
                    self,
                    "Импорт завершен",
                    f"✅ База данных успешно импортирована!\n\n"
                    f"Компонентов импортировано: {imported_count}\n"
                    f"База данных: {get_database_path()}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка импорта",
                    f"Не удалось импортировать базу данных:\n{str(e)}"
                )

    def backup_database(self):
        """Создает резервную копию базы данных"""
        try:
            backup_file = backup_database()
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

    def open_database_folder(self):
        """Открывает папку с базой данных в проводнике"""
        try:
            db_path = get_database_path()
            db_dir = os.path.dirname(db_path)

            # Открываем папку в системном проводнике
            if platform.system() == 'Windows':
                os.startfile(db_dir)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{db_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{db_dir}"')
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось открыть папку:\n{str(e)}"
            )

    def show_about(self):
        """Показывает информацию о программе"""
        ver = self.cfg.get("app_info", {}).get("version", "dev")
        edition = self.cfg.get("app_info", {}).get("edition", "Modern Edition")
        
        about_text = f"""
<h2>BOM Categorizer {edition}</h2>
<p><b>Версия:</b> {ver}</p>
<p><b>Разработчик:</b> Куреин М.Н. / Kurein M.N.</p>
<p><b>Дата:</b> 08.11.2025</p>

<p><b>Возможности:</b></p>
<ul>
<li>📋 Обработка файлов: XLSX, DOCX, TXT</li>
<li>🤖 Автоматическая классификация компонентов</li>
<li>🎨 Форматирование и сортировка</li>
<li>🗄️ База данных компонентов</li>
<li>🖥️ Современный темный/светлый интерфейс</li>
<li>🔒 PIN защита</li>
<li>💾 Экспорт в Excel и TXT</li>
</ul>

<p><b>Горячие клавиши:</b></p>
<ul>
<li>Ctrl+T - Переключить тему</li>
</ul>

<p style="color: #7287fd;"><b>Modern Edition</b> на основе PySide6 (Qt)</p>
        """

        QMessageBox.about(self, "О программе", about_text)


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