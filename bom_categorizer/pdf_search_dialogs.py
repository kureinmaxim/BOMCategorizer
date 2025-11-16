# -*- coding: utf-8 -*-
"""
Диалоги для поиска PDF документации
"""

import os
import json
import platform
import subprocess
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QComboBox, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QTabWidget,
    QWidget, QGridLayout, QTextBrowser, QCheckBox, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QTextCursor


class PDFSearchDialog(QDialog):
    """Главный диалог поиска PDF"""
    
    def __init__(self, parent, config: dict, unlocked: bool = True, expert_mode: bool = True):
        super().__init__(parent)
        self.parent_window = parent
        self.config = config
        self.unlocked = unlocked
        self.expert_mode = expert_mode
        
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
        
        # Вкладка локального поиска - доступна всегда
        self.local_tab = self._create_local_tab()
        self.tabs.addTab(self.local_tab, "📁 Локальный поиск")
        
        # Вкладка AI поиска - только для разблокированных экспертов
        if self.unlocked and self.expert_mode:
            self.ai_tab = self._create_ai_tab()
            self.tabs.addTab(self.ai_tab, "🤖 AI поиск")
        else:
            # Создаем заглушку для AI вкладки
            self.ai_tab = QWidget()
            ai_layout = QVBoxLayout(self.ai_tab)
            ai_layout.addStretch()
            
            lock_label = QLabel("🔒 AI поиск доступен только в экспертном режиме после разблокировки приложения")
            lock_label.setAlignment(Qt.AlignCenter)
            lock_label.setStyleSheet("color: #f38ba8; font-size: 14pt; font-weight: bold;")
            ai_layout.addWidget(lock_label)
            
            hint_label = QLabel("Дважды кликните на имя разработчика для разблокировки")
            hint_label.setAlignment(Qt.AlignCenter)
            hint_label.setStyleSheet("color: #cdd6f4; font-size: 12pt;")
            ai_layout.addWidget(hint_label)
            
            ai_layout.addStretch()
            self.tabs.addTab(self.ai_tab, "🔒 AI поиск")
            # Отключаем вкладку
            self.tabs.setTabEnabled(1, False)
        
        layout.addWidget(self.tabs)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        # Кнопка настроек - только для разблокированных экспертов
        if self.unlocked and self.expert_mode:
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
        self.local_path_input.setPlaceholderText("По умолчанию: папки БД, Project/pdf* (macOS), C:\\Project\\pdf* (Win)")
        
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
        elif self.unlocked and self.expert_mode:  # AI поиск - только для разблокированных экспертов
            self.run_ai_search(query)
        else:
            # Вкладка AI заблокирована
            QMessageBox.information(
                self,
                "AI поиск недоступен",
                "AI поиск доступен только в экспертном режиме после разблокировки приложения.\n\n"
                "Дважды кликните на имя разработчика для разблокировки."
            )
    
    def run_local_search(self, query: str):
        """Выполняет локальный поиск"""
        from .pdf_search import LocalPDFSearcher, get_default_pdf_directories
        
        # Определяем пути для поиска
        search_path = self.local_path_input.text().strip()
        
        if search_path:
            # Пользователь указал конкретный путь - ищем только там
            if not os.path.exists(search_path):
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Указанная папка не найдена!\nПроверьте путь."
                )
                return
            search_dirs = [search_path]
        else:
            # Используем все папки по умолчанию (включая пользовательские из конфига)
            search_dirs = get_default_pdf_directories(self.config)
            if not search_dirs:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Папки для поиска не найдены!\nУкажите путь вручную."
                )
                return
        
        # Выполняем поиск во всех директориях
        all_results = []
        for directory in search_dirs:
            if os.path.exists(directory):
                searcher = LocalPDFSearcher(directory)
                results = searcher.search(query, min_match_length=3)
                all_results.extend(results)
        
        # Удаляем дубликаты по пути (если файл найден в нескольких директориях)
        seen_paths = set()
        unique_results = []
        for result in all_results:
            if result['path'] not in seen_paths:
                seen_paths.add(result['path'])
                unique_results.append(result)
        
        # Отображаем результаты
        self.local_results_list.clear()
        
        if not unique_results:
            item = QListWidgetItem("❌ Файлы не найдены")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.local_results_list.addItem(item)
        else:
            for result in unique_results:
                item_text = f"📄 {result['filename']}\n   📁 {result['folder']} | 📊 {result['size']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, result['path'])
                self.local_results_list.addItem(item)
    
    def run_ai_search(self, query: str):
        """Выполняет AI поиск"""
        from .pdf_search import AIPDFSearcher
        
        # Получаем API ключ из нового централизованного конфига
        api_keys = self.config.get("api_keys", {})
        provider = self.ai_provider_combo.currentText()
        api_key = None
        
        if "Anthropic" in provider:
            api_key = api_keys.get("anthropic")
            provider_name = "anthropic"
        else:
            api_key = api_keys.get("openai")
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
        # Проверка доступности (только для разблокированных экспертов)
        if not (self.unlocked and self.expert_mode):
            return
        
        if not hasattr(self, 'ai_results_browser'):
            return
        
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
        # Проверка доступности (настройки только для разблокированных экспертов)
        if not (self.unlocked and self.expert_mode):
            QMessageBox.information(
                self,
                "Настройки недоступны",
                "Настройки API доступны только в экспертном режиме после разблокировки приложения.\n\n"
                "Дважды кликните на имя разработчика для разблокировки."
            )
            return
        
        dialog = PDFSearchSettingsDialog(self, self.config)
        if dialog.exec() == QDialog.Accepted:
            # Обновляем конфиг
            self.config = dialog.get_config()
            # Сохраняем в родительском окне
            if hasattr(self.parent_window, 'save_pdf_search_config'):
                self.parent_window.save_pdf_search_config(self.config)


