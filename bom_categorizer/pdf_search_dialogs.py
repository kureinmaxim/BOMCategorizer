# -*- coding: utf-8 -*-
"""
Диалоги для поиска PDF документации
"""

import os
import platform
import subprocess
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QComboBox, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QTabWidget,
    QWidget, QGridLayout, QTextBrowser, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QTextCursor


class PDFSearchDialog(QDialog):
    """Главный диалог поиска PDF"""
    
    def __init__(self, parent, config: dict):
        super().__init__(parent)
        self.parent_window = parent
        self.config = config
        
        self.setWindowTitle("🔍 Поиск PDF документации")
        self.setModal(False)
        self.resize(900, 700)
        
        self._create_ui()
        
    def _create_ui(self):
        """Создает интерфейс"""
        layout = QVBoxLayout(self)
        
        # Поле поиска
        search_layout = QHBoxLayout()
        search_label = QLabel("Компонент:")
        search_label.setFixedWidth(100)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите название компонента (например: HMC449, LM358)")
        self.search_input.returnPressed.connect(self.on_search)
        
        search_btn = QPushButton("🔎 Найти")
        search_btn.clicked.connect(self.on_search)
        search_btn.setFixedWidth(100)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # Вкладки для разных типов поиска
        self.tabs = QTabWidget()
        
        # Вкладка локального поиска
        self.local_tab = self._create_local_tab()
        self.tabs.addTab(self.local_tab, "📁 Локальный поиск")
        
        # Вкладка AI поиска
        self.ai_tab = self._create_ai_tab()
        self.tabs.addTab(self.ai_tab, "🤖 AI поиск")
        
        layout.addWidget(self.tabs)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_local_tab(self) -> QWidget:
        """Создает вкладку локального поиска"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Настройки пути
        path_group = QGroupBox("Путь для поиска")
        path_layout = QHBoxLayout()
        
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText("По умолчанию: папка с базой данных")
        
        browse_btn = QPushButton("📁 Обзор...")
        browse_btn.clicked.connect(self.browse_local_path)
        browse_btn.setFixedWidth(100)
        
        path_layout.addWidget(self.local_path_input)
        path_layout.addWidget(browse_btn)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # Результаты
        results_label = QLabel("Найденные файлы:")
        results_label.setProperty("class", "bold")
        layout.addWidget(results_label)
        
        self.local_results_list = QListWidget()
        self.local_results_list.itemDoubleClicked.connect(self.open_local_file)
        layout.addWidget(self.local_results_list)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        open_file_btn = QPushButton("📄 Открыть файл")
        open_file_btn.clicked.connect(self.open_selected_local_file)
        actions_layout.addWidget(open_file_btn)
        
        open_folder_btn = QPushButton("📁 Открыть папку")
        open_folder_btn.clicked.connect(self.open_local_file_folder)
        actions_layout.addWidget(open_folder_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return widget
    
    def _create_ai_tab(self) -> QWidget:
        """Создает вкладку AI поиска"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Выбор провайдера
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Провайдер AI:")
        provider_label.setFixedWidth(100)
        
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["Anthropic Claude", "OpenAI GPT-4o"])
        self.ai_provider_combo.setFixedWidth(200)
        
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.ai_provider_combo)
        provider_layout.addStretch()
        layout.addLayout(provider_layout)
        
        # Результаты AI поиска
        results_label = QLabel("Результаты поиска:")
        results_label.setProperty("class", "bold")
        layout.addWidget(results_label)
        
        self.ai_results_browser = QTextBrowser()
        self.ai_results_browser.setOpenExternalLinks(True)
        layout.addWidget(self.ai_results_browser)
        
        # Кнопка сохранения
        save_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить результат")
        save_btn.clicked.connect(self.save_ai_results)
        save_layout.addWidget(save_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        return widget
    
    def on_search(self):
        """Запускает поиск"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите название компонента")
            return
        
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:  # Локальный поиск
            self.run_local_search(query)
        else:  # AI поиск
            self.run_ai_search(query)
    
    def run_local_search(self, query: str):
        """Выполняет локальный поиск"""
        from .pdf_search import LocalPDFSearcher, get_default_pdf_directories
        
        # Определяем путь для поиска
        search_path = self.local_path_input.text().strip()
        if not search_path:
            # Используем папки по умолчанию
            search_dirs = get_default_pdf_directories()
            search_path = search_dirs[0] if search_dirs else None
        
        if not search_path or not os.path.exists(search_path):
            QMessageBox.warning(
                self,
                "Ошибка",
                "Папка для поиска не найдена!\nУкажите путь вручную."
            )
            return
        
        # Выполняем поиск
        searcher = LocalPDFSearcher(search_path)
        results = searcher.search(query, min_match_length=3)
        
        # Отображаем результаты
        self.local_results_list.clear()
        
        if not results:
            item = QListWidgetItem("❌ Файлы не найдены")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.local_results_list.addItem(item)
        else:
            for result in results:
                item_text = f"📄 {result['filename']}\n   📁 {result['folder']} | 📊 {result['size']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, result['path'])
                self.local_results_list.addItem(item)
    
    def run_ai_search(self, query: str):
        """Выполняет AI поиск"""
        from .pdf_search import AIPDFSearcher
        
        # Получаем API ключ из конфига
        provider = self.ai_provider_combo.currentText()
        api_key = None
        
        if "Anthropic" in provider:
            api_key = self.config.get("pdf_search", {}).get("anthropic_api_key")
            provider_name = "anthropic"
        else:
            api_key = self.config.get("pdf_search", {}).get("openai_api_key")
            provider_name = "openai"
        
        if not api_key:
            QMessageBox.warning(
                self,
                "API ключ не найден",
                f"API ключ для {provider} не установлен.\n"
                "Откройте настройки и введите ваш API ключ."
            )
            return
        
        # Показываем индикатор загрузки
        self.ai_results_browser.setHtml("<h3>⏳ Поиск...</h3><p>Запрашиваем информацию у AI...</p>")
        
        # Запускаем поиск в отдельном потоке
        self.ai_worker = AISearchWorker(provider_name, api_key, query)
        self.ai_worker.finished.connect(self.display_ai_results)
        self.ai_worker.start()
    
    def display_ai_results(self, results: Dict):
        """Отображает результаты AI поиска"""
        if 'error' in results:
            html = f"""
            <h2 style="color: #f38ba8;">❌ Ошибка поиска</h2>
            <p><b>Компонент:</b> {results.get('component', 'N/A')}</p>
            <p><b>Ошибка:</b> {results['error']}</p>
            """
            if 'raw_response' in results:
                html += f"<h3>Сырой ответ:</h3><pre>{results['raw_response']}</pre>"
        else:
            html = self._format_ai_results_html(results)
        
        self.ai_results_browser.setHtml(html)
    
    def _format_ai_results_html(self, results: Dict) -> str:
        """Форматирует результаты AI в HTML"""
        if not results.get('found', False):
            return f"""
            <h2 style="color: #f9e2af;">⚠️ Компонент не найден</h2>
            <p><b>Запрос:</b> {results.get('component', 'N/A')}</p>
            <p>Информация о данном компоненте не найдена.</p>
            """
        
        html = f"""
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; }}
            h2 {{ color: #89b4fa; border-bottom: 2px solid #89b4fa; padding-bottom: 5px; }}
            h3 {{ color: #a6e3a1; margin-top: 20px; }}
            .spec-table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            .spec-table td {{ padding: 8px; border: 1px solid #45475a; }}
            .spec-table td:first-child {{ font-weight: bold; background-color: #313244; width: 30%; }}
            .example {{ background-color: #1e1e2e; padding: 10px; margin: 5px 0; border-left: 3px solid #a6e3a1; }}
            .datasheet-link {{ 
                display: inline-block;
                background-color: #89b4fa;
                color: #1e1e2e;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
            }}
            .datasheet-link:hover {{ background-color: #74c7ec; }}
        </style>
        
        <h2>📋 {results.get('full_name', results.get('component', 'Компонент'))}</h2>
        
        <table class="spec-table">
            <tr>
                <td>🏭 Производитель</td>
                <td>{results.get('manufacturer', 'N/A')}</td>
            </tr>
            <tr>
                <td>🔧 Тип</td>
                <td>{results.get('type', 'N/A')}</td>
            </tr>
        </table>
        
        <h3>📝 Описание</h3>
        <p>{results.get('description', 'Описание отсутствует')}</p>
        """
        
        # Характеристики
        specs = results.get('specifications', {})
        if specs:
            html += "<h3>⚙️ Основные характеристики</h3><table class='spec-table'>"
            for key, value in specs.items():
                html += f"<tr><td>{key}</td><td>{value}</td></tr>"
            html += "</table>"
        
        # Примеры использования
        examples = results.get('examples', [])
        if examples:
            html += "<h3>💡 Примеры использования</h3>"
            for i, example in enumerate(examples, 1):
                html += f"<div class='example'>{i}. {example}</div>"
        
        # Ссылка на datasheet
        datasheet_url = results.get('datasheet_url', '')
        if datasheet_url and datasheet_url.startswith('http'):
            html += f"""
            <h3>📄 Документация</h3>
            <a href="{datasheet_url}" class="datasheet-link" target="_blank">
                📥 Скачать Datasheet (PDF)
            </a>
            """
        
        # Провайдер
        provider = results.get('provider', 'AI')
        html += f"<p style='margin-top: 30px; color: #6c7086; font-size: 0.9em;'>Информация предоставлена: {provider}</p>"
        
        return html
    
    def browse_local_path(self):
        """Выбор папки для локального поиска"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для поиска PDF",
            self.local_path_input.text() or ""
        )
        if folder:
            self.local_path_input.setText(folder)
    
    def open_local_file(self, item: QListWidgetItem):
        """Открывает PDF файл"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self._open_file_in_system(file_path)
    
    def open_selected_local_file(self):
        """Открывает выбранный файл"""
        items = self.local_results_list.selectedItems()
        if items:
            self.open_local_file(items[0])
    
    def open_local_file_folder(self):
        """Открывает папку с выбранным файлом"""
        items = self.local_results_list.selectedItems()
        if not items:
            return
        
        file_path = items[0].data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            folder = os.path.dirname(file_path)
            self._open_file_in_system(folder)
    
    def _open_file_in_system(self, path: str):
        """Открывает файл или папку в системном приложении"""
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', path])
            else:  # Linux
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть:\n{str(e)}")
    
    def save_ai_results(self):
        """Сохраняет результаты AI поиска"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты",
            f"ai_search_{self.search_input.text()}.html",
            "HTML Files (*.html);;Text Files (*.txt)"
        )
        
        if file_path:
            content = self.ai_results_browser.toHtml()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Сохранено", f"Результаты сохранены:\n{file_path}")
    
    def open_settings(self):
        """Открывает настройки"""
        dialog = PDFSearchSettingsDialog(self, self.config)
        if dialog.exec() == QDialog.Accepted:
            # Обновляем конфиг
            self.config = dialog.get_config()
            # Сохраняем в родительском окне
            if hasattr(self.parent_window, 'save_pdf_search_config'):
                self.parent_window.save_pdf_search_config(self.config)


class PDFSearchSettingsDialog(QDialog):
    """Диалог настроек поиска PDF"""
    
    def __init__(self, parent, config: dict):
        super().__init__(parent)
        self.config = config.copy()
        
        self.setWindowTitle("⚙️ Настройки поиска PDF")
        self.setModal(True)
        self.resize(600, 400)
        
        self._create_ui()
        self._load_settings()
    
    def _create_ui(self):
        """Создает интерфейс"""
        layout = QVBoxLayout(self)
        
        # API ключи
        api_group = QGroupBox("API ключи для AI поиска")
        api_layout = QGridLayout()
        
        # Anthropic
        anthropic_label = QLabel("Anthropic Claude:")
        self.anthropic_key_input = QLineEdit()
        self.anthropic_key_input.setEchoMode(QLineEdit.Password)
        self.anthropic_key_input.setPlaceholderText("sk-ant-api03-...")
        
        show_anthropic_btn = QCheckBox("Показать")
        show_anthropic_btn.stateChanged.connect(
            lambda state: self.anthropic_key_input.setEchoMode(
                QLineEdit.Normal if state else QLineEdit.Password
            )
        )
        
        api_layout.addWidget(anthropic_label, 0, 0)
        api_layout.addWidget(self.anthropic_key_input, 0, 1)
        api_layout.addWidget(show_anthropic_btn, 0, 2)
        
        # OpenAI
        openai_label = QLabel("OpenAI GPT:")
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        
        show_openai_btn = QCheckBox("Показать")
        show_openai_btn.stateChanged.connect(
            lambda state: self.openai_key_input.setEchoMode(
                QLineEdit.Normal if state else QLineEdit.Password
            )
        )
        
        api_layout.addWidget(openai_label, 1, 0)
        api_layout.addWidget(self.openai_key_input, 1, 1)
        api_layout.addWidget(show_openai_btn, 1, 2)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Помощь
        help_label = QLabel(
            "💡 <b>Как получить API ключи:</b><br>"
            "• Anthropic: <a href='https://console.anthropic.com/'>console.anthropic.com</a><br>"
            "• OpenAI: <a href='https://platform.openai.com/api-keys'>platform.openai.com/api-keys</a>"
        )
        help_label.setOpenExternalLinks(True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        layout.addStretch()
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def _load_settings(self):
        """Загружает настройки"""
        pdf_config = self.config.get("pdf_search", {})
        self.anthropic_key_input.setText(pdf_config.get("anthropic_api_key", ""))
        self.openai_key_input.setText(pdf_config.get("openai_api_key", ""))
    
    def get_config(self) -> dict:
        """Возвращает обновленный конфиг"""
        if "pdf_search" not in self.config:
            self.config["pdf_search"] = {}
        
        self.config["pdf_search"]["anthropic_api_key"] = self.anthropic_key_input.text().strip()
        self.config["pdf_search"]["openai_api_key"] = self.openai_key_input.text().strip()
        
        return self.config


class AISearchWorker(QThread):
    """Worker для AI поиска в отдельном потоке"""
    finished = Signal(dict)
    
    def __init__(self, provider: str, api_key: str, query: str):
        super().__init__()
        self.provider = provider
        self.api_key = api_key
        self.query = query
    
    def run(self):
        """Выполняет AI поиск"""
        from .pdf_search import AIPDFSearcher
        
        searcher = AIPDFSearcher(self.provider, self.api_key)
        results = searcher.search(self.query)
        self.finished.emit(results)

