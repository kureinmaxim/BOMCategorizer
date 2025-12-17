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
    from .main_window import BOMCategorizerMainWindow

from ..component_database import get_database_stats, get_database_path


def create_main_section(window: 'BOMCategorizerMainWindow') -> QGroupBox:
    """Создает секцию основных настроек"""
    group = QGroupBox("Основные настройки")
    layout = QVBoxLayout()

    # Кнопки управления файлами - теперь две отдельные кнопки
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(8)

    add_bom_btn = QPushButton("➕ Добавить BOM файлы")
    add_bom_btn.setToolTip("Добавить BOM файлы для обработки (F1 - справка)")
    add_bom_btn.setMinimumHeight(32)
    add_bom_btn.clicked.connect(window.on_add_files)
    window.lockable_widgets.append(add_bom_btn)
    buttons_layout.addWidget(add_bom_btn, 1)

    clear_btn = QPushButton("🗑️ Очистить")
    clear_btn.setProperty("class", "danger")
    clear_btn.setMinimumHeight(32)
    clear_btn.clicked.connect(window.on_clear_files)
    window.lockable_widgets.append(clear_btn)
    buttons_layout.addWidget(clear_btn, 1)
    
    # Кнопка CLI - в середине между BOM и ТРУ/РКМ
    open_cli_button = QPushButton("💻 CLI")
    open_cli_button.setObjectName("openCliButton")
    open_cli_button.setToolTip(
        "Открыть интерактивную командную строку:\n"
        "• Выполнение команд для обработки файлов\n"
        "• Управление базой данных через CLI\n"
        "• Синхронизация версий и API\n"
        "• Автодополнение и история команд"
    )
    open_cli_button.setMinimumHeight(32)
    open_cli_button.setStyleSheet("""
        QPushButton {
            background-color: #0f2744;
            color: white;
            border: 1px solid #1e3a5f;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #1a3352;
            border-color: #3d5a80;
        }
        QPushButton:pressed {
            background-color: #081830;
        }
    """)
    open_cli_button.clicked.connect(window.open_interactive_cli)
    buttons_layout.addWidget(open_cli_button, 1)
    
    # Кнопки для ТРУ/РКМ файлов
    add_tru_btn = QPushButton("➕ Добавить ТРУ/РКМ")
    add_tru_btn.setToolTip("Добавить файлы ТРУ и РКМ (только .xls)")
    add_tru_btn.setMinimumHeight(32)
    add_tru_btn.clicked.connect(window.on_add_tru_rkm_files)
    window.lockable_widgets.append(add_tru_btn)
    buttons_layout.addWidget(add_tru_btn, 1)

    clear_tru_btn = QPushButton("🗑️ Очистить")
    clear_tru_btn.setProperty("class", "danger")
    clear_tru_btn.setMinimumHeight(32)
    clear_tru_btn.clicked.connect(window.on_clear_tru_rkm_files)
    window.lockable_widgets.append(clear_tru_btn)
    buttons_layout.addWidget(clear_tru_btn, 1)

    layout.addLayout(buttons_layout)

    # Два списка файлов рядом - разделены пополам
    files_row_layout = QHBoxLayout()
    files_row_layout.setSpacing(10)
    
    # Левая половина - входные BOM файлы
    left_files_widget = QWidget()
    left_files_widget.setMinimumHeight(130)  # Фиксированная высота для всего блока
    left_files_widget.setMaximumHeight(130)
    left_files_layout = QVBoxLayout(left_files_widget)
    left_files_layout.setContentsMargins(0, 0, 0, 0)
    left_files_layout.setSpacing(5)
    
    files_label = QLabel("Входные файлы:")
    files_label.setProperty("class", "bold")
    files_label.setFixedHeight(20)  # Фиксированная высота для label
    left_files_layout.addWidget(files_label)

    window.files_list = QListWidget()
    window.files_list.setMinimumHeight(100)
    window.files_list.setMaximumHeight(100)
    window.files_list.itemSelectionChanged.connect(window.on_file_selected)
    window.lockable_widgets.append(window.files_list)
    left_files_layout.addWidget(window.files_list)
    
    files_row_layout.addWidget(left_files_widget, 1)
    
    # Правая половина - файлы ТРУ и РКМ (идентичные размеры)
    right_files_widget = QWidget()
    right_files_widget.setMinimumHeight(130)  # Такая же высота как у левой
    right_files_widget.setMaximumHeight(130)
    right_files_layout = QVBoxLayout(right_files_widget)
    right_files_layout.setContentsMargins(0, 0, 0, 0)
    right_files_layout.setSpacing(5)
    
    tru_rkm_label = QLabel("Файлы ТРУ и РКМ:")
    tru_rkm_label.setProperty("class", "bold")
    tru_rkm_label.setFixedHeight(20)  # Такая же высота как у label слева
    right_files_layout.addWidget(tru_rkm_label)

    window.tru_rkm_files_list = QListWidget()
    window.tru_rkm_files_list.setMinimumHeight(100)
    window.tru_rkm_files_list.setMaximumHeight(100)
    window.lockable_widgets.append(window.tru_rkm_files_list)
    right_files_layout.addWidget(window.tru_rkm_files_list)
    
    files_row_layout.addWidget(right_files_widget, 1)
    
    layout.addLayout(files_row_layout)

    # Grid layout для выровненных полей
    grid = QGridLayout()
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(10)
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
    window.multiplier_spin.setMinimum(0)
    window.multiplier_spin.setMaximum(999)
    window.multiplier_spin.setValue(1)
    window.multiplier_spin.setMaximumWidth(80)
    window.multiplier_spin.setMinimumHeight(32)  # Увеличиваем высоту для больших стрелок
    window.multiplier_spin.setAlignment(Qt.AlignCenter)  # Выравнивание по центру
    # Дополнительные стили для лучшего отображения
    window.multiplier_spin.setStyleSheet("""
        QSpinBox {
            padding: 4px 8px;
            text-align: center;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            width: 20px;
            subcontrol-origin: border;
        }
        QSpinBox::up-arrow {
            width: 12px;
            height: 12px;
        }
        QSpinBox::down-arrow {
            width: 12px;
            height: 12px;
        }
    """)
    window.multiplier_spin.setToolTip("Количество экземпляров (0 для удаления)")
    window.lockable_widgets.append(window.multiplier_spin)
    mult_layout.addWidget(window.multiplier_spin)

    apply_mult_btn = QPushButton("Применить")
    apply_mult_btn.setFixedWidth(100)
    apply_mult_btn.clicked.connect(window.on_multiplier_changed)
    window.lockable_widgets.append(apply_mult_btn)
    mult_layout.addWidget(apply_mult_btn)
    
    # Добавляем разделитель
    separator = QLabel("|")
    separator.setStyleSheet("color: #666; font-size: 16px;")
    mult_layout.addWidget(separator)
    
    # Чекбокс "исключая подбор" в той же строке
    window.exclude_podbor_checkbox = QCheckBox("Исключить подборы")
    window.exclude_podbor_checkbox.setToolTip(
        "В выходном файле не будут учитываться ИВП по замене и подбору"
    )
    window.lockable_widgets.append(window.exclude_podbor_checkbox)
    mult_layout.addWidget(window.exclude_podbor_checkbox)

    mult_layout.addStretch()

    grid.addWidget(mult_widget, row, 1)
    row += 1

    # Листы Excel - уменьшенная ширина
    label = QLabel("Листы (через запятую):")
    label.setMinimumWidth(180)
    grid.addWidget(label, row, 0, Qt.AlignLeft)

    # Создаем виджет для поля ввода с ограниченной шириной
    sheet_widget = QWidget()
    sheet_layout = QHBoxLayout(sheet_widget)
    sheet_layout.setContentsMargins(0, 0, 0, 0)
    
    window.sheet_entry = QLineEdit()
    window.sheet_entry.setPlaceholderText("Оставьте пустым для всех листов")
    window.sheet_entry.setMaximumWidth(450)  # Ограничиваем ширину
    window.lockable_widgets.append(window.sheet_entry)
    sheet_layout.addWidget(window.sheet_entry)
    sheet_layout.addStretch()  # Растягиваемое пространство справа
    
    grid.addWidget(sheet_widget, row, 1)
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

    # Кнопки запуска (такой же стиль как верхний ряд)
    action_layout = QHBoxLayout()
    action_layout.setSpacing(8)

    run_btn = QPushButton("▶️ Запустить обработку")
    run_btn.setProperty("class", "accent")
    run_btn.setMinimumHeight(32)
    run_btn.clicked.connect(window.on_run)
    window.lockable_widgets.append(run_btn)
    action_layout.addWidget(run_btn, 1)

    interactive_btn = QPushButton("🔄 Ручной режим")
    interactive_btn.setMinimumHeight(32)
    interactive_btn.setToolTip("Интерактивная классификация компонентов вручную")
    interactive_btn.clicked.connect(window.on_interactive_classify)
    window.lockable_widgets.append(interactive_btn)
    action_layout.addWidget(interactive_btn, 1)

    export_pdf_button = QPushButton("📄 Экспорт в PDF")
    export_pdf_button.setObjectName("exportPdfButton")
    export_pdf_button.setMinimumHeight(32)
    export_pdf_button.clicked.connect(window.export_last_result_to_pdf)
    export_pdf_button.setToolTip(
        "Конвертирует выходной Excel файл в PDF документ:\n"
        "• Сохранение таблиц и форматирования\n"
        "• Титульная страница со сводкой\n"
        "• Удобно для печати и отправки"
    )
    export_pdf_button.setStyleSheet("""
        QPushButton {
            background-color: #5c1f3d;
            color: white;
            border: 1px solid #7a2d52;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #7a2d52;
            border-color: #a04d76;
        }
        QPushButton:pressed {
            background-color: #3d1428;
        }
        QPushButton:disabled {
            background-color: #6c7086;
            color: #45475a;
        }
    """)
    window.lockable_widgets.append(export_pdf_button)
    action_layout.addWidget(export_pdf_button, 1)

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

    # Чекбокс суммарной комплектации
    window.combine_check = QCheckBox("Суммарная комплектация")
    window.combine_check.setChecked(window.combine)
    window.combine_check.stateChanged.connect(window.on_toggle_combine)
    window.lockable_widgets.append(window.combine_check)
    layout.addWidget(window.combine_check)

    window.timestamp_checkbox = QCheckBox("Добавлять временные метки в лог")
    window.timestamp_checkbox.setToolTip("При включении все сообщения лога будут помечены временем.")
    window.timestamp_checkbox.stateChanged.connect(window.on_toggle_log_timestamps)
    layout.addWidget(window.timestamp_checkbox)

    window.auto_open_output_checkbox = QCheckBox("Автоматически открывать папку результата после успешной обработки")
    window.auto_open_output_checkbox.setToolTip("После удачной обработки BOM-файлов будет автоматически открыт проводник с результатом.")
    window.auto_open_output_checkbox.stateChanged.connect(window.on_toggle_auto_open_output)
    layout.addWidget(window.auto_open_output_checkbox)
    
    # Опция автоматического экспорта в PDF
    window.auto_export_pdf_checkbox = QCheckBox("Автоматически создавать PDF после обработки")
    window.auto_export_pdf_checkbox.setToolTip("После успешной обработки автоматически создается PDF версия результата")
    window.auto_export_pdf_checkbox.stateChanged.connect(window.on_toggle_auto_pdf_export)
    layout.addWidget(window.auto_export_pdf_checkbox)
    
    # Разделитель
    layout.addWidget(QLabel("<hr>"))
    
    # AI-подсказки для классификации
    ai_header_layout = QHBoxLayout()
    ai_label = QLabel("🤖 AI-подсказки для классификации:")
    ai_label.setToolTip(
        "Интеграция с LLM для автоматической классификации неизвестных компонентов:\n"
        "• Использует Claude, GPT или локальный Ollama\n"
        "• Предлагает категории для новых компонентов\n"
        "• Объясняет выбор категории\n"
        "• Работает в интерактивном режиме"
    )
    ai_label.setProperty("class", "bold")
    ai_header_layout.addWidget(ai_label)
    ai_header_layout.addStretch()
    layout.addLayout(ai_header_layout)
    
    # Чекбокс включения AI-подсказок
    window.ai_classifier_checkbox = QCheckBox("Включить AI-подсказки при интерактивной классификации")
    window.ai_classifier_checkbox.setToolTip(
        "При включении в интерактивном режиме будет доступна кнопка 'AI-подсказка':\n"
        "• Автоматическое предложение категории через LLM\n"
        "• Объяснение выбора\n"
        "• Уровень уверенности (high/medium/low)\n"
        "• Требуется API ключ для выбранного провайдера"
    )
    window.ai_classifier_checkbox.stateChanged.connect(window.on_toggle_ai_classifier)
    layout.addWidget(window.ai_classifier_checkbox)
    
    # Опция автоматической классификации
    window.ai_auto_classify_checkbox = QCheckBox("Автоматически классифицировать все неизвестные компоненты через AI")
    window.ai_auto_classify_checkbox.setToolTip(
        "⚠️ Экспериментально! При включении ВСЕ неизвестные компоненты будут автоматически\n"
        "отправлены на классификацию через AI без интерактивного запроса.\n"
        "Требует API ключа. Может занять много времени и средств при большом количестве компонентов.\n\n"
        "При попытке включить без настроенного AI появится подсказка."
    )
    # Чекбокс всегда активен - если AI не настроен, при клике появится подсказка
    # Используем clicked вместо stateChanged для лучшего контроля
    window.ai_auto_classify_checkbox.clicked.connect(window.on_ai_auto_classify_clicked)
    layout.addWidget(window.ai_auto_classify_checkbox)

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

    from .main_window import get_config_path
    import platform
    config_path = get_config_path()
    db_path = get_database_path()
    
    # Определяем, установленная версия или разработка
    # Для установленной версии конфиг должен быть в системной папке, а не рядом с кодом
    is_installed = False
    if platform.system() == 'Darwin':  # macOS
        # Установленная версия: конфиг в ~/Library/Application Support/
        is_installed = 'Application Support' in config_path and 'BOMCategorizerModern' in config_path
        install_label = "Установка (Application Support)"
    elif platform.system() == 'Windows':
        # Установленная версия: конфиг в %APPDATA%
        is_installed = 'AppData' in config_path or '%APPDATA%' in config_path
        install_label = "Установка (%APPDATA%)"
    else:
        # Linux и другие
        is_installed = '.local' in config_path or '.config' in config_path
        install_label = "Установка (система)"
    
    if is_installed:
        # Для установленной версии Modern Edition открываем папку установки (где config_qt.json)
        location_label = QLabel(install_label)
        location_label.setStyleSheet("QLabel { color: #89b4fa; font-weight: bold; } QLabel:hover { color: #74c7ec; }")
        location_label.setToolTip("Нажмите для открытия папки установки Modern Edition\n(где находится config_qt.json)")
        location_label.mousePressEvent = lambda event: window.on_open_install_folder()
    else:
        # Для режима разработки открываем папку базы данных
        location_label = QLabel("Локальная")
        location_label.setStyleSheet("QLabel { color: #f9e2af; font-weight: bold; } QLabel:hover { color: #f9e2af; }")
        location_label.setToolTip("Нажмите для открытия папки с выделенным файлом базы данных")
        location_label.mousePressEvent = lambda event: window.on_open_db_folder()
    
    location_label.setCursor(Qt.PointingHandCursor)
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

