# -*- coding: utf-8 -*-
"""
Экспорт результатов обработки BOM в PDF формат

Конвертирует Excel файлы с результатами в PDF документы.
Поддерживает сохранение таблиц, форматирования и стилей.
"""

import os
from typing import Optional, List
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class PDFExporter:
    """Класс для экспорта BOM данных в PDF"""
    
    def __init__(self):
        self.page_size = landscape(A4)
        self.styles = getSampleStyleSheet()
        self._register_fonts()
    
    def _register_fonts(self):
        """Регистрирует шрифты с поддержкой кириллицы"""
        try:
            # Пытаемся использовать системные шрифты Windows
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/arialbd.ttf',
            ]
            
            for i, font_path in enumerate(font_paths):
                if os.path.exists(font_path):
                    font_name = f'Arial{i}'
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                    except:
                        pass
        except:
            # Если не удалось зарегистрировать шрифты, используем стандартные
            pass
    
    def export_excel_to_pdf(self, excel_path: str, pdf_path: Optional[str] = None) -> str:
        """
        Экспортирует Excel файл в PDF
        
        Args:
            excel_path: Путь к Excel файлу
            pdf_path: Путь к выходному PDF (если None, создается автоматически)
        
        Returns:
            Путь к созданному PDF файлу
        """
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Файл не найден: {excel_path}")
        
        # Определяем путь к PDF
        if not pdf_path:
            base_name = os.path.splitext(excel_path)[0]
            pdf_path = f"{base_name}.pdf"
        
        # Загружаем Excel
        wb = load_workbook(excel_path, data_only=True)
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=self.page_size,
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        # Элементы документа
        story = []
        
        # Заголовок документа
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        title = Paragraph(f"<b>BOM Categorizer - Отчет</b>", title_style)
        story.append(title)
        story.append(Spacer(1, 10*mm))
        
        # Обрабатываем каждый лист
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            
            # Заголовок листа
            sheet_title_style = ParagraphStyle(
                'SheetTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2563eb'),
                spaceAfter=8,
                alignment=TA_LEFT
            )
            
            sheet_title = Paragraph(f"<b>{sheet_name}</b>", sheet_title_style)
            story.append(sheet_title)
            story.append(Spacer(1, 5*mm))
            
            # Получаем данные из листа
            data = self._get_sheet_data(sheet)
            
            if data:
                # Создаем таблицу
                table = self._create_table(data, sheet)
                story.append(table)
            else:
                # Если лист пустой
                empty_text = Paragraph("<i>Лист пуст</i>", self.styles['Normal'])
                story.append(empty_text)
            
            story.append(Spacer(1, 10*mm))
            
            # Разрыв страницы между листами (кроме последнего)
            if sheet_name != wb.sheetnames[-1]:
                story.append(PageBreak())
        
        # Сборка PDF
        doc.build(story)
        
        return pdf_path
    
    def _get_sheet_data(self, sheet: Worksheet, max_rows: int = 1000) -> List[List]:
        """Извлекает данные из листа Excel"""
        data = []
        
        # Определяем границы данных
        max_row = min(sheet.max_row, max_rows)
        max_col = sheet.max_column
        
        if max_row == 0 or max_col == 0:
            return data
        
        # Читаем данные
        for row in sheet.iter_rows(min_row=1, max_row=max_row, max_col=max_col):
            row_data = []
            for cell in row:
                value = cell.value
                if value is None:
                    value = ""
                else:
                    value = str(value)
                row_data.append(value)
            
            # Проверяем, не пустая ли строка
            if any(cell for cell in row_data):
                data.append(row_data)
        
        return data
    
    def _create_table(self, data: List[List], sheet: Worksheet) -> Table:
        """Создает отформатированную таблицу для PDF"""
        if not data:
            return None
        
        # Определяем ширину колонок
        num_cols = len(data[0]) if data else 0
        page_width = self.page_size[0] - 20*mm  # Вычитаем отступы
        col_width = page_width / num_cols if num_cols > 0 else 50*mm
        
        # Ограничиваем ширину колонок
        if col_width > 60*mm:
            col_width = 60*mm
        elif col_width < 20*mm:
            col_width = 20*mm
        
        col_widths = [col_width] * num_cols
        
        # Создаем таблицу
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Базовый стиль таблицы
        style = TableStyle([
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Тело таблицы
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            
            # Границы
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Чередующиеся цвета строк
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
        ])
        
        table.setStyle(style)
        
        return table
    
    def export_with_summary(self, excel_path: str, pdf_path: Optional[str] = None, 
                          summary_info: Optional[dict] = None) -> str:
        """
        Экспортирует Excel в PDF с добавлением сводной информации
        
        Args:
            excel_path: Путь к Excel файлу
            pdf_path: Путь к выходному PDF
            summary_info: Дополнительная информация для сводки
        
        Returns:
            Путь к созданному PDF файлу
        """
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Файл не найден: {excel_path}")
        
        if not pdf_path:
            base_name = os.path.splitext(excel_path)[0]
            pdf_path = f"{base_name}_with_summary.pdf"
        
        # Загружаем Excel
        wb = load_workbook(excel_path, data_only=True)
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=self.page_size,
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        story = []
        
        # Титульная страница
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=15,
            alignment=TA_CENTER
        )
        
        story.append(Spacer(1, 30*mm))
        story.append(Paragraph("<b>BOM Categorizer</b>", title_style))
        story.append(Paragraph("<b>Отчет по обработке BOM</b>", title_style))
        story.append(Spacer(1, 20*mm))
        
        # Сводная информация
        if summary_info:
            info_style = ParagraphStyle(
                'Info',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                alignment=TA_LEFT
            )
            
            story.append(Paragraph("<b>Сводная информация:</b>", info_style))
            story.append(Spacer(1, 5*mm))
            
            for key, value in summary_info.items():
                story.append(Paragraph(f"<b>{key}:</b> {value}", info_style))
            
            story.append(Spacer(1, 10*mm))
        
        # Информация о листах
        info_style = ParagraphStyle(
            'Info',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        story.append(Paragraph(f"<b>Количество листов:</b> {len(wb.sheetnames)}", info_style))
        story.append(Paragraph(f"<b>Листы:</b> {', '.join(wb.sheetnames)}", info_style))
        story.append(Spacer(1, 5*mm))
        
        from datetime import datetime
        story.append(Paragraph(f"<b>Дата создания:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))
        
        story.append(PageBreak())
        
        # Содержимое листов
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            
            sheet_title_style = ParagraphStyle(
                'SheetTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2563eb'),
                spaceAfter=8,
                alignment=TA_LEFT
            )
            
            sheet_title = Paragraph(f"<b>{sheet_name}</b>", sheet_title_style)
            story.append(sheet_title)
            story.append(Spacer(1, 5*mm))
            
            data = self._get_sheet_data(sheet)
            
            if data:
                # Добавляем информацию о количестве записей
                count_style = ParagraphStyle(
                    'Count',
                    parent=self.styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#6b7280'),
                    spaceAfter=4
                )
                story.append(Paragraph(f"Всего записей: {len(data) - 1}", count_style))  # -1 для заголовка
                story.append(Spacer(1, 3*mm))
                
                table = self._create_table(data, sheet)
                story.append(table)
            else:
                empty_text = Paragraph("<i>Лист пуст</i>", self.styles['Normal'])
                story.append(empty_text)
            
            story.append(Spacer(1, 10*mm))
            
            if sheet_name != wb.sheetnames[-1]:
                story.append(PageBreak())
        
        # Сборка PDF
        doc.build(story)
        
        return pdf_path


def export_bom_to_pdf(excel_path: str, output_pdf: Optional[str] = None, 
                     with_summary: bool = True, summary_info: Optional[dict] = None) -> str:
    """
    Удобная функция для экспорта BOM в PDF
    
    Args:
        excel_path: Путь к Excel файлу с результатами
        output_pdf: Путь к выходному PDF (опционально)
        with_summary: Включить сводную информацию
        summary_info: Дополнительная информация для сводки
    
    Returns:
        Путь к созданному PDF файлу
    """
    exporter = PDFExporter()
    
    if with_summary:
        return exporter.export_with_summary(excel_path, output_pdf, summary_info)
    else:
        return exporter.export_excel_to_pdf(excel_path, output_pdf)

