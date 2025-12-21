# -*- coding: utf-8 -*-
"""
Модуль управления масштабированием и темами

Содержит функции для:
- Применения масштаба интерфейса
- Переключения тем
- Управления режимами просмотра
"""

import os
import json
import platform
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction, QShortcut, QKeySequence

if TYPE_CHECKING:
    from .main_window import BOMCategorizerMainWindow

from ..styles import DARK_THEME, LIGHT_THEME

# Import from shared module to avoid duplication
from ..shared.fonts import get_system_font



def apply_theme(window: 'BOMCategorizerMainWindow') -> None:
    """Применяет выбранную тему к приложению"""
    if window.current_theme == "dark":
        window.setStyleSheet(DARK_THEME)
    else:
        window.setStyleSheet(LIGHT_THEME)


def toggle_theme(window: 'BOMCategorizerMainWindow') -> None:
    """Переключает между темной и светлой темой"""
    window.current_theme = "light" if window.current_theme == "dark" else "dark"
    apply_theme(window)
    save_ui_preferences(window)
    
    theme_name = "Темная" if window.current_theme == "dark" else "Светлая"
    QMessageBox.information(
        window,
        "Тема изменена",
        f"{theme_name} тема применена успешно!"
    )


def register_zoom_shortcuts(window: 'BOMCategorizerMainWindow') -> None:
    """Создает (или пересоздает) горячие клавиши для изменения масштаба."""
    # Удаляем старые
    for shortcut in window.zoom_shortcuts:
        if shortcut:
            shortcut.setParent(None)
    window.zoom_shortcuts.clear()

    def create_shortcut(sequence, handler):
        try:
            shortcut = QShortcut(QKeySequence(sequence), window)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(handler)
            window.zoom_shortcuts.append(shortcut)
        except Exception as e:
            print(f"Ошибка создания шортката {sequence}: {e}")

    # Увеличение масштаба
    zoom_in_sequences = [
        QKeySequence.ZoomIn,
        "Ctrl++",
        "Ctrl+=",
        "Ctrl+Shift+="
    ]
    
    # Уменьшение масштаба
    zoom_out_sequences = [
        QKeySequence.ZoomOut,
        "Ctrl+-",
        "Ctrl+Minus",
        "Ctrl+_",
        "Ctrl+Shift+-"
    ]

    for seq in zoom_in_sequences:
        create_shortcut(seq, window.on_zoom_in)
    for seq in zoom_out_sequences:
        create_shortcut(seq, window.on_zoom_out)
    create_shortcut("Ctrl+0", window.reset_scale)


def apply_scale_factor(window: 'BOMCategorizerMainWindow') -> None:
    """Применяет текущий коэффициент масштабирования"""
    font_size = max(8, int(round(window.base_font_size * window.scale_factor)))
    font = QFont(get_system_font(), font_size)
    
    # Сохраняем текущий размер окна
    current_size = window.size()
    
    # Применяем масштаб глобально через QApplication
    if window.app:
        window.app.setFont(font)
    
    # Применяем к главному окну
    window.setFont(font)
    
    # Применяем к меню
    menubar = window.menuBar()
    if menubar:
        menubar.setFont(font)
        for action in menubar.actions():
            menu = action.menu()
            if menu:
                menu.setFont(font)
                for menu_action in menu.actions():
                    if menu_action:
                        menu_action.setFont(font)
                        submenu = menu_action.menu()
                        if submenu:
                            submenu.setFont(font)
                            for submenu_action in submenu.actions():
                                if submenu_action:
                                    submenu_action.setFont(font)
    
    # Применяем рекурсивно ко всем дочерним виджетам
    _apply_font_recursive(window, font)
    
    # Обновляем размеры виджетов
    _update_widget_sizes(window)
    
    # НЕ масштабируем размер окна - используем размер из config как есть!
    # Размер окна должен задаваться пользователем явно в config_qt.json
    # и НЕ пересчитываться автоматически при изменении scale_factor
    
    # Принудительно обновляем все виджеты
    window.update()
    window.repaint()
    if menubar:
        menubar.update()
        menubar.repaint()
    
    central_widget = window.centralWidget()
    if central_widget:
        central_widget.updateGeometry()
        central_widget.update()
        central_widget.repaint()
        for child in central_widget.findChildren(QWidget):
            try:
                child.repaint()
            except (RuntimeError, AttributeError, TypeError):
                continue
    
    update_scale_actions(window)


