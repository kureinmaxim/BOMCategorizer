# -*- coding: utf-8 -*-
"""
Модуль глобального поиска для GUI

Содержит:
- GlobalSearchDialog: диалог отображения результатов поиска
- SearchMixin: миксин с методами поиска для главного окна
"""

import os
import platform
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .scaling import get_system_font


class GlobalSearchDialog(QDialog):
    """Диалог отображения результатов глобального поиска."""

    def __init__(self, parent, results: Dict[str, Any]):
        super().__init__(parent)
        self.parent_window = parent
        self.results = results
        
        # Получаем scale_factor от родительского окна (без уменьшения, как в таблице истории БД)
        self.scale_factor = getattr(parent, 'scale_factor', 1.0)

        self.setWindowTitle(f"Результаты поиска: «{results.get('query', '')}»")
        self.setModal(True)
        self.resize(960, 560)

        layout = QVBoxLayout(self)

        summary_parts = [
            f"Запрос: «{results.get('query', '')}»",
            f"Совпадений: {results.get('total_matches', 0)}"
        ]
        counts = results.get("counts", {})
        if counts:
            breakdown = ", ".join([
                f"БД: {counts.get('database', 0)}",
                f"Входные: {counts.get('inputs', 0)}",
                f"Выходной: {counts.get('output', 0)}",
                f"Сравнение: {counts.get('comparison', 0)}"
            ])
            summary_parts.append(f"Разбивка: {breakdown}")
        if results.get("duration_ms") is not None:
            summary_parts.append(f"Время: {results['duration_ms']} мс")
        summary_label = QLabel(" | ".join(summary_parts))
        summary_label.setWordWrap(True)
        # Применяем крупный шрифт для читаемости (базовый 13pt)
        summary_font_size = max(11, int(13 * self.scale_factor))
        summary_label.setFont(QFont(get_system_font(), summary_font_size))
        layout.addWidget(summary_label)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Источник", "Совпадений", "Детали"])
        
        # Применяем крупный шрифт к дереву для читаемости (базовый 14pt)
        # Для Windows уменьшаем на 3 пункта (было 2, теперь еще на 1 меньше)
        base_font_size = 14
        if platform.system() == 'Windows':
            base_font_size = 11  # Уменьшаем на 3 пункта для Windows
        tree_font_size = max(10, int(base_font_size * self.scale_factor))
        tree_font = QFont(get_system_font(), tree_font_size)
        self.tree.setFont(tree_font)
        
        # Заголовки чуть крупнее и жирные
        header = self.tree.header()
        header_font = QFont(get_system_font(), tree_font_size + 1)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Центрируем заголовки колонок "Совпадений" и "Детали"
        header_item = self.tree.headerItem()
        if header_item:
            header_item.setTextAlignment(1, Qt.AlignCenter)  # Совпадений
            header_item.setTextAlignment(2, Qt.AlignCenter)  # Детали
        self.tree.setRootIsDecorated(True)
        layout.addWidget(self.tree, stretch=1)

        # Настраиваем стиль подсветки в зависимости от темы
        theme = getattr(parent, "current_theme", "dark")
        if theme == "light":
            hover_color = "#ccd0da"
            selected_bg = "#88aaff"
            selected_fg = "#1e1e2e"
        else:
            hover_color = "#2f3145"
            selected_bg = "#89b4fa"
            selected_fg = "#1e1e2e"

        self.tree.setStyleSheet(
            f"""
            QTreeWidget::item:hover {{
                background-color: {hover_color};
            }}
            QTreeWidget::item:selected {{
                background-color: {selected_bg};
                color: {selected_fg};
            }}
            """
        )

        info_label = QLabel("📁 Дважды щёлкните или нажмите Enter, чтобы открыть папку с выбранным файлом.")
        info_label.setWordWrap(True)
        # Применяем крупный шрифт для подсказки (базовый 13pt)
        info_font_size = max(11, int(13 * self.scale_factor))
        info_label.setFont(QFont(get_system_font(), info_font_size))
        info_label.setStyleSheet("color: #a6adc8;" if theme != "light" else "color: #4c4f69;")
        layout.addWidget(info_label)

        self._populate_tree()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Применяем крупный шрифт к кнопкам (базовый 13pt)
        button_font_size = max(12, int(13 * self.scale_factor))
        button_font = QFont(get_system_font(), button_font_size)

        self.save_button = QPushButton("💾 Сохранить результаты...")
        self.save_button.setFont(button_font)
        self.save_button.clicked.connect(self.save_results)
        button_layout.addWidget(self.save_button)

        close_button = QPushButton("Закрыть")
        close_button.setFont(button_font)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        self.tree.itemDoubleClicked.connect(self.on_item_activated)
        self.tree.itemActivated.connect(self.on_item_activated)

        if results.get("total_matches", 0) == 0 and not results.get("notes"):
            summary_label.setText(summary_label.text() + " | Совпадений не найдено")

    def _center_columns(self, item: QTreeWidgetItem) -> None:
        """Центрирует колонки 'Совпадений' (1) и 'Детали' (2) для элемента."""
        item.setTextAlignment(1, Qt.AlignCenter)  # Колонка "Совпадений"
        item.setTextAlignment(2, Qt.AlignCenter)  # Колонка "Детали"

    def _populate_tree(self) -> None:
        """Заполняет дерево результатами поиска."""
        self.tree.clear()

        nav_hint = "\nДважды щёлкните или нажмите Enter, чтобы открыть файл в проводнике."

        db_result = self.results.get("database")
        if db_result:
            db_root = QTreeWidgetItem(self.tree, [
                "База данных компонентов",
                str(db_result.get("count", 0)),
                ""
            ])
            self._center_columns(db_root)
            db_path = db_result.get("path")
            db_root.setData(0, Qt.UserRole, db_path)
            if db_path:
                db_root.setToolTip(0, db_path + nav_hint)

            for match in db_result.get("samples", []):
                name = match.get("name", "")
                category = match.get("category", "")
                item = QTreeWidgetItem(db_root, [name, "1", category])
                self._center_columns(item)
                if db_path:
                    item.setToolTip(0, f"{name}\nФайл: {db_path}{nav_hint}")
                else:
                    item.setToolTip(0, name)
                item.setToolTip(2, category)
                item.setData(0, Qt.UserRole, db_path)

            extra = db_result.get("extra", 0)
            if extra > 0:
                extra_item = QTreeWidgetItem(db_root, [f"... и еще {extra} совпадений", "", ""])
                self._center_columns(extra_item)
                extra_item.setDisabled(True)

            db_root.setExpanded(True)

        inputs = self.results.get("inputs", [])
        inputs_examined = self.results.get("inputs_examined", 0)
        inputs_total = sum(entry.get("count", 0) for entry in inputs)
        inputs_root = QTreeWidgetItem(self.tree, [
            f"Входные файлы (проверено: {inputs_examined})",
            str(inputs_total),
            ""
        ])
        self._center_columns(inputs_root)
        for entry in inputs:
            display = entry.get("display") or entry.get("filename") or os.path.basename(entry.get("path", "")) or "Файл"
            count = entry.get("count", 0)
            path = entry.get("path")
            file_item = QTreeWidgetItem(inputs_root, [display, str(count), ""])
            self._center_columns(file_item)
            file_item.setData(0, Qt.UserRole, path)
            if path:
                file_item.setToolTip(0, path + nav_hint)

            for sample in entry.get("samples", []):
                location = sample.get("location", "")
                context = sample.get("context", "")
                sample_item = QTreeWidgetItem(file_item, [location, "1", context])
                self._center_columns(sample_item)
                sample_item.setToolTip(0, f"{location}{nav_hint if path else ''}")
                sample_item.setToolTip(2, context)
                sample_item.setData(0, Qt.UserRole, path)

            extra = entry.get("extra", 0)
            if extra > 0:
                extra_item = QTreeWidgetItem(file_item, [f"... и еще {extra} совпадений", "", ""])
                self._center_columns(extra_item)
                extra_item.setDisabled(True)

            file_item.setExpanded(True)
        inputs_root.setExpanded(bool(inputs))

        output_result = self.results.get("output")
        if output_result:
            output_item = self._add_file_group(
                "Выходной файл",
                output_result
            )
            self.tree.addTopLevelItem(output_item)

        comparison_entries = self.results.get("comparison", [])
        if comparison_entries:
            compare_root = QTreeWidgetItem(self.tree, [
                "Файлы сравнения",
                str(sum(entry.get("count", 0) for entry in comparison_entries)),
                ""
            ])
            self._center_columns(compare_root)
            for entry in comparison_entries:
                display = entry.get("display") or entry.get("filename") or os.path.basename(entry.get("path", "")) or "Файл"
                count = entry.get("count", 0)
                path = entry.get("path")
                file_item = QTreeWidgetItem(compare_root, [display, str(count), ""])
                self._center_columns(file_item)
                file_item.setData(0, Qt.UserRole, path)
                if path:
                    file_item.setToolTip(0, path + nav_hint)

                for sample in entry.get("samples", []):
                    location = sample.get("location", "")
                    context = sample.get("context", "")
                    sample_item = QTreeWidgetItem(file_item, [location, "1", context])
                    self._center_columns(sample_item)
                    sample_item.setToolTip(0, f"{location}{nav_hint if path else ''}")
                    sample_item.setToolTip(2, context)
                    sample_item.setData(0, Qt.UserRole, path)

                extra = entry.get("extra", 0)
                if extra > 0:
                    extra_item = QTreeWidgetItem(file_item, [f"... и еще {extra} совпадений", "", ""])
                    self._center_columns(extra_item)
                    extra_item.setDisabled(True)

                file_item.setExpanded(True)
            compare_root.setExpanded(True)

        notes = self.results.get("notes", [])
        if notes:
            errors_root = QTreeWidgetItem(self.tree, [
                "ℹ️ Примечания поиска",
                str(len(notes)),
                ""
            ])
            self._center_columns(errors_root)
            for err in notes:
                source = err.get("source", "Источник не указан")
                message = err.get("message", "")
                err_item = QTreeWidgetItem(errors_root, [source, "", message])
                self._center_columns(err_item)
                err_item.setToolTip(0, source)
                err_item.setToolTip(2, message)
            errors_root.setExpanded(True)

        # Если нет совпадений вовсе, добавляем информационный узел
        if self.results.get("total_matches", 0) == 0 and not notes:
            info_item = QTreeWidgetItem(self.tree, [
                "Информация",
                "0",
                "Совпадений по запросу не найдено"
            ])
            self._center_columns(info_item)
            info_item.setDisabled(True)

        self.tree.expandToDepth(1)

    def _add_file_group(self, title: str, entry: Dict[str, Any]) -> QTreeWidgetItem:
        """Создает узел дерева для файла с совпадениями."""
        item = QTreeWidgetItem([
            title if title else entry.get("display", "Файл"),
            str(entry.get("count", 0)),
            ""
        ])
        self._center_columns(item)
        path = entry.get("path")
        nav_hint = "\nДважды щёлкните или нажмите Enter, чтобы открыть файл в проводнике."
        if path:
            item.setData(0, Qt.UserRole, path)
            item.setToolTip(0, path + nav_hint)

        for sample in entry.get("samples", []):
            location = sample.get("location", "")
            context = sample.get("context", "")
            sample_item = QTreeWidgetItem(item, [location, "1", context])
            self._center_columns(sample_item)
            if path:
                sample_item.setToolTip(0, f"{location}{nav_hint}")
            else:
                sample_item.setToolTip(0, location)
            sample_item.setToolTip(2, context)
            sample_item.setData(0, Qt.UserRole, path)

        extra = entry.get("extra", 0)
        if extra > 0:
            extra_item = QTreeWidgetItem(item, [f"... и еще {extra} совпадений", "", ""])
            self._center_columns(extra_item)
            extra_item.setDisabled(True)

        item.setExpanded(True)
        return item

    def on_item_activated(self, item: QTreeWidgetItem, _: int) -> None:
        """Открывает проводник при двойном клике по элементу."""
        path = item.data(0, Qt.UserRole)
        if path:
            self.parent_window.reveal_in_file_manager(path, select=True)

    def save_results(self) -> None:
        """Сохраняет результаты поиска в текстовый файл."""
        report_text = self._build_report_text()

        default_dir = None
        db_result = self.results.get("database")
        if db_result and db_result.get("path"):
            default_dir = os.path.dirname(db_result["path"])
        if not default_dir:
            output_result = self.results.get("output")
            if output_result and output_result.get("path"):
                default_dir = os.path.dirname(output_result["path"])
        if not default_dir:
            default_dir = os.getcwd()

        filename = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        default_path = os.path.join(default_dir, filename)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты поиска",
            default_path,
            "Text Files (*.txt)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_text)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить файл:\n{exc}"
            )
            return

        QMessageBox.information(
            self,
            "Результаты сохранены",
            f"Файл сохранен:\n{file_path}"
        )

    def _build_report_text(self) -> str:
        """Формирует текстовый отчет по результатам поиска."""
        lines: List[str] = []
        timestamp = self.results.get("timestamp")
        if isinstance(timestamp, datetime):
            ts_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines.append(f"Результаты поиска от {ts_text}")
        lines.append(f"Запрос: {self.results.get('query', '')}")
        if self.results.get("duration_ms") is not None:
            lines.append(f"Время выполнения: {self.results['duration_ms']} мс")
        lines.append(f"Совпадений найдено: {self.results.get('total_matches', 0)}")
        counts = self.results.get("counts", {})
        if counts:
            lines.append(
                "Разбивка: "
                f"БД={counts.get('database', 0)}, "
                f"Входные={counts.get('inputs', 0)}, "
                f"Выходной={counts.get('output', 0)}, "
                f"Сравнение={counts.get('comparison', 0)}"
            )
        lines.append("")

        db_result = self.results.get("database")
        if db_result:
            lines.append("=== БАЗА ДАННЫХ ===")
            if db_result.get("path"):
                lines.append(f"Файл: {db_result['path']}")
            lines.append(f"Совпадений: {db_result.get('count', 0)}")
            for match in db_result.get("matches", []):
                lines.append(f" - {match.get('name', '')} → {match.get('category', '')}")
            extra = db_result.get("extra", 0)
            if extra > 0:
                lines.append(f"... и еще {extra} совпадений")
            lines.append("")

        inputs = self.results.get("inputs", [])
        lines.append("=== ВХОДНЫЕ ФАЙЛЫ ===")
        lines.append(f"Проверено файлов: {self.results.get('inputs_examined', 0)}")
        if inputs:
            for entry in inputs:
                display = entry.get("display") or entry.get("filename") or os.path.basename(entry.get("path", "")) or "Файл"
                lines.append(f"{display} — совпадений: {entry.get('count', 0)}")
                for sample in entry.get("samples", []):
                    lines.append(f"   • {sample.get('location', '')}: {sample.get('context', '')}")
                extra = entry.get("extra", 0)
                if extra > 0:
                    lines.append(f"   • ... и еще {extra} совпадений")
                if entry.get("path"):
                    lines.append(f"   Путь: {entry['path']}")
            lines.append("")
        else:
            lines.append("Совпадений во входных файлах не найдено.\n")

        output_result = self.results.get("output")
        lines.append("=== ВЫХОДНОЙ ФАЙЛ ===")
        if output_result:
            lines.append(f"{output_result.get('display', 'Выходной файл')} — совпадений: {output_result.get('count', 0)}")
            for sample in output_result.get("samples", []):
                lines.append(f"   • {sample.get('location', '')}: {sample.get('context', '')}")
            extra = output_result.get("extra", 0)
            if extra > 0:
                lines.append(f"   • ... и еще {extra} совпадений")
            if output_result.get("path"):
                lines.append(f"   Путь: {output_result['path']}")
        else:
            lines.append("Выходной файл отсутствует или совпадений нет.")
        lines.append("")

        comparison_entries = self.results.get("comparison", [])
        lines.append("=== ФАЙЛЫ СРАВНЕНИЯ ===")
        if comparison_entries:
            for entry in comparison_entries:
                display = entry.get("display") or entry.get("filename") or os.path.basename(entry.get("path", "")) or "Файл"
                lines.append(f"{display} — совпадений: {entry.get('count', 0)}")
                for sample in entry.get("samples", []):
                    lines.append(f"   • {sample.get('location', '')}: {sample.get('context', '')}")
                extra = entry.get("extra", 0)
                if extra > 0:
                    lines.append(f"   • ... и еще {extra} совпадений")
                if entry.get("path"):
                    lines.append(f"   Путь: {entry['path']}")
            lines.append("")
        else:
            lines.append("Файлы сравнения не выбраны или совпадений нет.\n")

        notes = self.results.get("notes", [])
        if notes:
            lines.append("=== ПРИМЕЧАНИЯ ===")
            for err in notes:
                source = err.get("source", "Источник не указан")
                message = err.get("message", "")
                lines.append(f"{source}: {message}")
            lines.append("")

        return "\n".join(lines)

