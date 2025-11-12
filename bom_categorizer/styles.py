# -*- coding: utf-8 -*-

"""
Стили для BOM Categorizer Modern Edition
Темная тема: Catppuccin Macchiato
Светлая тема: Catppuccin Latte
"""

# ===============================
# === ТЕМНАЯ ТЕМА (По умолчанию) ===
# ===============================
DARK_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1e2e; /* Base */
    color: #e0e5ff; /* Brighter Text */
}

/* --- Вкладки --- */
QTabWidget::pane {
    border: 1px solid #45475a; /* Surface2 */
    background-color: #1e1e2e; /* Base */
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #313244; /* Surface1 */
    color: #e0e5ff; /* Brighter Text */
    border: 1px solid #45475a; /* Surface2 */
    padding: 8px 15px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #45475a; /* Surface2 */
    border-bottom-color: #1e1e2e; /* Base */
}

QTabBar::tab:hover:!selected {
    background-color: #585b70; /* Surface2 Hover */
}

/* --- Группы --- */
QGroupBox {
    border: 2px solid #585b70; /* Surface2 - более заметная граница */
    border-radius: 6px;
    margin-top: 1.2em;
    padding: 10px;
    font-weight: bold;
    color: #cba6f7; /* Lavender */
    background-color: #181825; /* Mantle - темнее фона */
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    background-color: #1e1e2e; /* Base */
    border: none;
    color: #cba6f7; /* Bright Lavender */
    font-size: 16pt;
    font-weight: bold;
    letter-spacing: 0.5px;
}

/* --- Кнопки --- */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #45475a, stop:1 #383a4a); /* Gradient */
    color: #e0e5ff; /* Brighter Text */
    border: 2px solid #6c7086; /* Overlay0 */
    border-radius: 5px;
    padding: 5px 12px;
    font-weight: bold;
    font-size: 10pt;
    min-height: 20px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #89b4fa, stop:1 #5a7fda); /* Blue Gradient */
    border: 2px solid #89b4fa; /* Blue */
    color: #ffffff;
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #313244, stop:1 #1e1e2e); /* Dark Gradient */
    border: 2px solid #cba6f7; /* Lavender */
    padding: 7px 13px 5px 15px; /* Эффект нажатия */
}

QPushButton:disabled {
    background-color: #313244; /* Surface1 */
    color: #7f849c; /* Subtext0 */
    border: 2px solid #45475a; /* Surface2 */
}

/* --- Основные кнопки действий (Синие) --- */
QPushButton#processButton, QPushButton#classifyButton, QPushButton#addButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #89b4fa, stop:1 #5a8fea); /* Blue Gradient */
    color: #ffffff; /* White */
    border: 2px solid #89b4fa; /* Blue */
    font-weight: bold;
    font-size: 10pt;
}

QPushButton#processButton:hover, QPushButton#classifyButton:hover, QPushButton#addButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #a6c8ff, stop:1 #89b4fa); /* Brighter Blue Gradient */
    border: 2px solid #b4befe; /* Lavender */
}

QPushButton#processButton:pressed, QPushButton#classifyButton:pressed, QPushButton#addButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #5a8fea, stop:1 #4a7fda); /* Darker Blue Gradient */
    border: 2px solid #74c7ec; /* Sapphire */
}

/* --- Кнопки успеха (Зеленые) --- */
QPushButton#importButton, QPushButton#exportButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #a6e3a1, stop:1 #86d391); /* Green Gradient */
    color: #1e1e2e; /* Base */
    border: 2px solid #a6e3a1; /* Green */
    font-weight: bold;
    font-size: 10pt;
}

QPushButton#importButton:hover, QPushButton#exportButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #b6f3b1, stop:1 #a6e3a1); /* Brighter Green Gradient */
    border: 2px solid #94e2d5; /* Teal */
}

QPushButton#importButton:pressed, QPushButton#exportButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #86d391, stop:1 #76c381); /* Darker Green Gradient */
    border: 2px solid #86d391;
}

/* --- Критические кнопки (Красные) --- */
QPushButton#deleteButton, QPushButton#clearButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #f38ba8, stop:1 #e36b88); /* Red Gradient */
    color: #ffffff; /* White */
    border: 2px solid #f38ba8; /* Red */
    font-weight: bold;
}

