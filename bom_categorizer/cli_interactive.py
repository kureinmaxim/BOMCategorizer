# -*- coding: utf-8 -*-
"""
Интерактивный CLI режим для BOM Categorizer

Расширенная командная строка с автодополнением и историей команд.
Доступна только в экспертном режиме.
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QLineEdit, QPushButton, QLabel, QCompleter)
from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtGui import QFont, QTextCursor, QColor


class CLICommand:
    """Базовый класс для CLI команд"""
    
    def __init__(self, name: str, description: str, usage: str, handler: Callable):
        self.name = name
        self.description = description
        self.usage = usage
        self.handler = handler
        self.aliases = []
    
    def add_alias(self, alias: str):
        """Добавляет алиас для команды"""
        self.aliases.append(alias)
        return self


class InteractiveCLI(QWidget):
    """Виджет интерактивной командной строки"""
    
    command_executed = Signal(str, str)  # (command, result)
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.command_history = []
        self.history_index = -1
        self.commands = {}
        
        # Получаем scale_factor от главного окна и увеличиваем на 20%
        base_scale = getattr(main_window, 'scale_factor', 1.0)
        self.scale_factor = base_scale * 1.4
        
        self._setup_ui()
        self._register_commands()
        self._print_welcome()
    
    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок
        header = QLabel("💻 Интерактивная командная строка")
        header_font_size = int(14 * self.scale_factor)
        header.setStyleSheet(f"font-weight: bold; font-size: {header_font_size}px; padding: 5px;")
        layout.addWidget(header)
        
        # Область вывода
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        output_font_size = max(8, int(10 * self.scale_factor))
        self.output_area.setFont(QFont("Consolas", output_font_size))
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 2px solid #45475a;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.output_area)
        
        # Поле ввода команды
        input_layout = QHBoxLayout()
        
        self.prompt_label = QLabel(">>>")
        prompt_font_size = max(8, int(14 * self.scale_factor))
        self.prompt_label.setStyleSheet(f"color: #89b4fa; font-weight: bold; font-family: Consolas; font-size: {prompt_font_size}pt;")
        input_layout.addWidget(self.prompt_label)
        
        self.input_field = QLineEdit()
        input_font_size = max(8, int(10 * self.scale_factor))
        self.input_field.setFont(QFont("Consolas", input_font_size))
        self.input_field.setPlaceholderText("Введите команду (help для справки)...")
        self.input_field.returnPressed.connect(self._execute_command)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 2px solid #45475a;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
        """)
        input_layout.addWidget(self.input_field)
        
        # Кнопка выполнения
        exec_button = QPushButton("Выполнить")
        exec_button.clicked.connect(self._execute_command)
        exec_button.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a6c9ff;
            }
        """)
        input_layout.addWidget(exec_button)
        
        layout.addLayout(input_layout)
        
        # Автодополнение с улучшенными настройками
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchStartsWith)  # Фильтр по началу
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)  # Popup меню
        self.completer.setMaxVisibleItems(10)  # Максимум 10 подсказок
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.input_field.setCompleter(self.completer)
        
        # Стилизация popup автодополнения
        popup = self.completer.popup()
        popup.setStyleSheet("""
            QListView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #585b70;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                padding: 4px;
            }
            QListView::item {
                padding: 4px 8px;
                border-radius: 3px;
            }
            QListView::item:selected {
                background-color: #45475a;
                color: #f5c2e7;
            }
            QListView::item:hover {
                background-color: #313244;
            }
        """)
        
        # Обработка истории (стрелки вверх/вниз) и автодополнения
        self.input_field.installEventFilter(self)
        
        # Обновление автодополнения при вводе
        self.input_field.textChanged.connect(self._on_text_changed)
    
    def eventFilter(self, obj, event):
        """Фильтр событий для истории команд и автодополнения"""
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            popup_visible = self.completer.popup().isVisible()
            
            # Если popup открыт, стрелки управляют им
            if popup_visible:
                if event.key() == Qt.Key_Up:
                    # Перемещаем выбор вверх в popup
                    current = self.completer.popup().currentIndex()
                    if current.row() > 0:
                        new_index = self.completer_model.index(current.row() - 1)
                        self.completer.popup().setCurrentIndex(new_index)
                    return True
                elif event.key() == Qt.Key_Down:
                    # Перемещаем выбор вниз в popup
                    current = self.completer.popup().currentIndex()
                    row_count = self.completer_model.rowCount()
                    if current.row() < row_count - 1:
                        new_index = self.completer_model.index(current.row() + 1)
                        self.completer.popup().setCurrentIndex(new_index)
                    return True
                elif event.key() == Qt.Key_Escape:
                    self.completer.popup().hide()
                    return True
            else:
                # История команд (если popup закрыт)
                if event.key() == Qt.Key_Up:
                    self._history_up()
                    return True
                elif event.key() == Qt.Key_Down:
                    self._history_down()
                    return True
            
            # Автодополнение по Tab или стрелке вправо
            if event.key() == Qt.Key_Tab:
                self._accept_completion()
                return True
            elif event.key() == Qt.Key_Right:
                # Стрелка вправо принимает автодополнение только если курсор в конце
                if self.input_field.cursorPosition() == len(self.input_field.text()):
                    if self._accept_completion():
                        return True
        return super().eventFilter(obj, event)
    
    def _accept_completion(self) -> bool:
        """Принимает текущее автодополнение"""
        # Если popup открыт и есть выбранный элемент
        if self.completer.popup().isVisible():
            current_index = self.completer.popup().currentIndex()
            if current_index.isValid():
                completion = self.completer.currentCompletion()
                if completion:
                    self.input_field.setText(completion)
                    self.input_field.setCursorPosition(len(completion))
                    self.completer.popup().hide()
                    return True
        
        # Fallback - ищем первое совпадение вручную
        current_text = self.input_field.text().strip().lower()
        if not current_text:
            return False
        
        # Ищем первое совпадение
        all_commands = list(self.commands.keys())
        for cmd in self.commands.values():
            all_commands.extend(cmd.aliases)
        
        for cmd in sorted(set(all_commands)):
            if cmd.startswith(current_text) and cmd != current_text:
                self.input_field.setText(cmd)
                self.input_field.setCursorPosition(len(cmd))
                return True
        
        return False
    
    def _on_text_changed(self, text: str):
        """Обработчик изменения текста - показывает автодополнение"""
        text = text.strip().lower()
        if not text:
            self.completer.popup().hide()
            return
        
        # Проверяем, есть ли совпадения
        all_commands = list(self.commands.keys())
        for cmd in self.commands.values():
            all_commands.extend(cmd.aliases)
        
        matches = [cmd for cmd in sorted(set(all_commands)) if cmd.startswith(text)]
        
        if matches and len(matches) > 0 and text not in matches:
            # Показываем popup если есть совпадения и текст не точное совпадение
            self.completer.complete()
        else:
            self.completer.popup().hide()
    
    def _history_up(self):
        """Навигация по истории вверх"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input_field.setText(self.command_history[-(self.history_index + 1)])
    
    def _history_down(self):
        """Навигация по истории вниз"""
        if self.history_index > 0:
            self.history_index -= 1
            self.input_field.setText(self.command_history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self.input_field.clear()
    
    def _print_welcome(self):
        """Выводит приветственное сообщение"""
        welcome = f"""
╔═══════════════════════════════════════════════════════════════╗
║  💻 BOM Categorizer - Интерактивный CLI режим                 ║
║  Версия: {self.main_window.cfg.get('app_info', {}).get('version', 'dev')}                                                  ║
╚═══════════════════════════════════════════════════════════════╝

Добро пожаловать в расширенную командную строку!

Введите 'help' для списка доступных команд.
Используйте ↑↓ для навигации по истории команд.
Используйте Tab для автодополнения команд.

"""
        self._print(welcome, color="#89b4fa")
    
    def _print(self, text: str, color: str = "#cdd6f4"):
        """Выводит текст в область вывода"""
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Устанавливаем цвет
        format = cursor.charFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        
        cursor.insertText(text + "\n")
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()
    
    def _execute_command(self):
        """Выполняет введенную команду"""
        command_line = self.input_field.text().strip()
        if not command_line:
            return
        
        # Добавляем в историю
        self.command_history.append(command_line)
        self.history_index = -1
        
        # Выводим команду
        self._print(f">>> {command_line}", color="#f9e2af")
        
        # Парсим команду
        parts = command_line.split()
        command_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Ищем команду
        command = self.commands.get(command_name)
        if not command:
            # Проверяем алиасы
            for cmd in self.commands.values():
                if command_name in cmd.aliases:
                    command = cmd
                    break
        
        if command:
            try:
                result = command.handler(args)
                if result:
                    self._print(result, color="#a6e3a1")
            except Exception as e:
                self._print(f"❌ Ошибка выполнения: {e}", color="#f38ba8")
        else:
            self._print(f"❌ Неизвестная команда: {command_name}", color="#f38ba8")
            self._print("   Введите 'help' для списка команд.", color="#6c7086")
        
        # Очищаем поле ввода
        self.input_field.clear()
        
        # Эмитим сигнал
        self.command_executed.emit(command_line, "OK")
    
    def _register_commands(self):
        """Регистрирует все доступные команды"""
        
        # === ОБЩИЕ КОМАНДЫ ===
        
        self.commands["help"] = CLICommand(
            "help",
            "Показывает список всех доступных команд",
            "help [команда]",
            self._cmd_help
        ).add_alias("?")
        
        self.commands["clear"] = CLICommand(
            "clear",
            "Очищает экран консоли",
            "clear",
            self._cmd_clear
        ).add_alias("cls")
        
        self.commands["exit"] = CLICommand(
            "exit",
            "Закрывает CLI консоль",
            "exit",
            self._cmd_exit
        ).add_alias("quit")
        
        self.commands["history"] = CLICommand(
            "history",
            "Показывает историю команд",
            "history",
            self._cmd_history
        )
        
        # === КОМАНДЫ ФАЙЛОВ ===
        
        self.commands["list"] = CLICommand(
            "list",
            "Показывает список входных файлов",
            "list",
            self._cmd_list_files
        ).add_alias("ls")
        
        self.commands["add"] = CLICommand(
            "add",
            "Добавляет файл в список обработки",
            "add <путь_к_файлу>",
            self._cmd_add_file
        )
        
        self.commands["remove"] = CLICommand(
            "remove",
            "Удаляет файл из списка",
            "remove <индекс|путь>",
            self._cmd_remove_file
        ).add_alias("rm")
        
        self.commands["process"] = CLICommand(
            "process",
            "Запускает обработку файлов",
            "process",
            self._cmd_process
        ).add_alias("run")
        
        # === КОМАНДЫ БАЗЫ ДАННЫХ ===
        
        self.commands["dbstats"] = CLICommand(
            "dbstats",
            "Показывает статистику базы данных",
            "dbstats",
            self._cmd_db_stats
        )
        
        self.commands["dbsearch"] = CLICommand(
            "dbsearch",
            "Поиск компонента в базе данных",
            "dbsearch <название>",
            self._cmd_db_search
        ).add_alias("search")
        
        self.commands["dbexport"] = CLICommand(
            "dbexport",
            "Экспортирует базу данных в Excel",
            "dbexport [путь]",
            self._cmd_db_export
        )
        
        self.commands["dbbackup"] = CLICommand(
            "dbbackup",
            "Создает резервную копию БД",
            "dbbackup",
            self._cmd_db_backup
        )
        
        # === СИСТЕМНЫЕ КОМАНДЫ ===
        
        self.commands["status"] = CLICommand(
            "status",
            "Показывает текущий статус приложения",
            "status",
            self._cmd_status
        )
        
        self.commands["config"] = CLICommand(
            "config",
            "Показывает конфигурацию",
            "config [параметр]",
            self._cmd_config
        )
        
        self.commands["theme"] = CLICommand(
            "theme",
            "Переключает тему интерфейса",
            "theme [dark|light]",
            self._cmd_theme
        )
        
        self.commands["scale"] = CLICommand(
            "scale",
            "Изменяет масштаб интерфейса",
            "scale <0.7-1.25>",
            self._cmd_scale
        )
        
        # === КОМАНДЫ СИНХРОНИЗАЦИИ ===
        
        self.commands["version"] = CLICommand(
            "version",
            "Показывает версии приложения",
            "version",
            self._cmd_version
        ).add_alias("ver")
        
        self.commands["vsync"] = CLICommand(
            "vsync",
            "Синхронизирует версии из шаблонов",
            "vsync",
            self._cmd_version_sync
        )
        
        self.commands["vset"] = CLICommand(
            "vset",
            "Устанавливает новую версию",
            "vset <версия>",
            self._cmd_version_set
        )
        
        self.commands["api"] = CLICommand(
            "api",
            "Показывает настройки Telegram API",
            "api",
            self._cmd_api_show
        )
        
        self.commands["apisync"] = CLICommand(
            "apisync",
            "Синхронизирует API ключ с сервера",
            "apisync",
            self._cmd_api_sync
        )
        
        self.commands["apitest"] = CLICommand(
            "apitest",
            "Проверяет подключение к API",
            "apitest",
            self._cmd_api_test
        )
        
        # === КОМАНДЫ AI ===
        
        self.commands["aiprovider"] = CLICommand(
            "aiprovider",
            "Показывает/меняет провайдера AI",
            "aiprovider [anthropic|openai|telegram]",
            self._cmd_ai_provider
        ).add_alias("provider")
        
        self.commands["aimodel"] = CLICommand(
            "aimodel",
            "Показывает/меняет модель AI",
            "aimodel [название_модели]",
            self._cmd_ai_model
        ).add_alias("model")
        
        self.commands["aimodels"] = CLICommand(
            "aimodels",
            "Список доступных моделей",
            "aimodels [anthropic|openai]",
            self._cmd_ai_models
        ).add_alias("models")
        
        self.commands["aiinfo"] = CLICommand(
            "aiinfo",
            "Показывает текущие настройки AI",
            "aiinfo",
            self._cmd_ai_info
        ).add_alias("ai")
        
        # Обновляем автодополнение
        command_names = list(self.commands.keys())
        for cmd in self.commands.values():
            command_names.extend(cmd.aliases)
        self.completer_model.setStringList(sorted(set(command_names)))
    
    # === ОБРАБОТЧИКИ КОМАНД ===
    
    def _cmd_help(self, args: List[str]) -> str:
        """Команда help"""
        if args:
            # Помощь по конкретной команде
            cmd_name = args[0].lower()
            cmd = self.commands.get(cmd_name)
            if cmd:
                result = f"\n📖 Команда: {cmd.name}\n"
                result += f"Описание: {cmd.description}\n"
                result += f"Использование: {cmd.usage}\n"
                if cmd.aliases:
                    result += f"Алиасы: {', '.join(cmd.aliases)}\n"
                return result
            else:
                return f"❌ Команда '{cmd_name}' не найдена"
        
        # Общая справка
        result = "\n📚 Доступные команды:\n"
        result += "=" * 60 + "\n\n"
        
        categories = {
            "Общие": ["help", "clear", "exit", "history"],
            "Файлы": ["list", "add", "remove", "process"],
            "База данных": ["dbstats", "dbsearch", "dbexport", "dbbackup"],
            "Система": ["status", "config", "theme", "scale"],
            "Синхронизация": ["version", "vsync", "vset", "api", "apisync", "apitest"],
            "AI настройки": ["aiinfo", "aiprovider", "aimodel", "aimodels"]
        }
        
        for category, commands in categories.items():
            result += f"🔹 {category}:\n"
            for cmd_name in commands:
                cmd = self.commands.get(cmd_name)
                if cmd:
                    aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                    result += f"  • {cmd.name}{aliases} - {cmd.description}\n"
            result += "\n"
        
        result += "Для подробной справки: help <команда>\n"
        return result
    
    def _cmd_clear(self, args: List[str]) -> str:
        """Команда clear"""
        self.output_area.clear()
        self._print_welcome()
        return ""
    
    def _cmd_exit(self, args: List[str]) -> str:
        """Команда exit"""
        self.parent().close() if self.parent() else None
        return "👋 До свидания!"
    
    def _cmd_history(self, args: List[str]) -> str:
        """Команда history"""
        if not self.command_history:
            return "История команд пуста"
        
        result = "\n📜 История команд:\n"
        for i, cmd in enumerate(self.command_history[-20:], 1):  # Последние 20
            result += f"{i:3}. {cmd}\n"
        return result
    
    def _cmd_list_files(self, args: List[str]) -> str:
        """Команда list"""
        if not self.main_window.input_files:
            return "📁 Список файлов пуст"
        
        result = "\n📁 Входные файлы:\n"
        for i, (file_path, count) in enumerate(self.main_window.input_files.items(), 1):
            filename = os.path.basename(file_path)
            result += f"{i:3}. {filename} (x{count})\n"
            result += f"     {file_path}\n"
        return result
    
    def _cmd_add_file(self, args: List[str]) -> str:
        """Команда add"""
        if not args:
            return "❌ Укажите путь к файлу: add <путь>"
        
        file_path = " ".join(args)
        if not os.path.exists(file_path):
            return f"❌ Файл не найден: {file_path}"
        
        if not file_path.lower().endswith(('.xlsx', '.docx', '.doc', '.txt')):
            return "❌ Неподдерживаемый формат файла"
        
        self.main_window.input_files[file_path] = 1
        self.main_window.update_listbox()
        return f"✅ Файл добавлен: {os.path.basename(file_path)}"
    
    def _cmd_remove_file(self, args: List[str]) -> str:
        """Команда remove"""
        if not args:
            return "❌ Укажите индекс или путь файла"
        
        if not self.main_window.input_files:
            return "❌ Список файлов пуст"
        
        # Попытка удалить по индексу
        try:
            index = int(args[0]) - 1
            files = list(self.main_window.input_files.keys())
            if 0 <= index < len(files):
                file_path = files[index]
                del self.main_window.input_files[file_path]
                self.main_window.update_listbox()
                return f"✅ Файл удален: {os.path.basename(file_path)}"
        except ValueError:
            pass
        
        # Удаление по пути
        file_path = " ".join(args)
        if file_path in self.main_window.input_files:
            del self.main_window.input_files[file_path]
            self.main_window.update_listbox()
            return f"✅ Файл удален: {os.path.basename(file_path)}"
        
        return f"❌ Файл не найден: {args[0]}"
    
    def _cmd_process(self, args: List[str]) -> str:
        """Команда process"""
        if not self.main_window.input_files:
            return "❌ Список файлов пуст. Добавьте файлы командой 'add'"
        
        self.main_window.on_run()
        return f"🚀 Запущена обработка {len(self.main_window.input_files)} файлов..."
    
    def _cmd_db_stats(self, args: List[str]) -> str:
        """Команда dbstats"""
        try:
            db = self.main_window.db
            stats = db.get_statistics()
            
            result = "\n📊 Статистика базы данных:\n"
            result += "=" * 50 + "\n"
            result += f"Всего компонентов: {stats['total_components']}\n"
            result += f"Версия БД: {stats['db_version']}\n"
            result += f"Последнее обновление: {stats['last_update']}\n\n"
            result += "Компонентов по категориям:\n"
            for category, count in stats['by_category'].items():
                result += f"  • {category}: {count}\n"
            
            return result
        except Exception as e:
            return f"❌ Ошибка получения статистики: {e}"
    
    def _cmd_db_search(self, args: List[str]) -> str:
        """Команда dbsearch"""
        if not args:
            return "❌ Укажите название компонента для поиска"
        
        query = " ".join(args)
        try:
            db = self.main_window.db
            results = db.search_component(query)
            
            if not results:
                return f"❌ Компонент '{query}' не найден в базе данных"
            
            result = f"\n🔍 Результаты поиска '{query}':\n"
            result += "=" * 50 + "\n"
            for i, comp in enumerate(results[:10], 1):  # Первые 10
                result += f"{i}. {comp['name']} - {comp['category']}\n"
            
            if len(results) > 10:
                result += f"\n... и еще {len(results) - 10} результатов\n"
            
            return result
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"
    
    def _cmd_db_export(self, args: List[str]) -> str:
        """Команда dbexport"""
        try:
            self.main_window.export_database()
            return "✅ База данных экспортирована"
        except Exception as e:
            return f"❌ Ошибка экспорта: {e}"
    
    def _cmd_db_backup(self, args: List[str]) -> str:
        """Команда dbbackup"""
        try:
            self.main_window.backup_database()
            return "✅ Резервная копия создана"
        except Exception as e:
            return f"❌ Ошибка создания резервной копии: {e}"
    
    def _cmd_status(self, args: List[str]) -> str:
        """Команда status"""
        result = "\n📋 Статус приложения:\n"
        result += "=" * 50 + "\n"
        result += f"Версия: {self.main_window.cfg.get('app_info', {}).get('version', 'N/A')}\n"
        result += f"Тема: {self.main_window.current_theme}\n"
        result += f"Масштаб: {int(self.main_window.scale_factor * 100)}%\n"
        result += f"Режим работы: {self.main_window.current_view_mode}\n"
        result += f"Входных файлов: {len(self.main_window.input_files)}\n"
        
        if hasattr(self.main_window, 'db'):
            result += f"База данных: подключена\n"
        else:
            result += f"База данных: не подключена\n"
        
        return result
    
    def _cmd_config(self, args: List[str]) -> str:
        """Команда config"""
        if not args:
            # Показываем всю конфигурацию
            result = "\n⚙️ Конфигурация:\n"
            result += "=" * 50 + "\n"
            result += json.dumps(self.main_window.cfg, indent=2, ensure_ascii=False)
            return result
        
        # Показываем конкретный параметр
        param = args[0]
        value = self.main_window.cfg.get(param, "Не найдено")
        return f"{param}: {value}"
    
    def _cmd_theme(self, args: List[str]) -> str:
        """Команда theme"""
        if not args:
            return f"Текущая тема: {self.main_window.current_theme}\nИспользование: theme [dark|light]"
        
        theme = args[0].lower()
        if theme in ["dark", "light"]:
            self.main_window.toggle_theme()
            return f"✅ Тема изменена на {theme}"
        else:
            return "❌ Неизвестная тема. Доступны: dark, light"
    
    def _cmd_scale(self, args: List[str]) -> str:
        """Команда scale"""
        if not args:
            return f"Текущий масштаб: {int(self.main_window.scale_factor * 100)}%\nИспользование: scale <0.7-1.25>"
        
        try:
            scale = float(args[0])
            if 0.7 <= scale <= 1.25:
                self.main_window.set_scale_factor(scale)
                return f"✅ Масштаб изменен на {int(scale * 100)}%"
            else:
                return "❌ Масштаб должен быть от 0.7 до 1.25"
        except ValueError:
            return "❌ Неверное значение масштаба"
    
    # === КОМАНДЫ СИНХРОНИЗАЦИИ ===
    
    def _get_project_root(self) -> str:
        """Получает корень проекта BOMCategorizer"""
        # Пробуем несколько способов найти корень проекта
        
        # Способ 1: относительно текущего файла
        # __file__ = bom_categorizer/cli_interactive.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        
        if os.path.exists(os.path.join(parent_dir, 'tools', 'sync_telegram_api.py')):
            return parent_dir
        
        # Способ 2: через main_window
        if hasattr(self.main_window, 'project_root'):
            return self.main_window.project_root
        
        # Способ 3: поиск вверх по директориям
        search_dir = current_dir
        for _ in range(5):  # Максимум 5 уровней вверх
            if os.path.exists(os.path.join(search_dir, 'tools', 'sync_telegram_api.py')):
                return search_dir
            search_dir = os.path.dirname(search_dir)
        
        # Способ 4: текущая рабочая директория
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, 'tools', 'sync_telegram_api.py')):
            return cwd
        
        # Способ 5: стандартные пути разработки
        dev_paths = [
            os.path.expanduser("~/Project/ProjectPython/BOMCategorizer"),
            os.path.expanduser("~/Documents/BOMCategorizer"),
            "/Users/olgazaharova/Project/ProjectPython/BOMCategorizer",
        ]
        for path in dev_paths:
            if os.path.exists(os.path.join(path, 'tools', 'sync_telegram_api.py')):
                return path
        
        return parent_dir  # Fallback
    
    def _is_app_bundle(self) -> bool:
        """Проверяет, запущено ли приложение из .app bundle"""
        current_path = os.path.abspath(__file__)
        # Проверяем несколько признаков bundled app
        return (
            '.app/Contents/' in current_path or
            '/Applications/' in current_path or
            'Resources/lib/python' in current_path
        )
    
    def _cmd_version(self, args: List[str]) -> str:
        """Команда version - показать версии"""
        import subprocess
        
        result = "\n📋 Версии приложения:\n"
        result += "=" * 50 + "\n"
        
        # Текущая версия из конфига
        app_info = self.main_window.cfg.get('app_info', {})
        result += f"Текущая версия: {app_info.get('version', 'N/A')}\n"
        result += f"Edition: {app_info.get('edition', 'N/A')}\n"
        result += f"Дата релиза: {app_info.get('release_date', 'N/A')}\n"
        result += f"Обновлено: {app_info.get('last_updated', 'N/A')}\n\n"
        
        # Пробуем запустить update_version.py status
        try:
            project_root = self._get_project_root()
            script_path = os.path.join(project_root, 'tools', 'update_version.py')
            
            if os.path.exists(script_path):
                result += "💡 Для полной информации выполните:\n"
                result += "   python tools/update_version.py status\n"
            else:
                result += f"💡 Скрипт update_version.py не найден\n"
                result += f"   Путь: {script_path}\n"
        except Exception:
            pass
        
        return result
    
    def _cmd_version_sync(self, args: List[str]) -> str:
        """Команда vsync - синхронизировать версии"""
        import subprocess
        
        try:
            project_root = self._get_project_root()
            script_path = os.path.join(project_root, 'tools', 'update_version.py')
            
            if not os.path.exists(script_path):
                return ("❌ Скрипт update_version.py не найден\n\n"
                        "💡 В терминале из папки проекта:\n"
                        "   python tools/update_version.py status\n"
                        "   python tools/update_version.py sync")
            
            result = subprocess.run(
                [sys.executable, script_path, 'sync'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            
            output = result.stdout + result.stderr
            # Убираем ANSI цвета для CLI
            import re
            output = re.sub(r'\033\[[0-9;]*m', '', output)
            
            return f"🔄 Синхронизация версий:\n{output}"
            
        except subprocess.TimeoutExpired:
            return "❌ Таймаут выполнения команды"
        except Exception as e:
            return f"❌ Ошибка синхронизации: {e}"
    
    def _cmd_version_set(self, args: List[str]) -> str:
        """Команда vset - установить версию"""
        if not args:
            return "❌ Укажите версию: vset <версия>\nПример: vset 4.6.0"
        
        import subprocess
        new_version = args[0]
        
        # Валидация формата версии
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', new_version):
            return f"❌ Неверный формат версии: {new_version}\nОжидается формат: X.Y.Z (например, 4.6.0)"
        
        try:
            project_root = self._get_project_root()
            script_path = os.path.join(project_root, 'tools', 'update_version.py')
            
            if not os.path.exists(script_path):
                return f"❌ Скрипт update_version.py не найден\n   Путь: {script_path}"
            
            result = subprocess.run(
                [sys.executable, script_path, 'set', 'modern', new_version],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            
            output = result.stdout + result.stderr
            # Убираем ANSI цвета
            import re
            output = re.sub(r'\033\[[0-9;]*m', '', output)
            
            if result.returncode == 0:
                return f"✅ Версия обновлена до {new_version}\n{output}"
            else:
                return f"❌ Ошибка обновления:\n{output}"
            
        except subprocess.TimeoutExpired:
            return "❌ Таймаут выполнения команды"
        except Exception as e:
            return f"❌ Ошибка установки версии: {e}"
    
    def _cmd_api_show(self, args: List[str]) -> str:
        """Команда api - показать настройки API"""
        result = "\n🔐 Настройки Telegram API:\n"
        result += "=" * 50 + "\n"
        
        api_keys = self.main_window.cfg.get('api_keys', {})
        
        telegram_url = api_keys.get('telegram_url', 'Не настроен')
        telegram_key = api_keys.get('telegram_key', '')
        
        result += f"URL: {telegram_url}\n"
        
        if telegram_key:
            # Показываем только часть ключа
            masked_key = telegram_key[:16] + "..." if len(telegram_key) > 16 else telegram_key
            result += f"Key: {masked_key}\n"
            result += f"Длина ключа: {len(telegram_key)} символов\n"
        else:
            result += "Key: ❌ Не настроен\n"
        
        result += "\n💡 Команды:\n"
        result += "  apisync - получить ключ с сервера\n"
        result += "  apitest - проверить подключение\n"
        
        return result
    
    def _cmd_api_sync(self, args: List[str]) -> str:
        """Команда apisync - синхронизировать API ключ"""
        import subprocess
        
        # Проверяем, запущено ли из .app bundle
        if self._is_app_bundle():
            return ("⚠️ Команда apisync недоступна в установленном приложении.\n\n"
                    "💡 Используйте один из способов:\n"
                    "   1. /api в Telegram боте → скопируйте ключ\n"
                    "   2. Настройки → API Ключи → Telegram Bot API\n"
                    "   3. В терминале из папки проекта:\n"
                    "      python tools/sync_telegram_api.py --fetch")
        
        try:
            project_root = self._get_project_root()
            script_path = os.path.join(project_root, 'tools', 'sync_telegram_api.py')
            
            if not os.path.exists(script_path):
                return (f"❌ Скрипт sync_telegram_api.py не найден\n"
                        f"   Путь: {script_path}\n"
                        f"   Проект: {project_root}\n\n"
                        f"💡 Альтернативы:\n"
                        f"   1. /api в Telegram боте → скопируйте ключ\n"
                        f"   2. Настройки → API Ключи → Telegram Bot API\n"
                        f"   3. В терминале из папки проекта:\n"
                        f"      python tools/sync_telegram_api.py --fetch\n"
                        f"      python tools/sync_telegram_api.py --test")
            
            self._print("🔄 Подключение к серверу...", color="#f9e2af")
            
            result = subprocess.run(
                [sys.executable, script_path, '--fetch'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                # Перезагружаем конфиг
                try:
                    config_path = os.path.join(project_root, 'config_qt.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            new_config = json.load(f)
                        self.main_window.cfg.update(new_config)
                except Exception:
                    pass
                
                return f"✅ API ключ синхронизирован!\n{output}\n\n⚠️ Перезапустите приложение для применения изменений."
            else:
                return f"❌ Ошибка синхронизации:\n{output}"
            
        except subprocess.TimeoutExpired:
            return "❌ Таймаут подключения к серверу (60 сек)"
        except Exception as e:
            return f"❌ Ошибка синхронизации API: {e}"
    
    def _cmd_api_test(self, args: List[str]) -> str:
        """Команда apitest - проверить подключение к API"""
        import subprocess
        
        api_keys = self.main_window.cfg.get('api_keys', {})
        telegram_url = api_keys.get('telegram_url', '')
        telegram_key = api_keys.get('telegram_key', '')
        
        if not telegram_url or not telegram_key:
            return "❌ API не настроен. Выполните apisync или настройте вручную."
        
        # Формируем URL для health check
        base_url = telegram_url.replace('/ai_query', '')
        health_url = f"{base_url}/health"
        
        try:
            import urllib.request
            import urllib.error
            
            self._print(f"🔄 Проверка {health_url}...", color="#f9e2af")
            
            req = urllib.request.Request(health_url)
            req.add_header('User-Agent', 'BOMCategorizer-CLI')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8')
                
                result = "\n✅ API доступен!\n"
                result += "=" * 50 + "\n"
                result += f"URL: {health_url}\n"
                result += f"Статус: {response.status}\n"
                result += f"Ответ: {data}\n"
                return result
                
        except urllib.error.URLError as e:
            return f"❌ Ошибка подключения: {e.reason}\nURL: {health_url}"
        except Exception as e:
            return f"❌ Ошибка проверки API: {e}"
    
    def _cmd_ai_info(self, args: List[str]) -> str:
        """Команда aiinfo - показать настройки AI"""
        result = "\n🤖 Настройки AI:\n"
        result += "=" * 50 + "\n"
        
        api_keys = self.main_window.cfg.get('api_keys', {})
        
        # Текущий провайдер
        current_provider = self.main_window.cfg.get('ai_provider', 'telegram')
        result += f"\n📍 Текущий провайдер: {current_provider.upper()}\n"
        
        # Telegram Bot
        result += "\n🔹 Telegram Bot API:\n"
        telegram_url = api_keys.get('telegram_url', 'Не настроен')
        telegram_key = api_keys.get('telegram_key', '')
        result += f"   URL: {telegram_url}\n"
        if telegram_key:
            result += f"   Key: {telegram_key[:16]}... ({len(telegram_key)} симв.)\n"
            result += "   Статус: ✅ Настроен\n"
        else:
            result += "   Статус: ❌ Не настроен\n"
        
        # Anthropic
        result += "\n🔹 Anthropic (Claude):\n"
        anthropic_key = api_keys.get('anthropic', '')
        anthropic_model = self.main_window.cfg.get('anthropic_model', 'claude-3-5-sonnet-20241022')
        if anthropic_key:
            result += f"   Key: {anthropic_key[:16]}... ({len(anthropic_key)} симв.)\n"
            result += f"   Model: {anthropic_model}\n"
            result += "   Статус: ✅ Настроен\n"
        else:
            result += "   Статус: ❌ Не настроен\n"
        
        # OpenAI
        result += "\n🔹 OpenAI (GPT):\n"
        openai_key = api_keys.get('openai', '')
        openai_model = self.main_window.cfg.get('openai_model', 'gpt-4')
        if openai_key:
            result += f"   Key: {openai_key[:16]}... ({len(openai_key)} симв.)\n"
            result += f"   Model: {openai_model}\n"
            result += "   Статус: ✅ Настроен\n"
        else:
            result += "   Статус: ❌ Не настроен\n"
        
        result += "\n💡 Команды:\n"
        result += "  aiprovider <имя>  - сменить провайдера\n"
        result += "  aimodel <модель>  - сменить модель\n"
        result += "  aimodels          - список моделей\n"
        
        return result
    
    def _cmd_ai_provider(self, args: List[str]) -> str:
        """Команда aiprovider - показать/сменить провайдера"""
        valid_providers = ['anthropic', 'openai', 'telegram']
        
        if not args:
            current = self.main_window.cfg.get('ai_provider', 'telegram')
            result = f"\n📍 Текущий AI провайдер: {current.upper()}\n"
            result += "\n💡 Доступные провайдеры:\n"
            for p in valid_providers:
                marker = "✅" if p == current else "  "
                result += f"   {marker} {p}\n"
            result += "\nДля смены: aiprovider <имя>\n"
            result += "Пример: aiprovider anthropic\n"
            return result
        
        new_provider = args[0].lower()
        
        if new_provider not in valid_providers:
            return f"❌ Неизвестный провайдер: {new_provider}\nДоступные: {', '.join(valid_providers)}"
        
        # Сохраняем в конфиг
        self.main_window.cfg['ai_provider'] = new_provider
        
        # Пытаемся сохранить в файл
        try:
            project_root = self._get_project_root()
            config_path = os.path.join(project_root, 'config_qt.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                config['ai_provider'] = new_provider
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Не критично если не сохранилось
        
        return f"✅ AI провайдер изменён на {new_provider.upper()}"
    
    def _cmd_ai_model(self, args: List[str]) -> str:
        """Команда aimodel - показать/сменить модель"""
        current_provider = self.main_window.cfg.get('ai_provider', 'telegram')
        
        if not args:
            # Показываем текущие модели
            result = "\n🤖 Текущие модели AI:\n"
            result += "=" * 50 + "\n"
            
            anthropic_model = self.main_window.cfg.get('anthropic_model', 'claude-3-5-sonnet-20241022')
            openai_model = self.main_window.cfg.get('openai_model', 'gpt-4')
            
            result += f"\n📍 Активный провайдер: {current_provider.upper()}\n"
            result += f"\n🔹 Anthropic: {anthropic_model}\n"
            result += f"🔹 OpenAI: {openai_model}\n"
            result += f"🔹 Telegram: (модель настраивается на сервере через /ch_model)\n"
            
            result += "\n💡 Для смены модели:\n"
            result += "   aimodel claude-3-5-sonnet-20241022\n"
            result += "   aimodel gpt-4-turbo\n"
            result += "   aimodels - показать список моделей\n"
            return result
        
        new_model = args[0]
        
        # Определяем для какого провайдера модель
        if 'claude' in new_model.lower() or 'anthropic' in new_model.lower():
            self.main_window.cfg['anthropic_model'] = new_model
            provider_name = 'Anthropic'
        elif 'gpt' in new_model.lower() or 'openai' in new_model.lower():
            self.main_window.cfg['openai_model'] = new_model
            provider_name = 'OpenAI'
        else:
            # По умолчанию для текущего провайдера
            if current_provider == 'anthropic':
                self.main_window.cfg['anthropic_model'] = new_model
                provider_name = 'Anthropic'
            else:
                self.main_window.cfg['openai_model'] = new_model
                provider_name = 'OpenAI'
        
        # Пытаемся сохранить в файл
        try:
            project_root = self._get_project_root()
            config_path = os.path.join(project_root, 'config_qt.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if provider_name == 'Anthropic':
                    config['anthropic_model'] = new_model
                else:
                    config['openai_model'] = new_model
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        
        return f"✅ Модель {provider_name} изменена на {new_model}"
    
    def _cmd_ai_models(self, args: List[str]) -> str:
        """Команда aimodels - список доступных моделей"""
        result = "\n📋 Доступные модели AI:\n"
        result += "=" * 50 + "\n"
        
        result += "\n🔹 Anthropic Claude:\n"
        anthropic_models = [
            "claude-opus-4-5-20251101 (новейшая, самая мощная)",
            "claude-sonnet-4-5-20251101 (баланс скорости/качества)",
            "claude-3-5-sonnet-20241022 (рекомендуется)",
            "claude-3-5-haiku-20241022 (быстрая)",
            "claude-3-opus-20240229 (мощная)",
            "claude-3-sonnet-20240229 (средняя)",
            "claude-3-haiku-20240307 (быстрая)"
        ]
        for m in anthropic_models:
            result += f"   • {m}\n"
        
        result += "\n🔹 OpenAI GPT:\n"
        openai_models = [
            "gpt-4-turbo (рекомендуется)",
            "gpt-4 (мощная)",
            "gpt-4o (оптимизированная)",
            "gpt-4o-mini (быстрая)",
            "gpt-3.5-turbo (быстрая, дешёвая)"
        ]
        for m in openai_models:
            result += f"   • {m}\n"
        
        result += "\n🔹 Telegram Bot:\n"
        result += "   • Модель настраивается на сервере\n"
        result += "   • Используйте команду /ch_model в боте\n"
        
        result += "\n💡 Для смены модели:\n"
        result += "   aimodel <название>\n"
        result += "   Пример: aimodel claude-3-5-sonnet-20241022\n"
        
        return result

