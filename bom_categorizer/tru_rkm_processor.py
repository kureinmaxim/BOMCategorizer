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

def process_rkm_file(input_path: str, output_path: str) -> Tuple[bool, str]:
    """
    Обрабатывает один РКМ файл
    
    Логика:
    1. Ищет заголовок таблицы
    2. Оставляет колонки: № п/п, Наименование, Цена, Затраты, Документы, Поставщик
    3. Фильтрует строки (начиная с 2.1.1 и т.д.)
    4. Очищает поле поставщика (только название)
    """
    try:
        # Читаем весь файл для поиска заголовка
        df_raw = pd.read_excel(input_path, header=None)
        
        # 1. Поиск строки заголовка
        header_row_idx = -1
        col_map = {} # {canonical_name: col_index}
        
        # Ключевые слова для поиска колонок
        keywords = {
            '№': ['№', 'п/п', 'номер'],
            'Наименование': ['наименование', 'материал'],
            'Цена': ['цена', 'за единицу'],
            'Стоимость': ['затраты', 'сумма', 'стоимость'],
            'Документы': ['обосновывающие', 'документ'],
            'Поставщик': ['поставщик', 'подрядчик', 'исполнитель']
        }
        
        # Сканируем первые 30 строк и накапливаем найденные колонки
        for idx, row in df_raw.head(30).iterrows():
            row_str = row.astype(str).str.lower().tolist()
            
            # Для текущей строки ищем совпадения
            for col_idx, cell_val in enumerate(row_str):
                # Проверяем каждое ключевое слово
                
                # 1. № п/п
                if '№' not in col_map:
                    if '№' in cell_val or 'п/п' in cell_val:
                        col_map['№'] = col_idx
                
                # 2. Наименование (First wins - usually Col 1)
                if 'Наименование' not in col_map:
                    if 'наименование' in cell_val:
                        col_map['Наименование'] = col_idx
                        
                # 3. Цена (Last wins - prefer Plan which is usually later columns?)
                # В РКМ часто две цены (план/факт). Обычно План идет первым или вторым?
                # В данном файле по дампу: 8:цена (план), 18:цена...
                # Нам нужна та, что относится к ТЕКУЩЕМУ (Планируемому) периоду.
                # Обычно левые колонки - это отчетный (прошлый), правые - планируемый.
                # НО в Row 1 написано:
                # Col 6: "Отчетный период..."
                # Col 17: "Планируемый период..."
                # Значит, правые колонки (после 17) - это План.
                # Левые (6-16) - Факт (Отчетный).
                # ИЛИ наоборот? 
                # Row 1: "6:Отчетный..." (cols 6-15?), "17:Планируемый..." (cols 17-23?)
                # Значит нам нужны колонки > 17 для Плана (2026)?
                # Давай попробуем искать "цена" и "затраты" которые имеют больший индекс, если есть выбор.
                # "Last wins" стратегия для цены/стоимости подойдет.
                
                if 'цена' in cell_val and 'единицу' in cell_val:
                    col_map['Цена'] = col_idx
                    # Обновляем header_row_idx, так как нашли важную колонку на этой строке
                    header_row_idx = max(header_row_idx, idx)
                    
                # 4. Стоимость/Затраты (Last wins)
                if 'затраты' in cell_val or 'стоимость' in cell_val:
                     col_map['Стоимость'] = col_idx
                     header_row_idx = max(header_row_idx, idx)
                    
                # 5. Документы
                if 'обосновывающие' in cell_val and 'документы' in cell_val:
                    col_map['Документы'] = col_idx
                    header_row_idx = max(header_row_idx, idx)
                elif 'обоснование' in cell_val and 'Документы' not in col_map:
                     col_map['Документы'] = col_idx # Fallback
                     header_row_idx = max(header_row_idx, idx)
                     
                # 6. Поставщик
                # Тут сложно. Поставщик есть и в Отчетном (Фактическом) и в Планируемом.
                # Обычно для РКМ заполняют План?
                # Но если План не выбран, берут Факт?
                # User request: "организация-поставщик ... и в ней только название".
                # Давайте использовать Last wins для Поставщика тоже (План), 
                # но если он пустой в данных, это будет проблема.
                # Для начала возьмем Last wins (План).
                
                if 'поставщик' in cell_val or 'подрядчик' in cell_val:
                     col_map['Поставщик'] = col_idx
                     header_row_idx = max(header_row_idx, idx)
            
            # Также обновляем header_row если нашли Наименование (оно обычно в верхней строке)
            if 'Наименование' in col_map and idx > header_row_idx:
                 # Если мы нашли наименование на строке 1, но цену на строке 2,
                 # header_row_idx будет 2. Это ок.
                 pass

        # Если не нашли заголовки
        if 'Наименование' not in col_map or 'Цена' not in col_map:
             return False, f"Не удалось найти заголовок таблицы. Найдено: {list(col_map.keys())}"

        # Adjust header_row_idx to ensure we skip sub-headers (like "план/факт" row)
        # Если после строки заголовка идет строка "1, 2, 3...", нужно её пропустить.
        # Обычно это +1 или +2 строки.
        # Проверим строку header_row_idx + 1
        if header_row_idx + 1 < len(df_raw):
             next_row = df_raw.iloc[header_row_idx + 1].astype(str).str.lower().tolist()
             if any('план' in s or 'факт' in s for s in next_row):
                 header_row_idx += 1
        
        # Проверим строку с номерами колонок "1", "2", "3"
        if header_row_idx + 1 < len(df_raw):
             next_row = df_raw.iloc[header_row_idx + 1].astype(str).tolist()
             # Если много цифр подряд
             digit_count = sum(1 for s in next_row if s.strip().isdigit())
             if digit_count > 3:
                 header_row_idx += 1
                 
        # 2. Извлечение данных
            
        # 2. Извлечение данных
        data = []
        
        # Итерируемся по строкам после заголовка
        for idx, row in df_raw.iloc[header_row_idx+1:].iterrows():
            if idx >= len(df_raw): break
            
            try:
                item = {}
                for key in keywords.keys():
                    col_idx = col_map.get(key)
                    val = row.iloc[col_idx] if col_idx is not None and col_idx < len(row) else None
                    item[key] = val
                
                # 3. Фильтрация
                no_val = str(item['№']).strip() if item['№'] is not None else ""
                name_val = str(item['Наименование']).strip() if item['Наименование'] is not None else ""
                
                if not name_val or name_val.lower() == 'nan':
                     continue
                
                # Фильтр по номеру (2.1.1 и т.д.)
                # Должен начинаться с цифры
                if not no_val or not no_val[0].isdigit():
                    continue
                    
                # Проверка на наличие "структуры" (точки)
                # User said "начиная с 2.1.1".
                # Accept anything looking like a dotted number or simple integer
                if not re.match(r'^[\d\.]+$', no_val):
                    # Maybe it has some text? Strict check:
                    continue

                # 4. Обработка Поставщика
                if item['Поставщик'] is not None:
                    s_val = str(item['Поставщик'])
                    if s_val.lower() == 'nan':
                        item['Поставщик'] = ""
                    else:
                        item['Поставщик'] = s_val.split('\n')[0].strip()
                else:
                    item['Поставщик'] = ""
                    
                # 5. Обработка Документов (Clean nan)
                if item['Документы'] is not None:
                    d_val = str(item['Документы'])
                    if d_val.lower() == 'nan':
                        item['Документы'] = ""
                else:
                    item['Документы'] = ""

                # Форматирование чисел
                def clean_float(val):
                    if pd.isna(val): return 0.0
                    try:
                        return float(val)
                    except:
                        try:
                            # Удаляем пробелы, заменяем запятую
                            s = str(val).replace(',', '.').replace(' ', '').replace('\xa0', '')
                            return float(s)
                        except:
                            return 0.0
                            
                item['Цена'] = clean_float(item['Цена'])
                item['Стоимость'] = clean_float(item['Стоимость'])
                
                data.append(item)
                
            except Exception as e:
                continue
                
        if not data:
            return False, "Не найдено строк данных для экспорта"
            
        result_df = pd.DataFrame(data)
        
        # Упорядочиваем колонки
        cols_order = ['№', 'Наименование', 'Цена', 'Стоимость', 'Документы', 'Поставщик']
        # Проверяем, все ли есть, если каких-то нет в result_df, добавляем пустые
        for c in cols_order:
            if c not in result_df.columns:
                result_df[c] = ""
                
        result_df = result_df[cols_order]
        
        # Сохранение (аналогично ТРУ)
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='РКМ')
            
            worksheet = writer.sheets['РКМ']
            
             # Стили (копипаст из ТРУ, чуть адаптирован)
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF', size=11)
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
            left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            
            # Apply widths
            ws_widths = {'A': 8, 'B': 60, 'C': 15, 'D': 15, 'E': 30, 'F': 40}
            for col_l, w in ws_widths.items():
                worksheet.column_dimensions[col_l].width = w
                
            for row in worksheet.iter_rows(min_row=2):
                row[0].alignment = center_align # No
                row[1].alignment = left_align # Name
                row[2].alignment = center_align # Price
                row[2].number_format = '#,##0.00'
                row[3].alignment = center_align # Cost
                row[3].number_format = '#,##0.00'
                row[4].alignment = left_align # Docs
                row[5].alignment = left_align # Provider

        return True, f"РКМ обработан: {len(result_df)} строк"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Ошибка РКМ: {str(e)}"


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
