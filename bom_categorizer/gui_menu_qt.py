# -*- coding: utf-8 -*-
"""
Модуль создания меню для GUI

Содержит функции для создания меню приложения
"""

from typing import TYPE_CHECKING, Dict
from PySide6.QtWidgets import QMenuBar, QMenu, QWidgetAction, QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence

if TYPE_CHECKING:
    from .gui_qt import BOMCategorizerMainWindow


def create_menu_bar(window: 'BOMCategorizerMainWindow') -> None:
    """Создает меню приложения"""
    menubar = window.menuBar()
    
    _create_file_menu(window, menubar)
    _create_view_menu(window, menubar)
    _create_database_menu(window, menubar)
    _create_help_menu(window, menubar)
    _add_global_search_menu(window, menubar)


def _create_file_menu(window: 'BOMCategorizerMainWindow', menubar: QMenuBar) -> None:
    """Создает меню 'Файл'"""
    file_menu = menubar.addMenu("Файл")
    
    # Открыть файлы
    open_action = QAction("📂 Открыть файлы", window)
    open_action.setShortcut(QKeySequence("Ctrl+O"))
    open_action.triggered.connect(window.on_add_files)
    file_menu.addAction(open_action)
    
    file_menu.addSeparator()
    
    # Запустить обработку
    run_action = QAction("🚀 Запустить обработку", window)
    run_action.setShortcut(QKeySequence("Ctrl+R"))
    run_action.triggered.connect(window.on_run)
    file_menu.addAction(run_action)
    
    file_menu.addSeparator()
    
    # Выход
    exit_action = QAction("🚪 Выход", window)
    exit_action.setShortcut(QKeySequence("Ctrl+Q"))
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)


def _create_view_menu(window: 'BOMCategorizerMainWindow', menubar: QMenuBar) -> None:
    """Создает меню 'Вид'"""
    view_menu = menubar.addMenu("Вид")
    
    # Подменю масштаба
    scale_menu = view_menu.addMenu("Масштабирование интерфейса")
    scale_group = QActionGroup(window)
    scale_group.setExclusive(True)

    scale_labels = {
        0.7: "Масштаб 70%",
        0.8: "Масштаб 80% (по умолчанию)",
        0.9: "Масштаб 90%",
        1.0: "Масштаб 100%",
        1.1: "Масштаб 110%",
        1.25: "Масштаб 125%",
    }

    window.scale_actions.clear()
    for factor in window.scale_levels:
        label = scale_labels.get(factor, f"Масштаб {int(factor * 100)}%")
        action = QAction(label, window)
        action.setCheckable(True)
        action.triggered.connect(lambda checked, f=factor: window.set_scale_factor(f))
        scale_menu.addAction(action)
        scale_group.addAction(action)
        window.scale_actions[factor] = action

    view_menu.addSeparator()

    zoom_in_action = QAction("Увеличить масштаб (Ctrl++)", window)
    zoom_in_action.triggered.connect(window.on_zoom_in)
    view_menu.addAction(zoom_in_action)

    zoom_out_action = QAction("Уменьшить масштаб (Ctrl+-)", window)
    zoom_out_action.triggered.connect(window.on_zoom_out)
    view_menu.addAction(zoom_out_action)

    reset_zoom_action = QAction("Сбросить масштаб (Ctrl+0)", window)
    reset_zoom_action.triggered.connect(window.reset_scale)
    view_menu.addAction(reset_zoom_action)

    view_menu.addSeparator()

    # Подменю режимов работы
    mode_menu = view_menu.addMenu("Режим работы")
    mode_group = QActionGroup(window)
    mode_group.setExclusive(True)

    mode_definitions = [
        ("simple", "Простой режим"),
        ("advanced", "Расширенный режим (все функции)"),
        ("expert", "Экспертный режим (дополнительные настройки)"),
    ]

    window.view_mode_actions.clear()
    for key, label in mode_definitions:
        action = QAction(label, window)
        action.setCheckable(True)
        action.triggered.connect(lambda checked, m=key: window.set_view_mode(m))
        mode_menu.addAction(action)
        mode_group.addAction(action)
        window.view_mode_actions[key] = action

    view_menu.addSeparator()

    # Пункт переключения темы
    theme_action = QAction("🌓 Переключить тему", window)
    theme_action.setShortcut("Ctrl+T")
    theme_action.triggered.connect(window.toggle_theme)
    view_menu.addAction(theme_action)


