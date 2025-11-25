# -*- coding: utf-8 -*-
"""
Диалоги для поиска PDF документации
"""

import os
import sys
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
from PySide6.QtCore import Qt, Signal, QThread, QUrl
from PySide6.QtGui import QFont, QTextCursor, QColor, QDesktopServices


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
        self.resize(730, 900)  # Увеличена ширина на 30% (900 -> 1170)
        
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
        
        # Папки для поиска
        path_group = QGroupBox("📂 Папки для поиска (рекурсивно)")
        path_layout = QVBoxLayout()
        
        # Список папок
        self.search_dirs_list = QListWidget()
        self.search_dirs_list.setMaximumHeight(156)  # Увеличено на 30% (120 -> 156)
        self.search_dirs_list.setToolTip("Список папок, в которых будет выполняться поиск PDF файлов\nДвойной клик по пути откроет папку в проводнике")
        # Обработчик двойного клика для открытия папки в проводнике
        self.search_dirs_list.itemDoubleClicked.connect(self.open_search_directory)
        path_layout.addWidget(self.search_dirs_list)
        
        # Кнопки управления путями
        buttons_layout = QHBoxLayout()
        
        add_dir_btn = QPushButton("➕ Добавить папку")
        add_dir_btn.clicked.connect(self.add_search_directory)
        add_dir_btn.setToolTip("Добавить временную папку для поиска")
        buttons_layout.addWidget(add_dir_btn)
        
        remove_dir_btn = QPushButton("➖ Удалить")
        remove_dir_btn.clicked.connect(self.remove_search_directory)
        remove_dir_btn.setToolTip("Удалить выбранную папку из списка")
        buttons_layout.addWidget(remove_dir_btn)
        
        save_to_config_btn = QPushButton("💾 Сохранить в конфиг")
        save_to_config_btn.clicked.connect(self.save_search_dirs_to_config)
        save_to_config_btn.setToolTip("Сохранить текущие папки в config_qt.json как пользовательские")
        buttons_layout.addWidget(save_to_config_btn)
        
        reset_btn = QPushButton("🔄 Сброс")
        reset_btn.clicked.connect(self.reset_search_directories)
        reset_btn.setToolTip("Вернуть список папок по умолчанию")
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        path_layout.addLayout(buttons_layout)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # Загружаем папки по умолчанию
        self._load_default_search_dirs()
        
        # Результаты
        results_label = QLabel("Найденные файлы:")
        results_label.setProperty("class", "bold")
        layout.addWidget(results_label)
        
        self.local_results_list = QListWidget()
        self.local_results_list.setMinimumHeight(200)  # Увеличена минимальная высота для результатов
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
        self.ai_provider_combo.addItems(["Anthropic Claude", "OpenAI GPT-4o", "Telegram Bot"])
        self.ai_provider_combo.setFixedWidth(200)
        
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.ai_provider_combo)
        provider_layout.addStretch()
        layout.addLayout(provider_layout)
        
        # === ВЫБОР ТИПА ПРОМПТА ===
        prompt_group = QGroupBox("📝 Тип запроса")
        prompt_layout = QVBoxLayout()
        
        # Выпадающий список готовых промптов
        prompt_select_layout = QHBoxLayout()
        prompt_select_label = QLabel("Готовый промпт:")
        prompt_select_label.setFixedWidth(120)
        
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItems([
            "🔧 Стандартный",
            "📋 Краткое описание ИВП",
            "📖 Развёрнутое описание ИВП",
            "🔄 Поиск аналогов",
            "📊 Сравнительный анализ",
            "✍️ Свой промпт"
        ])
        self.prompt_combo.currentIndexChanged.connect(self._on_prompt_type_changed)
        
        prompt_select_layout.addWidget(prompt_select_label)
        prompt_select_layout.addWidget(self.prompt_combo, 1)
        prompt_layout.addLayout(prompt_select_layout)
        
        # Поле для своего промпта
        self.custom_prompt_label = QLabel("Свой промпт:")
        self.custom_prompt_label.setVisible(False)
        prompt_layout.addWidget(self.custom_prompt_label)
        
        self.custom_prompt_edit = QTextEdit()
        self.custom_prompt_edit.setPlaceholderText(
            "Введите свой промпт. Используйте {component} для подстановки названия компонента.\n"
            "Например: Опиши компонент {component} и найди его аналоги..."
        )
        self.custom_prompt_edit.setMaximumHeight(100)
        self.custom_prompt_edit.setVisible(False)
        prompt_layout.addWidget(self.custom_prompt_edit)
        
        # Подсказка о текущем промпте
        self.prompt_preview_label = QLabel()
        self.prompt_preview_label.setWordWrap(True)
        self.prompt_preview_label.setStyleSheet("color: #6c7086; font-style: italic; padding: 5px;")
        self._update_prompt_preview()
        prompt_layout.addWidget(self.prompt_preview_label)
        
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        # === ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ (HINT) ===
        hint_group = QGroupBox("💡 Уточняющая подсказка (опционально)")
        hint_layout = QVBoxLayout()
        
        hint_desc = QLabel("Добавьте контекст для уменьшения ошибок AI.")
        hint_desc.setStyleSheet("color: #a6adc8; font-size: 11px;")
        hint_layout.addWidget(hint_desc)
        
        self.hint_edit = QTextEdit()
        self.hint_edit.setPlaceholderText(
            "Например: This is a frequency divider from Analog Devices"
        )
        self.hint_edit.setMaximumHeight(35)
        hint_layout.addWidget(self.hint_edit)
        
        hint_group.setLayout(hint_layout)
        layout.addWidget(hint_group)
        
        # Результаты AI поиска
        results_label = QLabel("Результаты поиска:")
        results_label.setProperty("class", "bold")
        layout.addWidget(results_label)
        
        self.ai_results_browser = QTextBrowser()
        self.ai_results_browser.setMinimumHeight(250)  # Увеличенная зона результатов
        # Отключаем внутреннюю навигацию, открываем ссылки во внешнем браузере
        self.ai_results_browser.setOpenExternalLinks(False)
        self.ai_results_browser.setOpenLinks(False)
        self.ai_results_browser.anchorClicked.connect(self._open_external_link)
        layout.addWidget(self.ai_results_browser, 1)  # stretch factor для растяжения
        
        # Кнопка сохранения
        save_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить результат")
        save_btn.clicked.connect(self.save_ai_results)
        save_layout.addWidget(save_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        return widget
    
    def _on_prompt_type_changed(self, index: int):
        """Обработчик смены типа промпта"""
        is_custom = index == 5  # "Свой промпт"
        self.custom_prompt_label.setVisible(is_custom)
        self.custom_prompt_edit.setVisible(is_custom)
        self._update_prompt_preview()
    
    def _update_prompt_preview(self):
        """Обновляет превью промпта"""
        index = self.prompt_combo.currentIndex()
        previews = [
            "Стандартный запрос: полное название, характеристики, описание, примеры использования, ссылка на PDF",
            "Краткое описание: техническая справка с характеристиками и обоснованием невозможности замены на отечественные аналоги",
            "Развёрнутый обзор: подробный анализ даташита на 200-400 слов с ключевыми параметрами",
            "Поиск аналогов: список совместимых замен с ссылками на производителей",
            "Сравнительный анализ: таблица сравнения с конкурирующими решениями",
            "Введите свой текст запроса выше. Используйте {component} для названия компонента"
        ]
        self.prompt_preview_label.setText(f"ℹ️ {previews[index]}")
    
    def _get_prompt_template(self, component_name: str) -> str:
        """Возвращает промпт на основе выбранного типа с учётом подсказки"""
        index = self.prompt_combo.currentIndex()
        
        # Получаем уточняющую подсказку (hint)
        hint = ""
        if hasattr(self, 'hint_edit'):
            hint = self.hint_edit.toPlainText().strip()
        
        prompts = {
            0: f"""Найди информацию об электронном компоненте: {component_name}

Пожалуйста, предоставь следующую информацию в структурированном виде:

1. Полное название и производитель
2. Тип компонента (микросхема, резистор, конденсатор и т.д.)
3. Основные характеристики (напряжение, ток, частота, корпус и т.д.)
4. Краткое описание назначения
5. Типичные примеры использования (2-3 примера)
6. Прямая ссылка на PDF документацию (желательно с официального сайта производителя)

Формат ответа: JSON
{{
    "found": true/false,
    "full_name": "полное название",
    "manufacturer": "производитель",
    "type": "тип компонента",
    "description": "описание",
    "specifications": {{"key": "value"}},
    "examples": ["пример 1", "пример 2"],
    "datasheet_url": "https://..."
}}""",

            1: f"""Составь краткое техническое описание источника вторичного питания (ИВП) или DC-DC преобразователя: {component_name}

Требуется:
1. Полное название компонента и производитель
2. Тип (понижающий/повышающий/инвертирующий DC-DC, LDO, POL и т.д.)
3. Основные технические характеристики:
   - Входное напряжение (Vin)
   - Выходное напряжение (Vout)
   - Максимальный выходной ток
   - КПД (эффективность)
   - Частота преобразования
   - Тип корпуса
4. Ключевые преимущества данного компонента
5. ВАЖНО: Обоснование невозможности или нецелесообразности замены на отечественные аналоги:
   - Отсутствие российских аналогов с такими же параметрами
   - Технологические ограничения отечественных производителей
   - Сертификация и надёжность оригинального компонента

Формат: структурированный текст на русском языке (150-200 слов)""",

            2: f"""Подготовь развёрнутое описание источника вторичного питания (ИВП) или DC-DC преобразователя: {component_name}

Сделай обзор на основе официального даташита производителя. Описание должно включать:

1. ОБЩАЯ ИНФОРМАЦИЯ
   - Полное название и серия
   - Производитель и страна происхождения
   - Целевое применение

2. ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ
   - Диапазон входных напряжений
   - Выходные параметры (напряжение, ток, мощность)
   - КПД в различных режимах работы
   - Частота преобразования
   - Защитные функции (OVP, OCP, OTP, UVLO)
   - Температурный диапазон работы

3. КОНСТРУКТИВНЫЕ ОСОБЕННОСТИ
   - Тип и размеры корпуса
   - Требования к внешним компонентам
   - Тепловые характеристики

4. ПРЕИМУЩЕСТВА И ОСОБЕННОСТИ
   - Уникальные технологические решения
   - Сравнение с предыдущими поколениями

5. РЕКОМЕНДАЦИИ ПО ПРИМЕНЕНИЮ
   - Типовые схемы включения
   - Области применения

Объём: 200-400 слов. Язык: русский.""",

            3: f"""Найди все существующие аналоги для компонента: {component_name}

Требуется предоставить:

1. ПРЯМЫЕ АНАЛОГИ (pin-to-pin совместимые)
   - Название компонента
   - Производитель
   - Ссылка на страницу продукта или даташит
   - Степень совместимости (полная/частичная)

2. ФУНКЦИОНАЛЬНЫЕ АНАЛОГИ (похожие характеристики)
   - Название компонента
   - Производитель
   - Основные отличия от оригинала
   - Ссылка на документацию

3. БЮДЖЕТНЫЕ АЛЬТЕРНАТИВЫ
   - Более дешёвые варианты
   - Компромиссы по характеристикам

4. ПРЕМИУМ АЛЬТЕРНАТИВЫ
   - Улучшенные версии
   - Дополнительные функции

Для каждого аналога укажи:
- Прямую ссылку на сайт производителя
- Ссылку на PDF даташит (если доступна)
- Ориентировочную доступность на рынке

Формат: структурированный список с активными ссылками""",

            4: f"""Проведи сравнительный анализ компонента {component_name} с конкурирующими решениями.

Требуется:

1. ИДЕНТИФИКАЦИЯ КОМПОНЕНТА
   - Полное название и производитель
   - Категория/класс устройства
   - Целевой сегмент рынка

2. ОСНОВНЫЕ КОНКУРЕНТЫ
   Выбери 3-5 ближайших конкурентов от разных производителей

3. СРАВНИТЕЛЬНАЯ ТАБЛИЦА
   | Параметр | {component_name} | Конкурент 1 | Конкурент 2 | Конкурент 3 |
   |----------|------------------|-------------|-------------|-------------|
   | Производитель | | | | |
   | Входное напряжение | | | | |
   | Выходное напряжение | | | | |
   | Выходной ток | | | | |
   | КПД | | | | |
   | Частота | | | | |
   | Корпус | | | | |
   | Цена (ориентир.) | | | | |

4. ВЫВОДЫ
   - Преимущества анализируемого компонента
   - Недостатки по сравнению с конкурентами
   - Рекомендации по выбору

Язык: русский"""
        }
        
        # Получаем базовый промпт
        if index == 5:  # Свой промпт
            custom = self.custom_prompt_edit.toPlainText().strip()
            if custom:
                base_prompt = custom.replace("{component}", component_name)
            else:
                base_prompt = prompts[0]  # Fallback на стандартный
        else:
            base_prompt = prompts.get(index, prompts[0])
        
        # Добавляем уточняющую подсказку, если она есть
        if hint:
            hint_instruction = f"""

ВАЖНАЯ ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ от пользователя (учитывай при ответе):
{hint}

ОБЯЗАТЕЛЬНО: Ответ должен быть ТОЛЬКО на русском языке, независимо от языка подсказки выше."""
            return base_prompt + hint_instruction
        
        return base_prompt
    
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
        from .pdf_search import LocalPDFSearcher
        
        # Получаем список папок из интерфейса
        search_dirs = []
        for i in range(self.search_dirs_list.count()):
            item = self.search_dirs_list.item(i)
            path = item.data(Qt.UserRole)
            if path and os.path.exists(path):
                search_dirs.append(path)
        
        if not search_dirs:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Список папок для поиска пуст!\n\n"
                "Нажмите '🔄 Сброс' для загрузки папок по умолчанию\n"
                "или '➕ Добавить папку' для выбора своей папки."
            )
            return
        
        # Выполняем поиск во всех директориях
        all_results = []
        for directory in search_dirs:
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
            item = QListWidgetItem(f"❌ Файлы не найдены в {len(search_dirs)} папках")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.local_results_list.addItem(item)
        else:
            # Добавляем заголовок с количеством результатов
            header = QListWidgetItem(f"✅ Найдено {len(unique_results)} файлов в {len(search_dirs)} папках:")
            header.setFlags(header.flags() & ~Qt.ItemIsEnabled)
            header.setBackground(QColor("#313244"))
            self.local_results_list.addItem(header)
            
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
        api_url = None
        
        if "Anthropic" in provider:
            api_key = api_keys.get("anthropic")
            provider_name = "anthropic"
        elif "Telegram" in provider:
            api_key = api_keys.get("telegram_key")
            api_url = api_keys.get("telegram_url")
            provider_name = "telegram_bot"
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
        
        # Получаем промпт на основе выбранного типа
        custom_prompt = self._get_prompt_template(query)
        prompt_type = self.prompt_combo.currentText()
        
        # Проверяем наличие подсказки
        hint = ""
        if hasattr(self, 'hint_edit'):
            hint = self.hint_edit.toPlainText().strip()
        
        # Показываем индикатор загрузки с информацией о типе запроса
        hint_info = f"<p style='color: #a6e3a1;'>💡 Подсказка: {hint[:50]}{'...' if len(hint) > 50 else ''}</p>" if hint else ""
        self.ai_results_browser.setHtml(
            f"<h3>⏳ Поиск...</h3>"
            f"<p>Запрашиваем информацию у AI...</p>"
            f"<p style='color: #6c7086;'>Тип запроса: {prompt_type}</p>"
            f"<p style='color: #6c7086;'>Компонент: {query}</p>"
            f"{hint_info}"
        )
        
        # Запускаем поиск в отдельном потоке с кастомным промптом
        self.ai_worker = AISearchWorker(provider_name, api_key, query, api_url, custom_prompt)
        self.ai_worker.finished.connect(self.display_ai_results)
        self.ai_worker.start()
    
    def _open_external_link(self, url: QUrl):
        """Открывает ссылку во внешнем браузере"""
        QDesktopServices.openUrl(url)
    
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
        
        # Базовые стили
        html = """
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; }
            h2 { color: #89b4fa; border-bottom: 2px solid #89b4fa; padding-bottom: 5px; }
            h3 { color: #a6e3a1; margin-top: 20px; }
            .spec-table { border-collapse: collapse; width: 100%; margin: 10px 0; }
            .spec-table td { padding: 8px; border: 1px solid #45475a; }
            .spec-table td:first-child { font-weight: bold; background-color: #313244; width: 30%; }
            .example { background-color: #1e1e2e; padding: 10px; margin: 5px 0; border-left: 3px solid #a6e3a1; }
            .datasheet-link { 
                display: inline-block;
                background-color: #89b4fa;
                color: #1e1e2e;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
            }
            .datasheet-link:hover { background-color: #74c7ec; }
            .text-response { 
                background-color: #1e1e2e; 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 4px solid #89b4fa;
                white-space: pre-wrap;
                font-size: 14px;
            }
            .text-response p { margin: 10px 0; }
            .text-response ul, .text-response ol { margin: 10px 0; padding-left: 20px; }
            .text-response li { margin: 5px 0; }
            a { color: #89b4fa; }
        </style>
        """
        
        # Проверяем, есть ли структурированные данные или только текст
        has_structured_data = any(key in results for key in ['full_name', 'manufacturer', 'type', 'specifications'])
        raw_response = results.get('raw_response', '')
        description = results.get('description', '')
        
        # Если есть только текстовый ответ (raw_response или description), показываем его красиво
        if not has_structured_data and (raw_response or description):
            text_content = raw_response or description
            
            # Преобразуем markdown-подобное форматирование в HTML
            formatted_text = self._format_markdown_to_html(text_content)
            
            html += f"""
            <h2>📋 {results.get('component', 'Компонент')}</h2>
            <div class="text-response">{formatted_text}</div>
            """
        else:
            # Стандартное структурированное отображение
            html += f"""
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
            <p>{description or 'Описание отсутствует'}</p>
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
    
    def _format_markdown_to_html(self, text: str) -> str:
        """Преобразует markdown-подобный текст в HTML"""
        import re
        
        # Экранируем HTML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Заголовки
        text = re.sub(r'^### (.+)$', r'<h4 style="color: #cba6f7;">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        
        # Жирный и курсив
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        
        # Ссылки
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
        
        # URL без разметки
        text = re.sub(
            r'(https?://[^\s<>\"\)]+)',
            r'<a href="\1" target="_blank">\1</a>',
            text
        )
        
        # Списки с тире
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'(<li>.+</li>\n?)+', r'<ul>\g<0></ul>', text)
        
        # Нумерованные списки
        text = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', text, flags=re.MULTILINE)
        
        # Параграфы (двойные переносы)
        text = re.sub(r'\n\n+', '</p><p>', text)
        text = f'<p>{text}</p>'
        
        # Одиночные переносы строк
        text = text.replace('\n', '<br>')
        
        return text
    
    def _load_default_search_dirs(self):
        """Загружает папки для поиска по умолчанию"""
        from .pdf_search import get_default_pdf_directories
        
        self.search_dirs_list.clear()
        
        # Получаем пользовательские папки из конфига
        custom_dirs_from_config = self.config.get("pdf_search", {}).get("custom_directories", [])
        
        # Получаем все папки (включая пользовательские)
        all_dirs = get_default_pdf_directories(self.config)
        
        for directory in all_dirs:
            if os.path.exists(directory):
                # Проверяем, это пользовательская папка или системная
                is_custom = directory in custom_dirs_from_config
                
                # Добавляем иконку в зависимости от типа папки
                if is_custom:
                    icon = "👤"  # Пользовательская папка
                elif "pdf" in os.path.basename(directory).lower():
                    icon = "📄"
                elif "Project" in directory:
                    icon = "📁"
                elif "component_database" in directory or "BOMCategorizer" in directory:
                    icon = "💾"
                else:
                    icon = "📂"
                
                item_text = f"{icon} {directory}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, directory)
                item.setData(Qt.UserRole + 1, is_custom)  # Флаг: пользовательская папка
                
                tooltip = directory
                if is_custom:
                    tooltip += "\n(Пользовательская папка)"
                else:
                    tooltip += "\n(Системная папка по умолчанию)"
                item.setToolTip(tooltip)
                
                self.search_dirs_list.addItem(item)
        
        # Если список пустой, показываем предупреждение
        if self.search_dirs_list.count() == 0:
            item = QListWidgetItem("⚠️ Папки для поиска не найдены")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.search_dirs_list.addItem(item)
    
    def add_search_directory(self):
        """Добавляет новую папку для поиска"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для поиска PDF",
            ""
        )
        
        if folder:
            # Проверяем, не добавлена ли уже эта папка
            for i in range(self.search_dirs_list.count()):
                item = self.search_dirs_list.item(i)
                existing_path = item.data(Qt.UserRole)
                if existing_path == folder:
                    QMessageBox.information(
                        self,
                        "Информация",
                        "Эта папка уже есть в списке!"
                    )
                    return
            
            # Добавляем новую пользовательскую папку
            item_text = f"👤 {folder}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, folder)
            item.setData(Qt.UserRole + 1, True)  # Помечаем как пользовательскую
            item.setToolTip(f"{folder}\n(Пользовательская папка - временно)")
            self.search_dirs_list.addItem(item)
    
    def remove_search_directory(self):
        """Удаляет выбранную папку из списка"""
        current_item = self.search_dirs_list.currentItem()
        if current_item:
            self.search_dirs_list.takeItem(self.search_dirs_list.row(current_item))
        else:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Выберите папку для удаления!"
            )
    
    def reset_search_directories(self):
        """Сбрасывает список папок к значениям по умолчанию"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вернуть список папок к значениям по умолчанию?\n\n"
            "Все временно добавленные папки будут удалены.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._load_default_search_dirs()
    
    def save_search_dirs_to_config(self):
        """Сохраняет ТОЛЬКО пользовательские папки в config_qt.json"""
        # Собираем ТОЛЬКО пользовательские папки (с флагом is_custom = True)
        custom_dirs = []
        
        for i in range(self.search_dirs_list.count()):
            item = self.search_dirs_list.item(i)
            path = item.data(Qt.UserRole)
            is_custom = item.data(Qt.UserRole + 1)  # Флаг пользовательской папки
            
            if path and os.path.exists(path) and is_custom:
                # Нормализуем путь (убираем лишние слэши, приводим к абсолютному)
                normalized_path = os.path.normpath(os.path.abspath(path))
                custom_dirs.append(normalized_path)
        
        # Сохраняем файл - используем ту же логику, что и load_config()
        try:
            # Используем функцию get_config_path() из main_window
            from .main_window import get_config_path
            config_path = get_config_path()
            
            # Загружаем текущий конфиг из файла, чтобы сохранить все остальные настройки
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
            except FileNotFoundError:
                # Если файла нет, используем текущий конфиг
                full_config = self.config.copy()
            except Exception as e:
                # Если ошибка чтения, используем текущий конфиг
                print(f"Ошибка чтения конфига: {e}")
                full_config = self.config.copy()
            
            # Обновляем только секцию pdf_search
            if "pdf_search" not in full_config:
                full_config["pdf_search"] = {}
            full_config["pdf_search"]["custom_directories"] = custom_dirs
            
            # Создаем папку, если её нет
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # Сохраняем весь конфиг
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2, ensure_ascii=False)
            
            # Формируем сообщение с путем к файлу
            if custom_dirs:
                msg = (f"✅ Сохранено {len(custom_dirs)} пользовательских папок в config_qt.json\n\n"
                       f"📁 Путь к файлу:\n{config_path}\n\n"
                       "Папки:\n" + "\n".join([f"  👤 {d}" for d in custom_dirs[:5]]) + 
                       (f"\n  ... и еще {len(custom_dirs) - 5}" if len(custom_dirs) > 5 else "") +
                       "\n\nСистемные папки (💾 📄 📁) не сохраняются - "
                       "они используются автоматически.")
            else:
                msg = (f"⚠️ Нет пользовательских папок для сохранения\n\n"
                       f"📁 Путь к файлу:\n{config_path}\n\n"
                       "Добавьте папки кнопкой ➕ - они будут помечены иконкой 👤\n"
                       "Системные папки (💾 📄 📁) сохранять не нужно.")
            
            QMessageBox.information(self, "Сохранено", msg)
            
            # Обновляем конфиг в памяти
            self.config = full_config
            
            # Обновляем конфиг в родительском окне
            if hasattr(self.parent_window, 'cfg'):
                self.parent_window.cfg = full_config
                self.parent_window.config = full_config  # Псевдоним для совместимости
            
            # Перезагружаем список, чтобы показать обновленные данные
            self._load_default_search_dirs()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось сохранить конфигурацию:\n{str(e)}\n\n"
                f"Путь: {config_path if 'config_path' in locals() else 'не определен'}"
            )
    
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
    
    def open_search_directory(self, item: QListWidgetItem):
        """Открывает папку из списка поиска в проводнике/файловом менеджере"""
        directory = item.data(Qt.UserRole)
        if directory and os.path.exists(directory) and os.path.isdir(directory):
            self._open_file_in_system(directory)
        else:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Папка не найдена или недоступна:\n{directory}"
            )
    
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
        
        filters = (
            "HTML Files (*.html);;"
            "Text Files (*.txt);;"
            "Word Document (*.docx);;"
            "PDF (*.pdf)"
        )
        
        # Формируем безопасное имя файла (убираем спецсимволы)
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in self.search_input.text())
        
        # Начальный путь — рабочий стол или домашняя директория
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.expanduser("~")
        
        default_path = os.path.join(desktop, f"ai_search_{safe_name}.html")
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты",
            default_path,
            filters
        )
        
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            
            if not ext:
                # Определяем расширение по выбранному фильтру
                if "Text Files" in selected_filter:
                    ext = ".txt"
                elif "Word Document" in selected_filter:
                    ext = ".docx"
                elif "PDF" in selected_filter:
                    ext = ".pdf"
                else:
                    ext = ".html"
                file_path += ext
            
            try:
                if ext == ".html":
                    content = self.ai_results_browser.toHtml()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                elif ext == ".txt":
                    content = self.ai_results_browser.toPlainText()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                elif ext == ".docx":
                    try:
                        from docx import Document
                    except ImportError:
                        QMessageBox.warning(
                            self,
                            "Отсутствует зависимость",
                            "Для сохранения в DOCX требуется пакет python-docx.\n"
                            "Установите его командой:\n\npip install python-docx"
                        )
                        return
                    
                    doc = Document()
                    doc.add_heading(f"AI поиск — {self.search_input.text()}", level=1)
                    for line in self.ai_results_browser.toPlainText().splitlines():
                        doc.add_paragraph(line if line else "")
                    doc.save(file_path)
                elif ext == ".pdf":
                    try:
                        from reportlab.lib.pagesizes import A4
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                        from reportlab.lib.styles import ParagraphStyle
                        from reportlab.lib.units import mm
                    except ImportError:
                        QMessageBox.warning(
                            self,
                            "Отсутствует зависимость",
                            "Для сохранения в PDF требуется пакет reportlab.\n"
                            "Установите его командой:\n\npip install reportlab"
                        )
                        return
                    
                    # Используем PDFExporter для правильной регистрации шрифтов
                    try:
                        from ..pdf_exporter import PDFExporter
                        pdf_exporter = PDFExporter()
                        font_name = pdf_exporter.cyrillic_font
                    except Exception as e:
                        print(f"Ошибка при инициализации PDFExporter: {e}")
                        font_name = 'Helvetica'
                    
                    # Создаём PDF документ
                    doc = SimpleDocTemplate(
                        file_path,
                        pagesize=A4,
                        leftMargin=15*mm,
                        rightMargin=15*mm,
                        topMargin=15*mm,
                        bottomMargin=15*mm
                    )
                    
                    # Стили
                    title_style = ParagraphStyle(
                        'Title',
                        fontName=font_name,
                        fontSize=12,
                        leading=14,
                        spaceAfter=10
                    )
                    
                    body_style = ParagraphStyle(
                        'Body',
                        fontName=font_name,
                        fontSize=9,
                        leading=11,
                        spaceAfter=3
                    )
                    
                    # Содержимое
                    story = []
                    
                    # Заголовок
                    title = f"AI поиск: {self.search_input.text()}"
                    story.append(Paragraph(title, title_style))
                    story.append(Spacer(1, 10))
                    
                    # Текст результатов
                    text = self.ai_results_browser.toPlainText()
                    for line in text.splitlines():
                        if line.strip():
                            # Экранируем HTML-специальные символы
                            safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            story.append(Paragraph(safe_line, body_style))
                        else:
                            story.append(Spacer(1, 6))
                    
                    doc.build(story)
                else:
                    QMessageBox.warning(self, "Неизвестный формат", f"Расширение {ext} не поддерживается.")
                    return
                
                QMessageBox.information(self, "Сохранено", f"Результаты сохранены:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось сохранить файл:\n{e}")
    
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
        
        # Используем новое единое окно настроек напрямую
        dialog = UnifiedSettingsDialog(self, self.config)
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
        self.resize(730, 550)
        
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

        # Telegram Bot
        telegram_group = QGroupBox("Настройки Telegram Bot API")
        telegram_layout = QGridLayout()

        telegram_url_label = QLabel("Bot API URL:")
        self.telegram_url_input = QLineEdit()
        self.telegram_url_input.setPlaceholderText("http://localhost:8000/ai_query")
        
        telegram_key_label = QLabel("Bot API Key:")
        self.telegram_key_input = QLineEdit()
        self.telegram_key_input.setEchoMode(QLineEdit.Password)
        self.telegram_key_input.setPlaceholderText("secret_key")
        
        show_telegram_btn = QCheckBox("Показать")
        show_telegram_btn.stateChanged.connect(
            lambda state: self.telegram_key_input.setEchoMode(
                QLineEdit.Normal if state else QLineEdit.Password
            )
        )

        telegram_layout.addWidget(telegram_url_label, 0, 0)
        telegram_layout.addWidget(self.telegram_url_input, 0, 1)
        telegram_layout.addWidget(telegram_key_label, 1, 0)
        telegram_layout.addWidget(self.telegram_key_input, 1, 1)
        telegram_layout.addWidget(show_telegram_btn, 1, 2)

        telegram_group.setLayout(telegram_layout)
        layout.addWidget(telegram_group)
        
        # Помощь
        help_label = QLabel(
            "💡 <b>Как получить API ключи:</b><br>"
            "• <b>Anthropic:</b> <a href='https://console.anthropic.com/'>console.anthropic.com</a><br>"
            "• <b>OpenAI:</b> <a href='https://platform.openai.com/api-keys'>platform.openai.com/api-keys</a><br>"
            "• <b>Ollama:</b> <a href='https://ollama.ai/'>ollama.ai</a> (для локального запуска)<br>"
            "• <b>Telegram Bot:</b> команда <code>/api</code> в боте (только для админа)"
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
        
        # Telegram Bot
        telegram_url = api_keys.get("telegram_url") or "http://localhost:8000/ai_query"
        self.telegram_url_input.setText(telegram_url)
        
        telegram_key = api_keys.get("telegram_key") or ""
        self.telegram_key_input.setText(telegram_key)
        
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
            "ollama_url": self.ollama_url_input.text().strip(),
            "telegram_url": self.telegram_url_input.text().strip(),
            "telegram_key": self.telegram_key_input.text().strip()
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
            # __file__ = bom_categorizer/gui/pdf_search_dialogs.py
            # Нужно 3 уровня вверх: gui -> bom_categorizer -> корень проекта
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, "config_qt.json")
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
    
    def __init__(self, provider: str, api_key: str, query: str, api_url: str = None, custom_prompt: str = None):
        super().__init__()
        self.provider = provider
        self.api_key = api_key
        self.query = query
        self.api_url = api_url
        self.custom_prompt = custom_prompt
    
    def run(self):
        """Выполняет AI поиск"""
        from .pdf_search import AIPDFSearcher
        
        searcher = AIPDFSearcher(self.provider, self.api_key, self.api_url)
        
        # Используем кастомный промпт если передан
        if self.custom_prompt:
            results = searcher.search_with_prompt(self.query, self.custom_prompt)
        else:
            results = searcher.search(self.query)
        
        self.finished.emit(results)