class UnifiedSettingsDialog(QDialog):
    """Единое окно настроек с вкладками для API ключей и AI классификатора"""
    
    def __init__(self, parent, config: dict):
        super().__init__(parent)
        self.config = config.copy()
        self.parent_window = parent
        
        self.setWindowTitle("⚙️ Настройки API и AI")
        self.setModal(True)
        self.resize(700, 550)
        
        self._create_ui()
        self._load_settings()
    
    def _create_ui(self):
        """Создает интерфейс с вкладками"""
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        # Вкладка 1: Пути поиска PDF
        self.pdf_paths_tab = self._create_pdf_paths_tab()
        self.tabs.addTab(self.pdf_paths_tab, "📂 Пути PDF")
        
        # Вкладка 2: API ключи
        self.api_keys_tab = self._create_api_keys_tab()
        self.tabs.addTab(self.api_keys_tab, "🔑 API Ключи")
        
        # Вкладка 3: Настройки AI классификатора
        self.ai_classifier_tab = self._create_ai_classifier_tab()
        self.tabs.addTab(self.ai_classifier_tab, "🤖 AI Классификатор")
        
        layout.addWidget(self.tabs)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_all_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_pdf_paths_tab(self):
        """Создает вкладку управления путями поиска PDF"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        desc = QLabel(
            "📁 <b>Настройка пользовательских папок для поиска PDF</b><br><br>"
            "Добавьте свои папки, в которых будет выполняться рекурсивный поиск PDF файлов.<br>"
            "Эти папки будут использоваться дополнительно к стандартным (папка БД, Project/pdf* и т.д.)."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Список путей
        paths_group = QGroupBox("Пользовательские папки")
        paths_layout = QVBoxLayout()
        
        self.custom_paths_list = QListWidget()
        self.custom_paths_list.setMinimumHeight(200)
        paths_layout.addWidget(self.custom_paths_list)
        
        # Кнопки управления путями
        buttons_layout = QHBoxLayout()
        
        add_path_btn = QPushButton("➕ Добавить папку")
        add_path_btn.clicked.connect(self._add_custom_path)
        buttons_layout.addWidget(add_path_btn)
        
        remove_path_btn = QPushButton("➖ Удалить выбранную")
        remove_path_btn.clicked.connect(self._remove_custom_path)
        buttons_layout.addWidget(remove_path_btn)
        
        clear_paths_btn = QPushButton("🗑️ Очистить все")
        clear_paths_btn.clicked.connect(self._clear_custom_paths)
        buttons_layout.addWidget(clear_paths_btn)
        
        buttons_layout.addStretch()
        paths_layout.addLayout(buttons_layout)
        
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        # Подсказка
        hint_label = QLabel(
            "💡 <b>Совет:</b> Вы можете также вручную редактировать файл <code>config_qt.json</code><br>"
            "в разделе <code>\"pdf_search\" → \"custom_directories\"</code> для добавления путей."
        )
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        layout.addStretch()
        return tab
    
    def _add_custom_path(self):
        """Добавляет новую пользовательскую папку"""
        from PySide6.QtWidgets import QFileDialog
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для поиска PDF",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder:
            # Проверяем, не добавлена ли уже эта папка
            for i in range(self.custom_paths_list.count()):
                if self.custom_paths_list.item(i).text() == folder:
                    QMessageBox.information(
                        self,
                        "Информация",
                        "Эта папка уже добавлена в список!"
                    )
                    return
            
            self.custom_paths_list.addItem(folder)
    
    def _remove_custom_path(self):
        """Удаляет выбранную папку"""
        current_item = self.custom_paths_list.currentItem()
        if current_item:
            self.custom_paths_list.takeItem(self.custom_paths_list.row(current_item))
        else:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Выберите папку для удаления!"
            )
    
    def _clear_custom_paths(self):
        """Очищает весь список пользовательских папок"""
        if self.custom_paths_list.count() > 0:
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Удалить все пользовательские папки из списка?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.custom_paths_list.clear()

    def _create_api_keys_tab(self):
        """Создает единую вкладку для всех API ключей"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        api_group = QGroupBox("Ключи доступа для облачных сервисов")
        api_layout = QGridLayout()

        # Anthropic
        anthropic_label = QLabel("Anthropic Claude API Key:")
        self.anthropic_key_input = QLineEdit()
        self.anthropic_key_input.setEchoMode(QLineEdit.Password)
        self.anthropic_key_input.setPlaceholderText("sk-ant-...")
        
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
        openai_label = QLabel("OpenAI GPT API Key:")
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

        # Ollama
        ollama_group = QGroupBox("Настройки для локальных моделей (Ollama)")
        ollama_layout = QGridLayout()

        ollama_label = QLabel("Ollama URL:")
        self.ollama_url_input = QLineEdit()
        self.ollama_url_input.setPlaceholderText("http://localhost:11434")

        ollama_layout.addWidget(ollama_label, 0, 0)
        ollama_layout.addWidget(self.ollama_url_input, 0, 1)

        ollama_group.setLayout(ollama_layout)
        layout.addWidget(ollama_group)
        
        # Помощь
        help_label = QLabel(
            "💡 <b>Как получить API ключи:</b><br>"
            "• <b>Anthropic:</b> <a href='https://console.anthropic.com/'>console.anthropic.com</a><br>"
            "• <b>OpenAI:</b> <a href='https://platform.openai.com/api-keys'>platform.openai.com/api-keys</a><br>"
            "• <b>Ollama:</b> <a href='https://ollama.ai/'>ollama.ai</a> (для локального запуска)"
        )
        help_label.setOpenExternalLinks(True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        layout.addStretch()
        return tab

    def _create_ai_classifier_tab(self):
        """Создает вкладку настроек AI классификатора (без ключей)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        desc = QLabel(
            "Настройте параметры для автоматической классификации компонентов.\n"
            "API ключи настраиваются на соседней вкладке 'API Ключи'."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        form_group = QGroupBox("Параметры классификатора")
        form = QFormLayout()
        
        # Провайдер
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Anthropic Claude", "OpenAI GPT", "Ollama (локальный)"])
        form.addRow("Провайдер AI:", self.provider_combo)
        
        # Модель
        self.ai_model_input = QLineEdit()
        self.ai_model_input.setPlaceholderText("По умолчанию (оставьте пустым)")
        form.addRow("Модель (опционально):", self.ai_model_input)
        
        # Порог уверенности
        self.ai_confidence_combo = QComboBox()
        self.ai_confidence_combo.addItems(["Высокий (high)", "Средний (medium)", "Низкий (low)"])
        form.addRow("Порог уверенности:", self.ai_confidence_combo)

        form_group.setLayout(form)
        layout.addWidget(form_group)
        
        # Справка по моделям
        help_text = QTextBrowser()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(100)
        help_text.setOpenExternalLinks(True)
        help_text.setHtml("""
<b>Модели по умолчанию:</b><br>
• Anthropic: <code>claude-3-sonnet-20240229</code><br>
• OpenAI: <code>gpt-4</code><br>
• Ollama: <code>llama2</code>
        """)
        layout.addWidget(help_text)

        layout.addStretch()
        return tab
    
    def _load_settings(self):
        """Загружает настройки из config_qt.json"""
        # --- 0. Загрузка пользовательских путей PDF ---
        pdf_search_conf = self.config.get("pdf_search", {})
        custom_dirs = pdf_search_conf.get("custom_directories", [])
        self.custom_paths_list.clear()
        for path in custom_dirs:
            if path:  # Пропускаем пустые строки
                self.custom_paths_list.addItem(path)
        
        # --- 1. Загрузка API ключей ---
        # Сначала из новой централизованной секции
        api_keys = self.config.get("api_keys", {})
        
        # Для обратной совместимости, ищем в старых секциях, если в новой пусто
        ai_classifier_conf = self.config.get("ai_classifier", {})
        ai_api_keys = ai_classifier_conf.get("api_keys", {})
        
        # Anthropic
        anthropic_key = api_keys.get("anthropic") or \
                        pdf_search_conf.get("anthropic_api_key") or \
                        ai_api_keys.get("anthropic", "")
        self.anthropic_key_input.setText(anthropic_key)
        
        # OpenAI
        openai_key = api_keys.get("openai") or \
                     pdf_search_conf.get("openai_api_key") or \
                     ai_api_keys.get("openai", "")
        self.openai_key_input.setText(openai_key)
        
        # Ollama
        ollama_url = api_keys.get("ollama_url") or \
                     ai_api_keys.get("ollama") or \
                     "http://localhost:11434"
        self.ollama_url_input.setText(ollama_url)
        
        # --- 2. Загрузка настроек AI Классификатора ---
        settings = ai_classifier_conf # Используем уже загруженный конфиг
        
        provider_map = {"anthropic": 0, "openai": 1, "ollama": 2}
        self.provider_combo.setCurrentIndex(provider_map.get(settings.get("provider"), 0))
        
        self.ai_model_input.setText(settings.get("model", ""))
        
        confidence_map = {"high": 0, "medium": 1, "low": 2}
        self.ai_confidence_combo.setCurrentIndex(confidence_map.get(settings.get("confidence_threshold"), 1))

    def _save_all_settings(self):
        """Сохраняет все настройки в config_qt.json"""
        # --- 0. Сохраняем пользовательские пути PDF ---
        custom_dirs = []
        for i in range(self.custom_paths_list.count()):
            path = self.custom_paths_list.item(i).text()
            if path:
                custom_dirs.append(path)
        
        if "pdf_search" not in self.config:
            self.config["pdf_search"] = {}
        self.config["pdf_search"]["custom_directories"] = custom_dirs
        
        # --- 1. Сохраняем API ключи в централизованную секцию ---
        self.config["api_keys"] = {
            "anthropic": self.anthropic_key_input.text().strip(),
            "openai": self.openai_key_input.text().strip(),
            "ollama_url": self.ollama_url_input.text().strip()
        }

        # --- 2. Сохраняем настройки AI классификатора ---
        # Удаляем старые ключи из секции pdf_search для очистки
        if "pdf_search" in self.config:
            self.config["pdf_search"].pop("anthropic_api_key", None)
            self.config["pdf_search"].pop("openai_api_key", None)

        ai_provider_map = {0: "anthropic", 1: "openai", 2: "ollama"}
        ai_confidence_map = {0: "high", 1: "medium", 2: "low"}
        
        ai_settings = {
            "enabled": self.config.get("ai_classifier", {}).get("enabled", False),
            "provider": ai_provider_map[self.provider_combo.currentIndex()],
            "model": self.ai_model_input.text().strip(),
            "auto_classify": self.config.get("ai_classifier", {}).get("auto_classify", False),
            "confidence_threshold": ai_confidence_map[self.ai_confidence_combo.currentIndex()],
            # ВАЖНО: секция api_keys здесь больше не нужна, т.к. они хранятся централизованно
        }
        self.config["ai_classifier"] = ai_settings
        
        # --- 3. Сохраняем весь файл config_qt.json ---
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_qt.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            if hasattr(self.parent_window, 'log_text') and self.parent_window.log_text:
                self.parent_window.log_text.append("✅ Настройки API и AI сохранены")
            
            if hasattr(self.parent_window, 'update_ai_status'):
                self.parent_window.update_ai_status()
                
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить настройки: {e}")

    def get_config(self) -> dict:
        """Возвращает обновленный конфиг"""
        return self.config


class PDFSearchSettingsDialog(QDialog):
    """Диалог настроек поиска PDF (устаревший, используйте UnifiedSettingsDialog)"""
    
    def __init__(self, parent, config: dict):
        super().__init__(parent)
        # Перенаправляем на единое окно настроек
        unified_dialog = UnifiedSettingsDialog(parent, config)
        result = unified_dialog.exec()
        # Для совместимости возвращаем конфиг
        self.config = unified_dialog.get_config() if result == QDialog.Accepted else config
        # Устанавливаем результат для этого диалога
        if result == QDialog.Accepted:
            self.accept()
        else:
            self.reject()
    
    def get_config(self) -> dict:
        """Возвращает обновленный конфиг"""
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

