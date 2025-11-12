# -*- coding: utf-8 -*-
"""
Модуль создания секций интерфейса

Содержит функции для создания различных секций GUI:
- Основные настройки
- Сравнение файлов
- Лог выполнения
- Экспертные инструменты
- Футер
"""

from typing import TYPE_CHECKING
from datetime import datetime
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QCheckBox, QListWidget, QTextEdit, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

if TYPE_CHECKING:
    from .gui_qt import BOMCategorizerMainWindow

from .component_database import get_database_stats, get_database_path


def create_main_section(window: 'BOMCategorizerMainWindow') -> QGroupBox:
    """Создает секцию основных настроек"""
    group = QGroupBox("Основные настройки")
    layout = QVBoxLayout()

    # Кнопки управления файлами
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(6)

    add_btn = QPushButton("➕ Добавить файлы")
    add_btn.setToolTip("Добавить BOM файлы для обработки (F1 - справка)")
    add_btn.clicked.connect(window.on_add_files)
    window.lockable_widgets.append(add_btn)
    buttons_layout.addWidget(add_btn, 1)

    clear_btn = QPushButton("🗑️ Очистить список")
    clear_btn.setProperty("class", "danger")
    clear_btn.clicked.connect(window.on_clear_files)
    window.lockable_widgets.append(clear_btn)
    buttons_layout.addWidget(clear_btn, 1)

    layout.addLayout(buttons_layout)

    # Список файлов
    files_label = QLabel("Входные файлы:")
    files_label.setProperty("class", "bold")
    layout.addWidget(files_label)

    window.files_list = QListWidget()
    window.files_list.setMaximumHeight(100)
    window.files_list.itemSelectionChanged.connect(window.on_file_selected)
    window.lockable_widgets.append(window.files_list)
    layout.addWidget(window.files_list)

    # Grid layout для выровненных полей
    grid = QGridLayout()
    grid.setHorizontalSpacing(8)
    grid.setVerticalSpacing(6)
    grid.setColumnStretch(1, 1)
    grid.setColumnMinimumWidth(0, 180)
    
    row = 0

    # Количество экземпляров
    label = QLabel("Количество экземпляров:")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    mult_widget = QWidget()
    mult_layout = QHBoxLayout(mult_widget)
    mult_layout.setContentsMargins(0, 0, 0, 0)
    mult_layout.setSpacing(6)

    window.multiplier_spin = QSpinBox()
    window.multiplier_spin.setMinimum(1)
    window.multiplier_spin.setMaximum(999)
    window.multiplier_spin.setValue(1)
    window.multiplier_spin.setMaximumWidth(80)
    window.lockable_widgets.append(window.multiplier_spin)
    mult_layout.addWidget(window.multiplier_spin)

    apply_mult_btn = QPushButton("Применить")
    apply_mult_btn.setFixedWidth(100)
    apply_mult_btn.clicked.connect(window.on_multiplier_changed)
    window.lockable_widgets.append(apply_mult_btn)
    mult_layout.addWidget(apply_mult_btn)

    mult_layout.addWidget(QLabel("(выберите файл из списка)"))
    mult_layout.addStretch()

    grid.addWidget(mult_widget, row, 1)
    row += 1

    # Листы Excel
    label = QLabel("Листы (через запятую):")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    window.sheet_entry = QLineEdit()
    window.sheet_entry.setPlaceholderText("Оставьте пустым для всех листов")
    window.lockable_widgets.append(window.sheet_entry)
    grid.addWidget(window.sheet_entry, row, 1)
    row += 1

    # Выходной файл XLSX
    label = QLabel("Выходной XLSX:")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    window.output_entry = QLineEdit()
    window.output_entry.setText(window.output_xlsx)
    window.lockable_widgets.append(window.output_entry)
    grid.addWidget(window.output_entry, row, 1)

    pick_output_btn = QPushButton("Выбрать...")
    pick_output_btn.setFixedWidth(100)
    pick_output_btn.clicked.connect(window.on_pick_output)
    window.lockable_widgets.append(pick_output_btn)
    grid.addWidget(pick_output_btn, row, 2)
    row += 1

    # Папка для TXT
    label = QLabel("Папка для TXT:")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    window.txt_entry = QLineEdit()
    window.txt_entry.setPlaceholderText("Опционально")
    window.lockable_widgets.append(window.txt_entry)
    grid.addWidget(window.txt_entry, row, 1)

    pick_txt_btn = QPushButton("Выбрать...")
    pick_txt_btn.setFixedWidth(100)
    pick_txt_btn.clicked.connect(window.on_pick_txt_dir)
    window.lockable_widgets.append(pick_txt_btn)
    grid.addWidget(pick_txt_btn, row, 2)

    layout.addLayout(grid)

    # Чекбокс суммарной комплектации
    window.combine_check = QCheckBox("Суммарная комплектация")
    window.combine_check.setChecked(window.combine)
    window.combine_check.stateChanged.connect(
        lambda state: setattr(window, 'combine', state == Qt.Checked)
    )
    window.lockable_widgets.append(window.combine_check)
    layout.addWidget(window.combine_check)

    # Кнопки запуска
    action_layout = QHBoxLayout()
    action_layout.setSpacing(6)

    run_btn = QPushButton("▶️ Запустить обработку")
    run_btn.setProperty("class", "accent")
    run_btn.clicked.connect(window.on_run)
    window.lockable_widgets.append(run_btn)
    action_layout.addWidget(run_btn, 1)

    interactive_btn = QPushButton("🔄 Интерактивная классификация")
    interactive_btn.clicked.connect(window.on_interactive_classify)
    window.lockable_widgets.append(interactive_btn)
    action_layout.addWidget(interactive_btn, 1)

    layout.addLayout(action_layout)

    group.setLayout(layout)
    return group


