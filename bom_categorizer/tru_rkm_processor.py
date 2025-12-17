# -*- coding: utf-8 -*-
"""
Модуль обработки файлов ТРУ и РКМ

Обрабатывает .xls файлы ТРУ и РКМ:
- Извлекает нужные столбцы
- Переименовывает столбцы
- Объединяет столбцы
- Сохраняет в новый .xlsx файл
"""

import os
import re
from typing import List, Dict, Optional, Tuple
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


def detect_file_type(filename: str) -> Optional[str]:
    """
    Определяет тип файла по имени
    Поддерживает кириллицу и латиницу, а также смешанные написания.
    
    Args:
        filename: Имя файла
        
    Returns:
        'tpy' если содержит вариации TRU/TRY/TPY
        'rkm' если содержит вариации RKM/PKM
        None если не определено
    """
    filename_lower = filename.lower()
    
    # Шаблоны для ТРУ (TRU/TRY/TPY)
    # Включают кириллицу 'тру' и латиницу 'try', 'tru', 'tpy'
    # Также учитываем визуально похожие написания
    tru_patterns = [
        'try', 'tpy', 'tru',  # Latin
        'тру',                # Cyrillic
        'тpy', 'tру', 'tpу'   # Mixed variations
    ]
    
    # Шаблоны для РКМ (RKM/PKM)
    # Включают кириллицу 'ркм' и латиницу 'rkm', 'pkm'
    rkm_patterns = [
        'rkm', 'pkm',         # Latin
        'ркм',                # Cyrillic
        'pкм', 'ркm'          # Mixed variations
    ]
    
    if any(pattern in filename_lower for pattern in tru_patterns):
        return 'tpy'
    elif any(pattern in filename_lower for pattern in rkm_patterns):
        return 'rkm'
    
    return None


def generate_output_filename(input_path: str, file_type: str) -> str:
    """
    Генерирует имя выходного файла
    
    Args:
        input_path: Путь к входному файлу
        file_type: Тип файла ('tpy' или 'rkm')
        
    Returns:
        Полный путь к выходному файлу
    """
    directory = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    # Добавляем суффикс перед расширением
    suffix = f"_{file_type}"
    output_filename = f"{name_without_ext}{suffix}.xlsx"
    output_path = os.path.join(directory, output_filename)
    
    # Проверяем существование и добавляем счетчик если нужно
    if os.path.exists(output_path):
        counter = 1
        while True:
            output_filename = f"{name_without_ext}{suffix}_{counter}.xlsx"
            output_path = os.path.join(directory, output_filename)
            if not os.path.exists(output_path):
                break
            counter += 1
    
    return output_path


