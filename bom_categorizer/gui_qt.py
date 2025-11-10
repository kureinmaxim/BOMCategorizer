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
    QFileDialog, QMessageBox, QScrollArea, QFrame, QDialog, QMenuBar, QMenu,
    QProgressDialog
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QAction
import subprocess

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
            import sys
            from io import StringIO
            
            # Перехватываем stdout для получения прогресса
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_argv = sys.argv
            
            captured_output = StringIO()
            
            try:
                sys.stdout = captured_output
                sys.stderr = captured_output
                sys.argv = ["split_bom.py"] + self.args
                
                # Отправляем начальное сообщение
                self.progress.emit("⏳ Начинаем обработку файлов...\n")
                self.progress.emit(f"Команда: split_bom {' '.join(self.args)}\n\n")
                
                # Запускаем обработку
                cli_main()
                
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
            from .main import compare_bom_files
            import sys
            from io import StringIO
            import codecs
            
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
                
                # Сначала пытаемся сравнить как обработанные файлы
                from .main import compare_processed_files, compare_bom_files
                
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
        buttons_layout.setSpacing(6)

        add_btn = QPushButton("➕ Добавить файлы")
        add_btn.clicked.connect(self.on_add_files)
        self.lockable_widgets.append(add_btn)
        buttons_layout.addWidget(add_btn, 1)  # stretch factor 1

        clear_btn = QPushButton("🗑️ Очистить список")
        clear_btn.setProperty("class", "danger")
        clear_btn.clicked.connect(self.on_clear_files)
        self.lockable_widgets.append(clear_btn)
        buttons_layout.addWidget(clear_btn, 1)  # stretch factor 1

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

        # Grid layout для выровненных полей
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)  # Растягиваем колонку с полями ввода
        grid.setColumnMinimumWidth(0, 180)  # Минимальная ширина для меток
        
        row = 0

        # Количество экземпляров
        label = QLabel("Количество экземпляров:")
        label.setMinimumWidth(180)
        grid.addWidget(label, row, 0, Qt.AlignLeft)

        mult_widget = QWidget()
        mult_layout = QHBoxLayout(mult_widget)
        mult_layout.setContentsMargins(0, 0, 0, 0)
        mult_layout.setSpacing(6)
        
        self.multiplier_spin = QSpinBox()
        self.multiplier_spin.setMinimum(1)
        self.multiplier_spin.setMaximum(999)
        self.multiplier_spin.setValue(1)
        self.multiplier_spin.setMaximumWidth(80)
        self.lockable_widgets.append(self.multiplier_spin)
        mult_layout.addWidget(self.multiplier_spin)

        apply_mult_btn = QPushButton("Применить")
        apply_mult_btn.setFixedWidth(100)
        apply_mult_btn.clicked.connect(self.on_multiplier_changed)
        self.lockable_widgets.append(apply_mult_btn)
        mult_layout.addWidget(apply_mult_btn)

        mult_layout.addWidget(QLabel("(выберите файл из списка)"))
        mult_layout.addStretch()
        
        grid.addWidget(mult_widget, row, 1)
        row += 1

        # Листы Excel
        label = QLabel("Листы (через запятую):")
        label.setMinimumWidth(180)
        grid.addWidget(label, row, 0, Qt.AlignLeft)
        
        self.sheet_entry = QLineEdit()
        self.sheet_entry.setPlaceholderText("Оставьте пустым для всех листов")
        self.lockable_widgets.append(self.sheet_entry)
        grid.addWidget(self.sheet_entry, row, 1)
        row += 1

        # Выходной файл XLSX
        label = QLabel("Выходной XLSX:")
        label.setMinimumWidth(180)
        grid.addWidget(label, row, 0, Qt.AlignLeft)
        
        self.output_entry = QLineEdit()
        self.output_entry.setText(self.output_xlsx)
        self.lockable_widgets.append(self.output_entry)
        grid.addWidget(self.output_entry, row, 1)
        
        pick_output_btn = QPushButton("Выбрать...")
        pick_output_btn.setFixedWidth(100)
        pick_output_btn.clicked.connect(self.on_pick_output)
        self.lockable_widgets.append(pick_output_btn)
        grid.addWidget(pick_output_btn, row, 2)
        row += 1

        # Папка для TXT
        label = QLabel("Папка для TXT:")
        label.setMinimumWidth(180)
        grid.addWidget(label, row, 0, Qt.AlignLeft)
        
        self.txt_entry = QLineEdit()
        self.txt_entry.setPlaceholderText("Опционально")
        self.lockable_widgets.append(self.txt_entry)
        grid.addWidget(self.txt_entry, row, 1)
        
        pick_txt_btn = QPushButton("Выбрать...")
        pick_txt_btn.setFixedWidth(100)
        pick_txt_btn.clicked.connect(self.on_pick_txt_dir)
        self.lockable_widgets.append(pick_txt_btn)
        grid.addWidget(pick_txt_btn, row, 2)
        
        layout.addLayout(grid)

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
        action_layout.setSpacing(6)

        run_btn = QPushButton("▶️ Запустить обработку")
        run_btn.setProperty("class", "accent")
        run_btn.clicked.connect(self.on_run)
        self.lockable_widgets.append(run_btn)
        action_layout.addWidget(run_btn, 1)  # stretch factor 1

        interactive_btn = QPushButton("🔄 Интерактивная классификация")
        interactive_btn.clicked.connect(self.on_interactive_classify)
        self.lockable_widgets.append(interactive_btn)
        action_layout.addWidget(interactive_btn, 1)  # stretch factor 1

        layout.addLayout(action_layout)

        group.setLayout(layout)
        return group

    def _create_comparison_section(self) -> QGroupBox:
        """Создает секцию сравнения файлов"""
        group = QGroupBox("Сравнение BOM файлов")
        layout = QVBoxLayout()

        # Grid layout для выровненных полей
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)  # Растягиваем колонку с полями ввода
        grid.setColumnMinimumWidth(0, 180)  # Минимальная ширина для меток
        
        row = 0

        # Первый файл
        label = QLabel("Первый файл (базовый):")
        label.setMinimumWidth(180)
        grid.addWidget(label, row, 0, Qt.AlignLeft)
        
        self.compare_entry1 = QLineEdit()
        self.lockable_widgets.append(self.compare_entry1)
        grid.addWidget(self.compare_entry1, row, 1)

        pick_file1_btn = QPushButton("Выбрать...")
        pick_file1_btn.setFixedWidth(100)
        pick_file1_btn.clicked.connect(self.on_select_compare_file1)
        self.lockable_widgets.append(pick_file1_btn)
        grid.addWidget(pick_file1_btn, row, 2)
        row += 1

        # Второй файл
        label = QLabel("Второй файл (новый):")
        label.setMinimumWidth(180)
        grid.addWidget(label, row, 0, Qt.AlignLeft)
        
        self.compare_entry2 = QLineEdit()
        self.lockable_widgets.append(self.compare_entry2)
        grid.addWidget(self.compare_entry2, row, 1)

        pick_file2_btn = QPushButton("Выбрать...")
        pick_file2_btn.setFixedWidth(100)
        pick_file2_btn.clicked.connect(self.on_select_compare_file2)
        self.lockable_widgets.append(pick_file2_btn)
        grid.addWidget(pick_file2_btn, row, 2)
        row += 1

        # Выходной файл
        label = QLabel("Файл результата:")
        label.setMinimumWidth(180)
        grid.addWidget(label, row, 0, Qt.AlignLeft)
        
        self.compare_output_entry = QLineEdit()
        self.compare_output_entry.setText(self.compare_output)
        self.lockable_widgets.append(self.compare_output_entry)
        grid.addWidget(self.compare_output_entry, row, 1)

        pick_output_btn = QPushButton("Выбрать...")
        pick_output_btn.setFixedWidth(100)
        pick_output_btn.clicked.connect(self.on_select_compare_output)
        self.lockable_widgets.append(pick_output_btn)
        grid.addWidget(pick_output_btn, row, 2)
        
        layout.addLayout(grid)

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

        # Размер окна (кликабельная метка)
        self.size_label = QLabel(f"📐 {self.width()}×{self.height()}")
        self.size_label.setStyleSheet("QLabel { color: #89b4fa; font-weight: bold; } QLabel:hover { color: #74c7ec; }")
        self.size_label.setCursor(Qt.PointingHandCursor)
        self.size_label.mousePressEvent = lambda event: self.on_show_size_menu(event)
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

    def _build_args(self, output_file: str) -> list:
        """
        Формирует список аргументов для CLI
        
        Args:
            output_file: Путь к выходному файлу
            
        Returns:
            Список аргументов для передачи в CLI
        """
        args = []
        if self.input_files:
            # Формируем список файлов в формате "файл:количество"
            file_specs = []
            for file_path, count in self.input_files.items():
                if count > 1:
                    file_specs.append(f"{file_path}:{count}")
                else:
                    file_specs.append(file_path)
            args.extend(["--inputs"] + file_specs)
        
        sheet_txt = self.sheet_entry.text().strip()
        if sheet_txt:
            args.extend(["--sheets", sheet_txt])
        
        args.extend(["--xlsx", output_file])
        
        if self.combine_check.isChecked():
            args.append("--combine")
        
        td = self.txt_entry.text().strip()
        if td:
            args.extend(["--txt-dir", td])
        
        # Всегда отключаем автоматический интерактивный режим в GUI
        args.append("--no-interactive")
        
        return args
    
    def check_and_convert_doc_files(self) -> bool:
        """
        Проверяет наличие .doc файлов и предлагает конвертацию
        
        Returns:
            True если можно продолжить, False если нужно остановить
        """
        # Ищем .doc файлы (старый формат)
        doc_files = [f for f in self.input_files.keys() if f.lower().endswith('.doc') and not f.lower().endswith('.docx')]
        
        if not doc_files:
            return True  # Нет .doc файлов, продолжаем
        
        # Показываем диалог конвертации
        dialog = DocConversionDialog(doc_files, self)
        result = dialog.exec()
        
        if result == QDialog.Rejected:
            return False  # Пользователь отменил
        
        # Проверяем успешность конвертации
        if dialog.converted_files:
            # Заменяем .doc на .docx в списке файлов
            for old_file, new_file in dialog.converted_files.items():
                if old_file in self.input_files:
                    count = self.input_files[old_file]
                    del self.input_files[old_file]
                    self.input_files[new_file] = count
            
            self.update_listbox()
            return True
        
        return dialog.can_continue
    
    def on_run(self):
        """Запуск обработки"""
        if not self.input_files:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Добавьте хотя бы один входной файл (XLSX/DOCX/DOC/TXT)"
            )
            return
        
        # Проверяем и конвертируем .doc файлы
        if not self.check_and_convert_doc_files():
            return  # Пользователь отменил или нужна ручная конвертация
        
        args = self._build_args(self.output_entry.text())
        
        # Очищаем лог
        self.log_text.clear()
        self.log_text.append(f"🚀 Запуск обработки BOM файлов...")
        self.log_text.append(f"Команда: split_bom {' '.join(args)}\n")
        
        # Создаем progress dialog
        self.progress_dialog = QProgressDialog(
            "Обработка файлов...",
            "Отмена",
            0, 0,
            self
        )
        self.progress_dialog.setWindowTitle("Обработка")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setCancelButton(None)  # Убираем кнопку отмены
        self.progress_dialog.show()
        
        # Создаем и запускаем worker
        self.processing_worker = ProcessingWorker(args)
        self.processing_worker.progress.connect(self.on_processing_progress)
        self.processing_worker.finished.connect(self.on_processing_finished)
        self.processing_worker.start()
    
    def on_processing_progress(self, message: str):
        """Обработка прогресса обработки"""
        self.log_text.append(message)
    
    def on_processing_finished(self, message: str, success: bool, output_file: str):
        """Обработка завершения обработки"""
        # Закрываем progress dialog
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        # Добавляем сообщение в лог
        self.log_text.append("\n" + message)
        
        # Показываем результат
        if success:
            QMessageBox.information(
                self,
                "Готово",
                message
            )
            
            # Проверяем наличие нераспределенных элементов
            if output_file:
                self.check_and_offer_interactive_classification(output_file)
        else:
            QMessageBox.critical(
                self,
                "Ошибка",
                message
            )
    
    def check_and_offer_interactive_classification(self, output_file: str):
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
            self.log_text.append(f"\n⚠️ Ошибка при проверке нераспределенных элементов: {e}\n")

    def on_compare_files(self):
        """Сравнение файлов"""
        file1 = self.compare_entry1.text().strip()
        file2 = self.compare_entry2.text().strip()
        output = self.compare_output_entry.text().strip()
        
        # Валидация
        if not file1 or not file2:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Выберите оба файла для сравнения"
            )
            return
        
        if not output:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Укажите имя файла для результатов"
            )
            return
        
        # Проверяем существование файлов
        if not os.path.exists(file1):
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Первый файл не найден:\n{file1}"
            )
            return
        
        if not os.path.exists(file2):
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Второй файл не найден:\n{file2}"
            )
            return
        
        # Очищаем лог
        self.log_text.clear()
        self.log_text.append("🔄 Сравнение файлов...")
        self.log_text.append(f"  Первый:  {os.path.basename(file1)}")
        self.log_text.append(f"  Второй:  {os.path.basename(file2)}")
        self.log_text.append(f"  Результат: {os.path.basename(output)}\n")
        
        # Создаем progress dialog
        self.progress_dialog = QProgressDialog(
            "Сравнение файлов...",
            "Отмена",
            0, 0,
            self
        )
        self.progress_dialog.setWindowTitle("Обработка")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setCancelButton(None)  # Убираем кнопку отмены
        self.progress_dialog.show()
        
        # Создаем и запускаем worker
        self.comparison_worker = ComparisonWorker(file1, file2, output)
        self.comparison_worker.progress.connect(self.on_comparison_progress)
        self.comparison_worker.finished.connect(self.on_comparison_finished)
        self.comparison_worker.start()
    
    def on_comparison_progress(self, message: str):
        """Обработка прогресса сравнения"""
        self.log_text.append(message)
    
    def on_comparison_finished(self, message: str, success: bool):
        """Обработка завершения сравнения"""
        # Закрываем progress dialog
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        # Добавляем сообщение в лог
        self.log_text.append("\n" + message)
        
        # Показываем результат
        if success:
            output_file = self.compare_output_entry.text().strip()
            reply = QMessageBox.question(
                self,
                "Готово",
                f"{message}\n\nОткрыть файл?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes and os.path.exists(output_file):
                try:
                    # Открываем файл в системном приложении
                    if platform.system() == 'Windows':
                        os.startfile(output_file)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.Popen(['open', output_file])
                    else:  # Linux
                        subprocess.Popen(['xdg-open', output_file])
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Предупреждение",
                        f"Не удалось открыть файл:\n{str(e)}"
                    )
        else:
            QMessageBox.critical(
                self,
                "Ошибка",
                message
            )

    def on_interactive_classify(self):
        """Интерактивная классификация"""
        output_file = self.output_entry.text().strip()
        
        if not output_file:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Сначала обработайте файлы, затем запустите интерактивную классификацию"
            )
            return
        
        if not os.path.exists(output_file):
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Выходной файл не найден:\n{output_file}\n\nСначала обработайте входные файлы"
            )
            return
        
        self.run_interactive_classification(output_file)
    
    def run_interactive_classification(self, output_file: str):
        """
        Запускает интерактивную классификацию для выходного файла
        
        Args:
            output_file: Путь к выходному файлу с нераспределенными элементами
        """
        try:
            import pandas as pd
            
            # Проверяем наличие листа "Не распределено"
            xls = pd.ExcelFile(output_file, engine='openpyxl')
            
            if 'Не распределено' not in xls.sheet_names:
                QMessageBox.information(
                    self,
                    "Информация",
                    "В файле нет нераспределенных элементов.\n\nВсе элементы уже классифицированы!"
                )
                return
            
            df_un = pd.read_excel(output_file, sheet_name='Не распределено', engine='openpyxl')
            
            # Фильтруем пустые строки
            df_un_valid = df_un[df_un['Наименование ИВП'].notna()]
            
            if len(df_un_valid) == 0:
                QMessageBox.information(
                    self,
                    "Информация",
                    "В листе 'Не распределено' нет элементов для классификации"
                )
                return
            
            # Показываем диалог классификации
            dialog = ClassificationDialog(df_un_valid, output_file, self)
            dialog.exec()
            
            # После завершения диалога обновляем лог
            if hasattr(dialog, 'classified_count') and dialog.classified_count > 0:
                self.log_text.append(f"\n✅ Классифицировано элементов: {dialog.classified_count}\n")
                self.log_text.append(f"   Файл обновлен: {output_file}\n")
                
                # Предлагаем открыть файл
                reply = QMessageBox.question(
                    self,
                    "Открыть файл?",
                    f"Классификация завершена!\n\n"
                    f"Классифицировано: {dialog.classified_count} элементов\n\n"
                    f"Открыть файл?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes and os.path.exists(output_file):
                    if platform.system() == 'Windows':
                        os.startfile(output_file)
                    elif platform.system() == 'Darwin':
                        subprocess.Popen(['open', output_file])
                    else:
                        subprocess.Popen(['xdg-open', output_file])
            
        except Exception as e:
            import traceback
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось запустить интерактивную классификацию:\n{str(e)}\n\n{traceback.format_exc()}"
            )


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
        from PySide6.QtCore import QPoint
        
        menu = QMenu(self)
        
        # Предустановленные размеры
        sizes = [
            ("По умолчанию (620×800)", 620, 800),
            ("Компактный (720×792)", 720, 792),
            ("Средний (800×850)", 800, 850),
            ("Большой (900×900)", 900, 900),
            ("Широкий (1000×800)", 1000, 800),
            ("HD (1280×720)", 1280, 720),
        ]
        
        for label, w, h in sizes:
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, width=w, height=h: self.set_window_size(width, height))
            menu.addAction(action)
        
        menu.addSeparator()
        
        save_action = QAction("📌 Сохранить текущий размер", self)
        save_action.triggered.connect(self.save_current_window_size)
        menu.addAction(save_action)
        
        # Показываем меню у метки размера окна
        menu.exec(self.size_label.mapToGlobal(QPoint(0, self.size_label.height())))
    
    def set_window_size(self, width: int, height: int):
        """Устанавливает размер окна"""
        self.resize(width, height)
        self.save_window_size_to_config(width, height)
        QMessageBox.information(self, "Размер окна", f"Размер окна изменен на {width}×{height}")
    
    def save_current_window_size(self):
        """Сохраняет текущий размер окна"""
        width = self.width()
        height = self.height()
        self.save_window_size_to_config(width, height)
        QMessageBox.information(self, "Размер сохранен", f"Текущий размер окна ({width}×{height}) сохранен в конфигурацию")
    
    def save_window_size_to_config(self, width: int, height: int):
        """Сохраняет размер окна в конфигурационный файл"""
        try:
            self.cfg["window"] = {
                "width": width,
                "height": height,
                "remember_size": True
            }
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_qt.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Не удалось сохранить размер окна: {e}")

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
    
    def closeEvent(self, event):
        """Обработка закрытия окна - сохранение настроек"""
        try:
            # Сохраняем размер окна
            self.save_window_size_to_config(self.width(), self.height())
            
            # Сохраняем тему (уже сохраняется в save_theme_preference, но на всякий случай)
            if "ui" not in self.cfg:
                self.cfg["ui"] = {}
            self.cfg["ui"]["theme"] = self.current_theme
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_qt.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Не удалось сохранить настройки: {e}")
        
        # Закрываем окно
        event.accept()

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