def _create_database_menu(window: 'BOMCategorizerMainWindow', menubar: QMenuBar) -> None:
    """Создает меню 'База данных'"""
    window.db_menu = menubar.addMenu("База данных")
    
    # Статистика БД
    stats_action = QAction("📊 Статистика", window)
    stats_action.triggered.connect(window.show_database_stats)
    window.db_menu.addAction(stats_action)
    
    # Экспорт БД
    export_action = QAction("📤 Экспорт в Excel", window)
    export_action.triggered.connect(window.export_database)
    window.db_menu.addAction(export_action)
    
    # Импорт БД
    import_action = QAction("📥 Импорт из Excel", window)
    import_action.triggered.connect(window.import_database)
    window.db_menu.addAction(import_action)
    
    window.db_menu.addSeparator()
    
    # Резервное копирование
    backup_action = QAction("💾 Резервное копирование", window)
    backup_action.triggered.connect(window.backup_database)
    window.db_menu.addAction(backup_action)
    
    # Открыть папку БД
    folder_action = QAction("📁 Открыть папку БД", window)
    folder_action.triggered.connect(window.open_database_folder)
    window.db_menu.addAction(folder_action)
    
    window.db_menu.addSeparator()
    
    # Посмотреть базу
    view_action = QAction("👁️ Посмотреть базу", window)
    view_action.triggered.connect(window.on_view_database)
    window.db_menu.addAction(view_action)
    
    # Изменить версию БД
    version_action = QAction("🔢 Изменить версию БД", window)
    version_action.triggered.connect(window.on_change_database_version)
    window.db_menu.addAction(version_action)
    
    # Очистить базу данных
    clear_action = QAction("🗑️ Очистить базу данных", window)
    clear_action.triggered.connect(window.on_clear_database)
    window.db_menu.addAction(clear_action)
    
    window.db_menu.addSeparator()
    
    # Заменить БД
    replace_action = QAction("🔄 Заменить БД", window)
    replace_action.triggered.connect(window.on_replace_database)
    window.db_menu.addAction(replace_action)
    
    # Добавить все из выходного файла
    import_output_action = QAction("📋 Добавить из выходного файла", window)
    import_output_action.triggered.connect(window.on_import_from_output)
    window.db_menu.addAction(import_output_action)


def _create_help_menu(window: 'BOMCategorizerMainWindow', menubar: QMenuBar) -> None:
    """Создает меню 'Помощь'"""
    help_menu = menubar.addMenu("Помощь")
    
    # Контекстная помощь
    context_help_action = QAction("❓ Контекстная помощь", window)
    context_help_action.setShortcut(QKeySequence("F1"))
    context_help_action.triggered.connect(window.show_context_help)
    help_menu.addAction(context_help_action)
    
    # База знаний
    knowledge_base_action = QAction("📚 База знаний", window)
    knowledge_base_action.triggered.connect(window.show_knowledge_base)
    help_menu.addAction(knowledge_base_action)
    
    help_menu.addSeparator()
    
    # О программе
    about_action = QAction("ℹ️ О программе", window)
    about_action.triggered.connect(window.show_about)
    help_menu.addAction(about_action)
    
    # Системная информация
    system_info_action = QAction("💻 Системная информация", window)
    system_info_action.triggered.connect(window.show_system_info)
    help_menu.addAction(system_info_action)


def _add_global_search_menu(window: 'BOMCategorizerMainWindow', menubar: QMenuBar) -> None:
    """Добавляет меню 'Поиск' с выпадающим виджетом поиска."""
    if window.global_search_input is not None:
        return  # Поиск уже добавлен

    # Создаем меню "Поиск"
    search_menu = menubar.addMenu("🔍 Поиск")

    # Создаем виджет для выпадающего меню
    search_widget = QWidget()
    search_widget.setObjectName("globalSearchWidget")
    search_widget.setFixedWidth(300)

    layout = QHBoxLayout(search_widget)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    # Поле ввода
    line_edit = QLineEdit()
    line_edit.setObjectName("globalSearchInput")
    line_edit.setPlaceholderText("Введите название ИВП или ключевое слово...")
    line_edit.setClearButtonEnabled(True)
    line_edit.setMinimumWidth(200)

    # Кнопка поиска с лупой
    search_button = QPushButton("🔎")
    search_button.setObjectName("globalSearchButton")
    search_button.setCursor(Qt.PointingHandCursor)
    search_button.setToolTip("Найти (Enter)")
    search_button.setFixedSize(32, 32)

    layout.addWidget(line_edit)
    layout.addWidget(search_button)

    # Создаем действие с виджетом
    search_action = QWidgetAction(window)
    search_action.setDefaultWidget(search_widget)
    search_menu.addAction(search_action)

    # Сохраняем ссылку на поле ввода
    window.global_search_input = line_edit

    # Подключаем сигналы
    search_button.clicked.connect(window.on_global_search_triggered)
    line_edit.returnPressed.connect(window.on_global_search_triggered)