def process_tru_file(input_path: str, output_path: str) -> Tuple[bool, str]:
    """
    Обрабатывает ТРУ файл
    
    Args:
        input_path: Путь к входному .xls файлу
        output_path: Путь к выходному .xlsx файлу
        
    Returns:
        (success, message): Успешность и сообщение
    """
    try:
        # Используем xlrd напрямую для указания кодировки
        import xlrd
        workbook = xlrd.open_workbook(input_path, encoding_override='cp1251')
        sheet = workbook.sheet_by_index(0)
        
        # Конвертируем данные в список списков
        data = []
        for row_idx in range(sheet.nrows):
            data.append([sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)])
            
        # Создаем DataFrame
        df = pd.DataFrame(data)
        
        # Проверяем что файл не пустой и есть хотя бы 2 строки
        if len(df) < 2:
            return False, "Файл слишком мал или пуст"
        
        # Строка 1 содержит заголовки столбцов
        # Данные начинаются со строки 2
        # Берем нужные столбцы по индексам:
        # 0: Артикул
        # 1: Наименование
        # 4: Количество заявлено в БЕИ
        # 8: Цена в руб
        # 9: Сумма в ДВ
        # 14: Группа ответственных
        # 16: Код группы ответственных
        
        # Извлекаем данные начиная со строки 2 (индекс 2)
        data_df = df.iloc[2:].copy()
        
        # Выбираем нужные столбцы
        result_df = pd.DataFrame()
        result_df['Артикул'] = data_df.iloc[:, 0]
        result_df['Наименование'] = data_df.iloc[:, 1]
        result_df['Количество'] = data_df.iloc[:, 4]
        result_df['Цена'] = data_df.iloc[:, 8]
        result_df['Стоимость'] = data_df.iloc[:, 9]
        
        # Объединяем "Группа ответственных" и "Код группы ответственных"
        # Порядок: Код + Название группы
        group_resp = data_df.iloc[:, 14].fillna('')
        code_resp = data_df.iloc[:, 16].fillna('')
        
        # Конвертируем коды в int где возможно, чтобы убрать .0
        def format_code(val):
            try:
                if pd.isna(val): return ""
                return str(int(float(val)))
            except:
                return str(val)
        
        code_resp_formatted = code_resp.apply(format_code)
        
        # Объединяем: Код + пробел + Группа
        result_df['Ответственные'] = (code_resp_formatted + ' ' + group_resp.astype(str)).str.strip()
        
        # Удаляем пустые строки (где все значения NaN)
        result_df = result_df.dropna(how='all')
        
        # Сохраняем в Excel с форматированием
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='ТРУ')
            
            # Получаем worksheet для форматирования
            worksheet = writer.sheets['ТРУ']
            
            # Стили
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF', size=11)
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            center_align = Alignment(horizontal='center', vertical='center')
            left_align = Alignment(horizontal='left', vertical='center')
            
            # Форматируем заголовки
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            
            # Форматируем данные
            for row in worksheet.iter_rows(min_row=2):
                # Артикул (A) - по центру (или слева если длинный)
                row[0].alignment = left_align
                # Наименование (B) - слева
                row[1].alignment = left_align
                # Количество (C) - по центру
                row[2].alignment = center_align
                # Цена (D) - по центру
                row[3].alignment = center_align
                # Стоимость (E) - по центру
                row[4].alignment = center_align
                # Ответственные (F) - слева
                row[5].alignment = left_align

            # Автоматическая ширина столбцов с запасом
            column_widths = {
                'A': 15, # Артикул
                'B': 50, # Наименование
                'C': 12, # Количество
                'D': 15, # Цена
                'E': 15, # Стоимость
                'F': 40  # Ответственные
            }
            
            for col_letter, width in column_widths.items():
                worksheet.column_dimensions[col_letter].width = width
        
        rows_processed = len(result_df)
        return True, f"Успешно обработано {rows_processed} строк"
        
    except Exception as e:
        return False, f"Ошибка обработки: {str(e)}"


def process_rkm_file(input_path: str, output_path: str) -> Tuple[bool, str]:
    """
    Обрабатывает РКМ файл
    
    TODO: Реализовать когда будет известна структура
    
    Args:
        input_path: Путь к входному .xls файлу
        output_path: Путь к выходному .xlsx файлу
        
    Returns:
        (success, message): Успешность и сообщение
    """
    return False, "Обработка РКМ файлов пока не реализована"


def process_tru_rkm_files(file_paths: List[str], progress_callback=None) -> Dict[str, Dict[str, any]]:
    """
    Обрабатывает список ТРУ/РКМ файлов
    
    Args:
        file_paths: Список путей к файлам
        progress_callback: Функция для отчета о прогрессе (optional)
        
    Returns:
        Словарь {input_path: {'success': bool, 'output_path': str, 'message': str}}
    """
    results = {}
    
    for i, input_path in enumerate(file_paths):
        filename = os.path.basename(input_path)
        
        # Определяем тип файла
        file_type = detect_file_type(filename)
        
        if file_type is None:
            results[input_path] = {
                'success': False,
                'output_path': None,
                'message': 'Не удалось определить тип файла (ТРУ или РКМ)'
            }
            continue
        
        # Генерируем имя выходного файла
        output_path = generate_output_filename(input_path, file_type)
        
        # Обрабатываем файл
        if file_type == 'tpy':
            success, message = process_tru_file(input_path, output_path)
        elif file_type == 'rkm':
            success, message = process_rkm_file(input_path, output_path)
        else:
            success = False
            message = f"Неизвестный тип файла: {file_type}"
        
        results[input_path] = {
            'success': success,
            'output_path': output_path if success else None,
            'message': message
        }
        
        # Отчет о прогрессе
        if progress_callback:
            progress_callback(i + 1, len(file_paths), filename, success)
    
    return results