def create_comparison_section(window: 'BOMCategorizerMainWindow') -> QGroupBox:
    """Создает секцию сравнения файлов"""
    group = QGroupBox("Сравнение BOM файлов")
    layout = QVBoxLayout()

    # Grid layout для выровненных полей
    grid = QGridLayout()
    grid.setHorizontalSpacing(8)
    grid.setVerticalSpacing(6)
    grid.setColumnStretch(1, 1)
    grid.setColumnMinimumWidth(0, 180)
    
    row = 0

    # Первый файл
    label = QLabel("Первый файл (базовый):")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    window.compare_entry1 = QLineEdit()
    window.lockable_widgets.append(window.compare_entry1)
    grid.addWidget(window.compare_entry1, row, 1)

    pick_file1_btn = QPushButton("Выбрать...")
    pick_file1_btn.setFixedWidth(100)
    pick_file1_btn.clicked.connect(window.on_select_compare_file1)
    window.lockable_widgets.append(pick_file1_btn)
    grid.addWidget(pick_file1_btn, row, 2)
    row += 1

    # Второй файл
    label = QLabel("Второй файл (новый):")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    window.compare_entry2 = QLineEdit()
    window.lockable_widgets.append(window.compare_entry2)
    grid.addWidget(window.compare_entry2, row, 1)

    pick_file2_btn = QPushButton("Выбрать...")
    pick_file2_btn.setFixedWidth(100)
    pick_file2_btn.clicked.connect(window.on_select_compare_file2)
    window.lockable_widgets.append(pick_file2_btn)
    grid.addWidget(pick_file2_btn, row, 2)
    row += 1

    # Выходной файл
    label = QLabel("Файл результата:")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    window.compare_output_entry = QLineEdit()
    window.compare_output_entry.setText(window.compare_output)
    window.lockable_widgets.append(window.compare_output_entry)
    grid.addWidget(window.compare_output_entry, row, 1)

    pick_output_btn = QPushButton("Выбрать...")
    pick_output_btn.setFixedWidth(100)
    pick_output_btn.clicked.connect(window.on_select_compare_output)
    window.lockable_widgets.append(pick_output_btn)
    grid.addWidget(pick_output_btn, row, 2)

    layout.addLayout(grid)

    # Кнопка сравнения
    compare_btn = QPushButton("⚡ Сравнить файлы")
    compare_btn.setProperty("class", "accent")
    compare_btn.clicked.connect(window.on_compare_files)
    window.lockable_widgets.append(compare_btn)
    layout.addWidget(compare_btn)

    group.setLayout(layout)
    return group


def create_log_section(window: 'BOMCategorizerMainWindow') -> QGroupBox:
    """Создает секцию лога выполнения"""
    group = QGroupBox("Лог выполнения")
    group.setToolTip(
        "📝 <b>Лог выполнения</b><br><br>"
        "Область для отображения информации о процессе обработки файлов.<br><br>"
        "<b>Функции:</b><br>"
        "• Показывает прогресс обработки<br>"
        "• Отображает ошибки и предупреждения<br>"
        "• Двойной клик открывает лог в текстовом редакторе<br>"
        "• В экспертном режиме можно включить временные метки<br><br>"
        "<b>Справка:</b> Наведите курсор на область лога и нажмите <b>F1</b> для получения подробной информации"
    )
    layout = QVBoxLayout()

    window.log_text = QTextEdit()
    window.log_text.setReadOnly(True)
    window.log_text.setMaximumHeight(160)
    window.log_text.mouseDoubleClickEvent = lambda event: window.on_log_double_click(event)
    window.log_text.setCursor(Qt.PointingHandCursor)
    window.log_text.setToolTip(
        "📝 <b>Лог выполнения</b><br><br>"
        "Отображает информацию о процессе обработки файлов:<br>"
        "• Прогресс обработки<br>"
        "• Ошибки и предупреждения<br>"
        "• Результаты операций<br><br>"
        "<b>Действия:</b><br>"
        "• <b>Двойной клик</b> - открыть лог в текстовом редакторе<br>"
        "• <b>F1</b> - получить подробную справку"
    )

    original_append = window.log_text.append

    def append_with_mode(message):
        text = "" if message is None else str(message)
        if getattr(window, "log_with_timestamps", False) and text.strip():
            leading_newlines = len(text) - len(text.lstrip('\n'))
            prefix = "\n" * leading_newlines
            body = text.lstrip('\n')
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_body = f"[{timestamp}] {body}" if body else f"[{timestamp}]"
            original_append(prefix + formatted_body)
        else:
            original_append(text)

    window._log_append_original = original_append
    window.log_text.append = append_with_mode

    layout.addWidget(window.log_text)

    group.setLayout(layout)
    return group