def _apply_font_recursive(widget, font):
    """Рекурсивно применяет шрифт ко всем дочерним виджетам"""
    current_font = widget.font()
    if current_font.family() != font.family() and current_font.family() != get_system_font():
        current_font.setPointSize(font.pointSize())
        widget.setFont(current_font)
    else:
        widget.setFont(font)
    
    for child in widget.findChildren(QWidget):
        try:
            child_font = child.font()
            if child_font.family() != font.family() and child_font.family() != get_system_font():
                child_font.setPointSize(font.pointSize())
                child.setFont(child_font)
            else:
                child.setFont(font)
        except (RuntimeError, AttributeError):
            continue
    
    try:
        for action in widget.findChildren(QAction):
            try:
                action_font = action.font()
                if action_font.family() != font.family() and action_font.family() != get_system_font():
                    action_font.setPointSize(font.pointSize())
                    action.setFont(action_font)
                else:
                    action.setFont(font)
            except (RuntimeError, AttributeError):
                continue
    except (RuntimeError, AttributeError):
        pass


def _update_widget_sizes(window):
    """Обновляет размеры виджетов в соответствии с масштабом"""
    base_sizes = {
        'files_list_height': 100,
        'log_text_height': 160,
    }
    
    if hasattr(window, 'files_list') and window.files_list:
        scaled_height = int(base_sizes['files_list_height'] * window.scale_factor)
        window.files_list.setMaximumHeight(scaled_height)
    
    if hasattr(window, 'log_text') and window.log_text:
        scaled_height = int(base_sizes['log_text_height'] * window.scale_factor)
        window.log_text.setMaximumHeight(scaled_height)


def update_scale_actions(window: 'BOMCategorizerMainWindow') -> None:
    """Обновляет состояние пунктов меню масштаба"""
    if not window.scale_actions:
        return
    for factor, action in window.scale_actions.items():
        if action is None:
            continue
        blocked = action.blockSignals(True)
        action.setChecked(abs(window.scale_factor - factor) < 0.001)
        action.blockSignals(blocked)


def set_scale_factor(window: 'BOMCategorizerMainWindow', factor: float) -> None:
    """Устанавливает масштаб интерфейса"""
    if factor not in window.scale_levels:
        factor = min(window.scale_levels, key=lambda x: abs(x - factor))
    if abs(window.scale_factor - factor) < 0.001:
        update_scale_actions(window)
        return
    window.scale_factor = factor
    apply_scale_factor(window)
    save_ui_preferences(window)


def on_zoom_in(window: 'BOMCategorizerMainWindow') -> None:
    """Увеличивает масштаб интерфейса"""
    print("🔍 Zoom In вызван")
    index = _current_scale_index(window)
    if index < len(window.scale_levels) - 1:
        new_scale = window.scale_levels[index + 1]
        print(f"   Изменение масштаба: {window.scale_factor*100:.0f}% -> {new_scale*100:.0f}%")
        set_scale_factor(window, new_scale)
        QApplication.processEvents()
    else:
        print(f"   Уже максимальный масштаб: {window.scale_factor*100:.0f}%")


def on_zoom_out(window: 'BOMCategorizerMainWindow') -> None:
    """Уменьшает масштаб интерфейса"""
    print("🔍 Zoom Out вызван")
    index = _current_scale_index(window)
    if index > 0:
        new_scale = window.scale_levels[index - 1]
        print(f"   Изменение масштаба: {window.scale_factor*100:.0f}% -> {new_scale*100:.0f}%")
        set_scale_factor(window, new_scale)
        QApplication.processEvents()
    else:
        print(f"   Уже минимальный масштаб: {window.scale_factor*100:.0f}%")


def reset_scale(window: 'BOMCategorizerMainWindow') -> None:
    """Сбрасывает масштаб на значение по умолчанию"""
    set_scale_factor(window, 0.8)


def _current_scale_index(window: 'BOMCategorizerMainWindow') -> int:
    """Возвращает индекс текущего масштаба"""
    if window.scale_factor in window.scale_levels:
        return window.scale_levels.index(window.scale_factor)
    closest = min(range(len(window.scale_levels)), key=lambda i: abs(window.scale_levels[i] - window.scale_factor))
    window.scale_factor = window.scale_levels[closest]
    return closest


