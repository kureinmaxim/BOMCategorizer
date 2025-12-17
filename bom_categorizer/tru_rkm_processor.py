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


def _read_tru_file(input_path: str) -> Optional[pd.DataFrame]:
    """
    Читает один ТРУ файл и возвращает сырой DataFrame с нужными колонками
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
            return None
            
        # Извлекаем данные начиная со строки 2 (индекс 2)
        data_df = df.iloc[2:].copy()
        
        # Выбираем нужные столбцы
        result_df = pd.DataFrame()
        result_df['Артикул'] = data_df.iloc[:, 0]
        result_df['Наименование'] = data_df.iloc[:, 1]
        result_df['Количество'] = data_df.iloc[:, 4]
        result_df['Цена'] = data_df.iloc[:, 8]
        result_df['Стоимость'] = data_df.iloc[:, 9] # Будет пересчитано, но берем для структуры
        
        # Данные для колонки Ответственные
        result_df['_group_resp'] = data_df.iloc[:, 14].fillna('')
        result_df['_code_resp'] = data_df.iloc[:, 16].fillna('')
        
        return result_df
        
    except Exception as e:
        print(f"Ошибка чтения {input_path}: {e}")
        return None

def process_tru_files_batch(input_paths: List[str], output_path: str) -> Tuple[bool, str]:
    """
    Обрабатывает несколько ТРУ файлов и сохраняет в один
    """
    try:
        all_dfs = []
        
        for path in input_paths:
            df = _read_tru_file(path)
            if df is not None:
                all_dfs.append(df)
        
        if not all_dfs:
            return False, "Не удалось прочитать ни одного файла"
            
        # Объединяем все DataFrame
        result_df = pd.concat(all_dfs, ignore_index=True)
        
        # Обработка колонки "Ответственные"
        # Конвертируем коды в int где возможно
        def format_code(val):
            try:
                if pd.isna(val): return ""
                return str(int(float(val)))
            except:
                return str(val)
        
        code_resp_formatted = result_df['_code_resp'].apply(format_code)
        
        # Объединяем: Код + пробел + Группа
        result_df['Ответственные'] = (code_resp_formatted + ' ' + result_df['_group_resp'].astype(str)).str.strip()
        
        # Очистка и сортировка
        # Очистка цен и количеств
        def parse_price(val):
            try:
                if isinstance(val, (int, float)):
                    return float(val)
                val_str = str(val).replace(',', '.').replace(' ', '')
                return float(val_str)
            except:
                return 0.0
                
        result_df['Количество'] = result_df['Количество'].apply(parse_price)
        result_df['Цена'] = result_df['Цена'].apply(parse_price)
        
        # Рассчитываем стоимость для сортировки (по формуле)
        result_df['Стоимость'] = result_df['Количество'] * result_df['Цена']
        
        # Сортировка
        # 1. По коду (числовому)
        result_df['_sort_key_code'] = pd.to_numeric(result_df['_code_resp'], errors='coerce').fillna(float('inf'))
        
        # Сортируем: Код, затем Цена
        result_df = result_df.sort_values(by=['_sort_key_code', 'Цена'], ascending=[True, True])
        
        # Удаляем временные колонки
        result_df = result_df.drop(columns=['_group_resp', '_code_resp', '_sort_key_code'])
        
        # Удаляем пустые строки
        result_df = result_df.dropna(how='all')
        
        # Сохраняем (логика с openpyxl такая же как раньше)
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='ТРУ')
            
            worksheet = writer.sheets['ТРУ']
            
            # Стили
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF', size=11)
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            center_align = Alignment(horizontal='center', vertical='center')
            left_align = Alignment(horizontal='left', vertical='center')
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            
            for row in worksheet.iter_rows(min_row=2):
                row[0].alignment = left_align # Артикул
                row[1].alignment = left_align # Наименование
                row[2].alignment = center_align # Количество
                
                # Цена
                row[3].alignment = center_align
                row[3].number_format = '#,##0.00'
                
                # Стоимость (Формула)
                row_idx = row[0].row
                cell = row[4]
                cell.value = f"=C{row_idx}*D{row_idx}"
                cell.alignment = center_align
                cell.number_format = '#,##0.00'
                
                row[5].alignment = left_align # Ответственные

            column_widths = {'A': 15, 'B': 50, 'C': 12, 'D': 15, 'E': 15, 'F': 40}
            for col_letter, width in column_widths.items():
                worksheet.column_dimensions[col_letter].width = width
            
            # ИТОГО
            last_row = len(result_df) + 1
            total_row = last_row + 2
            
            total_label_cell = worksheet.cell(row=total_row, column=4, value="ИТОГО:")
            total_label_cell.font = Font(bold=True, size=12)
            total_label_cell.alignment = Alignment(horizontal='right', vertical='center')
            
            total_value_cell = worksheet.cell(row=total_row, column=5, value=f"=SUM(E2:E{last_row})")
            total_value_cell.font = Font(bold=True, size=12)
            total_value_cell.alignment = Alignment(horizontal='center', vertical='center')
            total_value_cell.number_format = '#,##0.00'
            
            top_border = Border(top=Side(border_style="double", color="000000"))
            total_label_cell.border = top_border
            total_value_cell.border = top_border
            
            total_fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
            total_label_cell.fill = total_fill
            total_value_cell.fill = total_fill
            
        # Пересохранение через COM
        try:
            import platform
            if platform.system() == 'Windows':
                _resave_with_excel_com(output_path)
        except:
            pass
            
        return True, f"Объединено и обработано {len(all_dfs)} файлов, {len(result_df)} строк"
        
    except Exception as e:
        return False, f"Ошибка пакетной обработки: {str(e)}"

def process_tru_rkm_files(file_paths: List[str], progress_callback=None) -> Dict[str, Dict[str, any]]:
    """
    Обрабатывает список ТРУ/РКМ файлов
    ТРУ файлы объединяются в один.
    """
    results = {}
    
    # Разделяем файлы по типам
    tru_files = []
    rkm_files = []
    
    for i, path in enumerate(file_paths):
        ft = detect_file_type(os.path.basename(path))
        if ft == 'tpy':
            tru_files.append(path)
        elif ft == 'rkm':
            rkm_files.append(path)
        else:
            results[path] = {'success': False, 'message': 'Unknown file type'}
            if progress_callback: progress_callback(i+1, len(file_paths), os.path.basename(path), False)
            
    # Обработка ТРУ файлов (объединение)
    if tru_files:
        # Имя выходного файла берем из первого файла
        output_path = generate_output_filename(tru_files[0], 'tpy')
        
        if progress_callback:
             progress_callback(1, len(file_paths), "Объединение ТРУ файлов...", True)
             
        success, msg = process_tru_files_batch(tru_files, output_path)
        
        # Записываем результат для всех входных файлов
        for path in tru_files:
            results[path] = {
                'success': success,
                'output_path': output_path if success else None,
                'message': msg
            }
            
    # Обработка РКМ (пока поштучно, т.к. не реализовано)
    for path in rkm_files:
         output_path = generate_output_filename(path, 'rkm')
         success, msg = process_rkm_file(path, output_path)
         results[path] = {'success': success, 'output_path': output_path, 'message': msg}
         
    return results