def create_expert_tools_section(window: 'BOMCategorizerMainWindow') -> QGroupBox:
    """Создает секцию экспертных инструментов"""
    group = QGroupBox("Экспертные инструменты")
    layout = QVBoxLayout()

    description = QLabel("Дополнительные настройки для опытных пользователей.")
    description.setWordWrap(True)
    layout.addWidget(description)

    window.timestamp_checkbox = QCheckBox("Добавлять временные метки в лог")
    window.timestamp_checkbox.setToolTip("При включении все сообщения лога будут помечены временем.")
    window.timestamp_checkbox.stateChanged.connect(window.on_toggle_log_timestamps)
    layout.addWidget(window.timestamp_checkbox)

    window.auto_open_output_checkbox = QCheckBox("Автоматически открывать папку результата после успешной обработки")
    window.auto_open_output_checkbox.setToolTip("После удачной обработки BOM-файлов будет автоматически открыт проводник с результатом.")
    window.auto_open_output_checkbox.stateChanged.connect(window.on_toggle_auto_open_output)
    layout.addWidget(window.auto_open_output_checkbox)

    group.setLayout(layout)
    group.setVisible(False)
    return group


def create_footer(window: 'BOMCategorizerMainWindow') -> QWidget:
    """Создает футер с информацией"""
    footer = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(3, 3, 3, 3)

    # Информация о разработчике
    dev_layout = QHBoxLayout()

    dev_label = QLabel("Разработчик: Куреин М.Н.")
    dev_label.setProperty("class", "bold")
    dev_label.mouseDoubleClickEvent = lambda event: window.on_developer_double_click()
    dev_layout.addWidget(dev_label)

    dev_layout.addStretch()

    date_label = QLabel(f"Дата: {window.cfg.get('app_info', {}).get('release_date', 'N/A')}")
    dev_layout.addWidget(date_label)

    layout.addLayout(dev_layout)

    # Информация о БД и размере окна
    info_layout = QHBoxLayout()

    # БД статистика
    try:
        stats = get_database_stats()
        metadata = stats.get('metadata', {})
        db_version = metadata.get('version', 'N/A')
        last_updated = metadata.get('last_updated', '')
        total_components = stats.get('total', 0)
        
        # Форматируем дату для отображения
        if last_updated and last_updated != 'N/A':
            try:
                date_part = last_updated.split()[0]
                version_text = f"{db_version} ({date_part})"
            except:
                version_text = db_version
        else:
            version_text = db_version
        
        window.db_info_label = QLabel(f"БД: {version_text} ({total_components} компонентов)")
        
        # Добавляем tooltip с историей
        window.update_database_tooltip()
        
        # Делаем метку кликабельной
        window.db_info_label.setCursor(Qt.PointingHandCursor)
        window.db_info_label.mousePressEvent = lambda event: window.on_view_database()
    except Exception:
        window.db_info_label = QLabel("БД: Не загружена")

    info_layout.addWidget(window.db_info_label)

    # Индикатор режима
    window.mode_label = QLabel()
    window.mode_label.setStyleSheet("QLabel { color: #a6e3a1; font-weight: bold; }")
    info_layout.addWidget(window.mode_label)

    info_layout.addStretch()

    # Информация о расположении (кликабельная метка)
    db_path = get_database_path()
    if "%APPDATA%" in db_path or "AppData" in db_path:
        location_label = QLabel("Установка (%APPDATA%)")
        location_label.setStyleSheet("QLabel { color: #89b4fa; font-weight: bold; } QLabel:hover { color: #74c7ec; }")
    else:
        location_label = QLabel("Локальная")
        location_label.setStyleSheet("QLabel { color: #f9e2af; font-weight: bold; } QLabel:hover { color: #f9e2af; }")
    
    location_label.setCursor(Qt.PointingHandCursor)
    location_label.setToolTip("Нажмите для открытия папки с выделенным файлом базы данных")
    location_label.mousePressEvent = lambda event: window.on_open_db_folder()
    info_layout.addWidget(location_label)

    # Размер окна (кликабельная метка)
    window.size_label = QLabel(f"📐 {window.width()}×{window.height()}")
    window.size_label.setStyleSheet("QLabel { color: #89b4fa; font-weight: bold; } QLabel:hover { color: #74c7ec; }")
    window.size_label.setCursor(Qt.PointingHandCursor)
    window.size_label.mousePressEvent = lambda event: window.on_show_size_menu(event)
    info_layout.addWidget(window.size_label)

    layout.addLayout(info_layout)

    footer.setLayout(layout)
    return footer