def apply_view_mode(window: 'BOMCategorizerMainWindow', initial: bool = False) -> None:
    """Применяет текущий режим просмотра"""
    simple = window.current_view_mode == "simple"
    expert = window.current_view_mode == "expert"

    if hasattr(window, "comparison_section") and window.comparison_section:
        window.comparison_section.setVisible(not simple)
    if hasattr(window, "log_section") and window.log_section:
        window.log_section.setVisible(not simple)
    if hasattr(window, "expert_section") and window.expert_section:
        window.expert_section.setVisible(expert)

    # Скрываем меню БД в простом режиме
    from shiboken6 import isValid
    if window.db_menu is not None and isValid(window.db_menu):
        action = window.db_menu.menuAction()
        if action:
            action.setVisible(not simple)

    if window.mode_label is not None:
        mode_titles = {
            "simple": ("Режим: Простой", "#fab387"),
            "advanced": ("Режим: Расширенный", "#89b4fa"),
            "expert": ("Режим: Эксперт", "#f38ba8"),
        }
        text, color = mode_titles.get(window.current_view_mode, ("Режим: Неизвестно", "#cdd6f4"))
        window.mode_label.setText(text)
        window.mode_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")

    if window.timestamp_checkbox is not None:
        window.timestamp_checkbox.blockSignals(True)
        window.timestamp_checkbox.setEnabled(expert)
        window.timestamp_checkbox.setChecked(window.log_with_timestamps if expert else False)
        window.timestamp_checkbox.blockSignals(False)

    if window.auto_open_output_checkbox is not None:
        window.auto_open_output_checkbox.blockSignals(True)
        window.auto_open_output_checkbox.setEnabled(expert)
        window.auto_open_output_checkbox.setChecked(window.auto_open_output if expert else False)
        window.auto_open_output_checkbox.blockSignals(False)

    update_view_mode_actions(window)

    if not initial:
        save_ui_preferences(window)


def update_view_mode_actions(window: 'BOMCategorizerMainWindow') -> None:
    """Обновляет состояние пунктов меню режима просмотра"""
    if not window.view_mode_actions:
        return
    for key, action in window.view_mode_actions.items():
        blocked = action.blockSignals(True)
        action.setChecked(key == window.current_view_mode)
        action.blockSignals(blocked)


def set_view_mode(window: 'BOMCategorizerMainWindow', mode: str) -> None:
    """Устанавливает режим просмотра"""
    if mode not in ("simple", "advanced", "expert"):
        return
    if mode == window.current_view_mode:
        update_view_mode_actions(window)
        return
    window.current_view_mode = mode
    if mode != "expert":
        window.log_with_timestamps = False
        window.auto_open_output = False
    apply_view_mode(window)


def save_ui_preferences(window: 'BOMCategorizerMainWindow') -> None:
    """Сохраняет настройки интерфейса"""
    try:
        from ..shared.config import get_config_path
        
        if "ui" not in window.cfg:
            window.cfg["ui"] = {}
        ui_settings = window.cfg["ui"]
        ui_settings["theme"] = window.current_theme
        ui_settings["scale_factor"] = round(window.scale_factor, 2)
        # view_mode НЕ сохраняется - всегда используется из config_qt.json
        ui_settings["log_timestamps"] = bool(window.log_with_timestamps if window.current_view_mode == "expert" else False)
        ui_settings["auto_open_output"] = bool(window.auto_open_output if window.current_view_mode == "expert" else False)

        # Используем ту же логику определения пути, что и load_config()
        cfg_path = get_config_path()
        
        # Загружаем текущий конфиг, чтобы сохранить все остальные настройки
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                full_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            full_config = window.cfg.copy()
        
        # Обновляем только секцию ui
        full_config["ui"] = ui_settings
        # Сохраняем остальные секции из window.cfg
        for key, value in window.cfg.items():
            if key != "ui":
                full_config[key] = value
        
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(full_config, f, indent=2, ensure_ascii=False)
        
        # Обновляем конфиг в памяти
        window.cfg = full_config
    except Exception as e:
        print(f"Не удалось сохранить настройки интерфейса: {e}")

