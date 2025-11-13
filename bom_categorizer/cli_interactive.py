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
        
        # Автодополнение
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.input_field.setCompleter(self.completer)
        
        # Обработка истории (стрелки вверх/вниз)
        self.input_field.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Фильтр событий для истории команд"""
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Up:
                self._history_up()
                return True
            elif event.key() == Qt.Key_Down:
                self._history_down()
                return True
        return super().eventFilter(obj, event)
    
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
            "Система": ["status", "config", "theme", "scale"]
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