QPushButton#deleteButton:hover, QPushButton#clearButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ffabc0, stop:1 #f38ba8); /* Brighter Red Gradient */
    border: 2px solid #eba0ac; /* Red Hover */
}

QPushButton#deleteButton:pressed, QPushButton#clearButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #e36b88, stop:1 #d35b78); /* Darker Red Gradient */
    border: 2px solid #e36b88;
}

/* --- Поля ввода --- */
QLineEdit, QSpinBox {
    background-color: #313244; /* Surface1 */
    color: #e0e5ff; /* Brighter Text */
    border: 2px solid #45475a; /* Surface2 */
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}

QLineEdit:focus, QSpinBox:focus {
    border: 2px solid #cba6f7; /* Lavender */
    background-color: #3a3c4e; /* Lighter Surface1 */
}

QLineEdit:disabled, QSpinBox:disabled {
    background-color: #181825; /* Mantle */
    color: #7f849c; /* Subtext0 */
    border: 2px solid #313244;
}

/* --- Глобальный поиск --- */
QWidget#globalSearchWidget {
    background-color: #181825; /* Mantle */
    border: 2px solid #89b4fa; /* Accent Blue */
    border-radius: 8px;
}

QLineEdit#globalSearchInput {
    background-color: #242438; /* Darker Surface */
    border: 2px solid #89b4fa;
    color: #e0e5ff;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 10pt;
}

QLineEdit#globalSearchInput:focus {
    border: 2px solid #b4befe; /* Lavender */
    background-color: #2f3045;
}

QPushButton#globalSearchButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #89b4fa, stop:1 #5a7fda); /* Blue Gradient */
    color: #ffffff;
    border: 2px solid #89b4fa;
    border-radius: 6px;
    font-weight: bold;
    font-size: 11pt;
    padding: 6px 10px;
}

QPushButton#globalSearchButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #a6c8ff, stop:1 #89b4fa);
    border: 2px solid #b4befe;
}

QPushButton#globalSearchButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #4a6ecf, stop:1 #3b5dbf);
    border: 2px solid #74c7ec;
}

/* --- Списки --- */
QListWidget {
    background-color: #313244; /* Surface1 */
    color: #e0e5ff; /* Brighter Text */
    border: 2px solid #45475a; /* Surface2 */
    border-radius: 4px;
    padding: 4px;
    font-size: 9pt;
}

QListWidget::item {
    padding: 5px 8px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #89b4fa, stop:1 #6a94da); /* Blue Gradient */
    color: #ffffff; /* White */
    font-weight: bold;
}

QListWidget::item:hover:!selected {
    background-color: #45475a; /* Surface2 */
}

/* --- Текстовые поля --- */
QTextEdit {
    background-color: #1a1b26; /* Darker Base */
    color: #c9d1f5; /* Brighter Subtext */
    border: 2px solid #414868; /* Custom darker Surface2 */
    border-radius: 4px;
    padding: 8px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9pt;
}

QTextEdit:focus {
    border: 2px solid #cba6f7; /* Lavender */
    background-color: #1e1f2e; /* Lighter Dark Base */
}

/* --- Чекбоксы --- */
QCheckBox {
    color: #e0e5ff; /* Brighter Text */
    font-size: 9pt;
    spacing: 4px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #45475a; /* Surface2 */
    border-radius: 2px;
    background-color: #313244; /* Surface1 */
}

QCheckBox::indicator:checked {
    background-color: #cba6f7; /* Lavender */
    border: 1px solid #cba6f7; /* Lavender */
}

QCheckBox::indicator:hover {
    border: 1px solid #89b4fa; /* Blue */
}

/* --- Метки --- */
QLabel {
    color: #e0e5ff; /* Brighter Text */
    background-color: transparent;
    font-size: 9pt;
}

QLabel[class="bold"] {
    font-weight: bold;
    color: #b4befe; /* Even Brighter Text */
}

QLabel[class="header"] {
    font-weight: bold;
    color: #d4a5ff; /* Brighter Lavender */
    font-size: 10pt;
}

QLabel[class="accent"] {
    color: #89dceb; /* Sky */
    font-weight: bold;
}

/* --- Полосы прокрутки --- */
QScrollBar:vertical {
    border: none;
    background-color: #313244; /* Surface1 */
    width: 10px;
    margin: 10px 0 10px 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #45475a; /* Surface2 */
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70; /* Surface2 Hover */
}

QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
    border: none;
    background: none;
    height: 10px;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background-color: #313244; /* Surface1 */
    height: 10px;
    margin: 0 10px 0 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #45475a; /* Surface2 */
    min-width: 20px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #585b70; /* Surface2 Hover */
}

/* --- Меню --- */
QMenuBar {
    background-color: #181825; /* Mantle */
    color: #e0e5ff; /* Brighter Text */
    font-size: 10pt;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 10px;
}

QMenuBar::item:selected {
    background-color: #313244; /* Surface1 */
}

QMenu {
    background-color: #1e1e2e; /* Base */
    color: #e0e5ff; /* Brighter Text */
    border: 1px solid #45475a; /* Surface2 */
    padding: 3px;
}

QMenu::item {
    padding: 4px 20px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #45475a; /* Surface2 */
}

QMenu::separator {
    height: 1px;
    background: #45475a; /* Surface2 */
    margin: 3px 0;
}

/* --- Строка статуса --- */
QStatusBar {
    background-color: #181825; /* Mantle */
    color: #b4befe; /* Brighter Text */
    font-size: 9pt;
    font-weight: 500;
}

/* --- Подсказки --- */
QToolTip {
    background-color: #313244; /* Surface1 */
    color: #e0e5ff; /* Brighter Text */
    border: 1px solid #45475a; /* Surface2 */
    border-radius: 3px;
    padding: 4px;
    font-size: 9pt;
}

/* --- Диалоги --- */
QDialog {
    background-color: #1e1e2e; /* Base */
    color: #e0e5ff; /* Brighter Text */
}

QDialog QLabel {
    font-size: 10pt;
}

/* --- Разделители --- */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: #45475a; /* Surface2 */
    border: none;
}
"""


# ===============================
# === СВЕТЛАЯ ТЕМА ===
# ===============================
LIGHT_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #eff1f5; /* Latte Base */
    color: #3c3f51; /* Darker Latte Text */
}

/* --- Вкладки --- */
QTabWidget::pane {
    border: 1px solid #bcc0cc; /* Latte Overlay 0 */
    background-color: #eff1f5; /* Latte Base */
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #ccd0da; /* Latte Surface 1 */
    color: #3c3f51; /* Darker Latte Text */
    border: 1px solid #bcc0cc; /* Latte Overlay 0 */
    padding: 8px 15px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #eff1f5; /* Latte Base */
    border-bottom-color: #eff1f5; /* Latte Base */
}

QTabBar::tab:hover:!selected {
    background-color: #bcc0cc; /* Latte Overlay 0 */
}

/* --- Группы --- */
QGroupBox {
    border: 2px solid #9ca0b0; /* Darker Latte Overlay */
    border-radius: 6px;
    margin-top: 1.2em;
    padding: 10px;
    font-weight: bold;
    color: #1e66f5; /* Latte Blue */
    background-color: #e6e9ef; /* Latte Surface 0 - светлее фона */
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    background-color: #eff1f5; /* Latte Base */
    border: none;
    color: #5c5ff5; /* Brighter Latte Blue */
    font-size: 16pt;
    font-weight: bold;
    letter-spacing: 0.5px;
}

/* --- Кнопки --- */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ccd0da, stop:1 #b0b4c0); /* Light Gradient */
    color: #3c3f51; /* Darker Latte Text */
    border: 2px solid #9ca0b0; /* Latte Overlay 0 */
    border-radius: 5px;
    padding: 5px 12px;
    font-weight: bold;
    font-size: 10pt;
    min-height: 20px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #7287fd, stop:1 #5a6fdd); /* Blue Gradient */
    border: 2px solid #1e66f5; /* Latte Blue */
    color: #ffffff;
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #acb0be, stop:1 #9ca0b0); /* Darker Light Gradient */
    border: 2px solid #7287fd; /* Lavender */
    padding: 7px 13px 5px 15px; /* Эффект нажатия */
}

QPushButton:disabled {
    background-color: #ccd0da; /* Latte Surface 1 */
    color: #9ca0b0; /* Latte Subtext 0 */
    border: 2px solid #bcc0cc; /* Latte Overlay 0 */
}

/* --- Основные кнопки действий (Синие) --- */
QPushButton#processButton, QPushButton#classifyButton, QPushButton#addButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #1e66f5, stop:1 #0e56e5); /* Blue Gradient */
    color: #ffffff; /* White */
    border: 2px solid #1e66f5; /* Latte Blue */
    font-weight: bold;
    font-size: 10pt;
}

QPushButton#processButton:hover, QPushButton#classifyButton:hover, QPushButton#addButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #7287fd, stop:1 #5a6fdd); /* Brighter Blue Gradient */
    border: 2px solid #7287fd; /* Latte Lavender */
}

QPushButton#processButton:pressed, QPushButton#classifyButton:pressed, QPushButton#addButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #0e56e5, stop:1 #0446d5); /* Darker Blue Gradient */
    border: 2px solid #04a5e5; /* Latte Sapphire */
}

/* --- Кнопки успеха (Зеленые) --- */
QPushButton#importButton, QPushButton#exportButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #40a02b, stop:1 #30901b); /* Green Gradient */
    color: #ffffff; /* White */
    border: 2px solid #40a02b; /* Latte Green */
    font-weight: bold;
    font-size: 10pt;
}

QPushButton#importButton:hover, QPushButton#exportButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #50b03b, stop:1 #40a02b); /* Brighter Green Gradient */
    border: 2px solid #179299; /* Latte Teal */
}

QPushButton#importButton:pressed, QPushButton#exportButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #30901b, stop:1 #20800b); /* Darker Green Gradient */
    border: 2px solid #30901b;
}

/* --- Критические кнопки (Красные) --- */
QPushButton#deleteButton, QPushButton#clearButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #d20f39, stop:1 #b20f29); /* Red Gradient */
    color: #ffffff; /* White */
    border: 2px solid #d20f39; /* Latte Red */
    font-weight: bold;
}

QPushButton#deleteButton:hover, QPushButton#clearButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #e64553, stop:1 #d20f39); /* Brighter Red Gradient */
    border: 2px solid #e64553; /* Lighter Red */
}

QPushButton#deleteButton:pressed, QPushButton#clearButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #b20f29, stop:1 #a20f19); /* Darker Red Gradient */
    border: 2px solid #b20f29;
}

/* --- Поля ввода --- */
QLineEdit, QSpinBox {
    background-color: #ccd0da; /* Latte Surface 1 */
    color: #3c3f51; /* Darker Latte Text */
    border: 2px solid #9ca0b0; /* Latte Overlay 0 */
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}

QLineEdit:focus, QSpinBox:focus {
    border: 2px solid #7287fd; /* Latte Lavender */
    background-color: #dce0ea; /* Lighter Surface1 */
}

QLineEdit:disabled, QSpinBox:disabled {
    background-color: #e6e9ef; /* Latte Surface 0 */
    color: #9ca0b0; /* Latte Subtext 0 */
    border: 2px solid #ccd0da;
}

/* --- Глобальный поиск --- */
QWidget#globalSearchWidget {
    background-color: #e6e9ef; /* Latte Surface 0 */
    border: 2px solid #1e66f5; /* Latte Blue */
    border-radius: 8px;
}

QLineEdit#globalSearchInput {
    background-color: #dce0ea; /* Lighter Surface */
    border: 2px solid #1e66f5;
    color: #2c2f3c; /* Dark Text */
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 10pt;
}

QLineEdit#globalSearchInput:focus {
    border: 2px solid #7287fd; /* Latte Lavender */
    background-color: #f2f4f8;
}

QPushButton#globalSearchButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #1e66f5, stop:1 #0e56e5); /* Blue Gradient */
    color: #ffffff;
    border: 2px solid #1e66f5;
    border-radius: 6px;
    font-weight: bold;
    font-size: 11pt;
    padding: 6px 10px;
}

QPushButton#globalSearchButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #7287fd, stop:1 #5a6fdd);
    border: 2px solid #7287fd;
}

QPushButton#globalSearchButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #0e56e5, stop:1 #0446d5);
    border: 2px solid #04a5e5;
}

/* --- Списки --- */
QListWidget {
    background-color: #ccd0da; /* Latte Surface 1 */
    color: #3c3f51; /* Darker Latte Text */
    border: 2px solid #9ca0b0; /* Latte Overlay 0 */
    border-radius: 4px;
    padding: 4px;
    font-size: 9pt;
}

QListWidget::item {
    padding: 5px 8px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #1e66f5, stop:1 #0e56e5); /* Blue Gradient */
    color: #ffffff; /* White */
    font-weight: bold;
}

QListWidget::item:hover:!selected {
    background-color: #bcc0cc; /* Latte Overlay 0 */
}

/* --- Текстовые поля --- */
QTextEdit {
    background-color: #e6e9ef; /* Latte Surface 0 */
    color: #2c2f41; /* Darker Latte Text */
    border: 2px solid #9ca0b0; /* Latte Overlay 0 */
    border-radius: 4px;
    padding: 8px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9pt;
}

QTextEdit:focus {
    border: 2px solid #7287fd; /* Latte Lavender */
    background-color: #dce0ea; /* Lighter Surface0 */
}

/* --- Чекбоксы --- */
QCheckBox {
    color: #3c3f51; /* Darker Latte Text */
    font-size: 9pt;
    spacing: 4px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #bcc0cc; /* Latte Overlay 0 */
    border-radius: 2px;
    background-color: #ccd0da; /* Latte Surface 1 */
}

QCheckBox::indicator:checked {
    background-color: #7287fd; /* Latte Lavender */
    border: 1px solid #7287fd; /* Latte Lavender */
}

QCheckBox::indicator:hover {
    border: 1px solid #1e66f5; /* Latte Blue */
}

/* --- Метки --- */
QLabel {
    color: #3c3f51; /* Darker Latte Text */
    background-color: transparent;
    font-size: 9pt;
}

QLabel[class="bold"] {
    font-weight: bold;
    color: #2c2f41; /* Even Darker Latte Text */
}

QLabel[class="header"] {
    font-weight: bold;
    color: #7287fd; /* Brighter Latte Lavender */
    font-size: 10pt;
}

QLabel[class="accent"] {
    color: #1e66f5; /* Latte Blue */
    font-weight: bold;
}

/* --- Полосы прокрутки --- */
QScrollBar:vertical {
    border: none;
    background-color: #ccd0da; /* Latte Surface 1 */
    width: 10px;
    margin: 10px 0 10px 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #bcc0cc; /* Latte Overlay 0 */
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #acb0be; /* Latte Overlay 1 */
}

QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
    border: none;
    background: none;
    height: 15px;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background-color: #ccd0da; /* Latte Surface 1 */
    height: 10px;
    margin: 0 10px 0 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #bcc0cc; /* Latte Overlay 0 */
    min-width: 20px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #acb0be; /* Latte Overlay 1 */
}

/* --- Меню --- */
QMenuBar {
    background-color: #e6e9ef; /* Latte Surface 0 */
    color: #3c3f51; /* Darker Latte Text */
    font-size: 10pt;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 10px;
}

QMenuBar::item:selected {
    background-color: #ccd0da; /* Latte Surface 1 */
}

QMenu {
    background-color: #eff1f5; /* Latte Base */
    color: #3c3f51; /* Darker Latte Text */
    border: 1px solid #bcc0cc; /* Latte Overlay 0 */
    padding: 3px;
}

QMenu::item {
    padding: 4px 20px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #ccd0da; /* Latte Surface 1 */
}

QMenu::separator {
    height: 1px;
    background: #bcc0cc; /* Latte Overlay 0 */
    margin: 3px 0;
}

/* --- Строка статуса --- */
QStatusBar {
    background-color: #e6e9ef; /* Latte Surface 0 */
    color: #5c5f77; /* Darker Latte Text */
    font-size: 9pt;
    font-weight: 500;
}

/* --- Подсказки --- */
QToolTip {
    background-color: #ccd0da; /* Latte Surface 1 */
    color: #3c3f51; /* Darker Latte Text */
    border: 1px solid #bcc0cc; /* Latte Overlay 0 */
    border-radius: 3px;
    padding: 4px;
    font-size: 9pt;
}

/* --- Диалоги --- */
QDialog {
    background-color: #eff1f5; /* Latte Base */
    color: #3c3f51; /* Darker Latte Text */
}

QDialog QLabel {
    font-size: 10pt;
}

/* --- Разделители --- */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: #bcc0cc; /* Latte Overlay 0 */
    border: none;
}
"""

