"""
Модуль для извлечения подборных элементов из примечаний DOC файлов
"""

import re
import pandas as pd


def extract_podbor_elements(df: pd.DataFrame) -> pd.DataFrame:
    """
    Извлекает подборные элементы из примечания и добавляет их как отдельные строки
    
    В DOC файлах после основного элемента в примечании могут быть указаны
    варианты замены (подборы). Например:
    
    C22* → GRM1885C2A220J (основной)
    Примечание:
        GRM1885C2A100J  ← подбор
        GRM1885C2A150J  ← подбор
    
    Args:
        df: DataFrame с распарсенными данными
        
    Returns:
        DataFrame с добавленными подборными элементами
    """
    if df.empty:
        return df
    
    # Проверяем наличие нужных колонок
    if 'original_note' not in df.columns and 'note' not in df.columns and 'Примечание' not in df.columns:
        return df
    
    new_rows = []
    
    for idx, row in df.iterrows():
        # Добавляем основную строку
        new_rows.append(row.to_dict())
        
        # Проверяем наличие позиционного обозначения (основной элемент)
        ref = str(row.get('reference', '')).strip() if pd.notna(row.get('reference')) else ''
        
        # Только для строк с позиционным обозначением ищем подборы
        if not ref:
            continue
        
        # Получаем примечание (приоритет: original_note → note → Примечание)
        note = ''
        if 'original_note' in df.columns and pd.notna(row.get('original_note')):
            note = str(row.get('original_note')).strip()
        elif 'note' in df.columns and pd.notna(row.get('note')):
            note = str(row.get('note')).strip()
        elif 'Примечание' in df.columns and pd.notna(row.get('Примечание')):
            note = str(row.get('Примечание')).strip()
        
        if not note:
            continue
        
        # Разбиваем примечание на строки И на запятые (подборы могут быть через запятую)
        note_lines = []
        for line in note.split('\n'):
            # Разбиваем каждую строку по запятым
            for part in line.split(','):
                part = part.strip()
                if part:
                    note_lines.append(part)
        
        # Паттерн для определения наименования компонента
        # Типичные форматы: GRM1885C2A100J, К10-17в, 1272ПН3Т, HMC435AMS8GE, 0603HP-2N2XJ
        component_pattern = r'^([A-Za-zА-ЯЁа-яё0-9\-]+\d+[A-Za-zА-ЯЁа-яё0-9\-]*)'
        
        podbor_found = False
        
        for line in note_lines:
            # Пропускаем строки с ключевыми словами (не компоненты)
            line_lower = line.lower()
            skip_keywords = [
                'допускается', 'отсутствие', 'примечание', 'или', 'и',
                'справ', 'см.', 'гост', 'ту ', 'осту', 'можно', 'использовать'
            ]
            
            if any(kw in line_lower for kw in skip_keywords):
                continue
            
            # Проверяем, содержит ли строка наименование компонента
            match = re.match(component_pattern, line)
            if match:
                component_name = match.group(1).strip()
                
                # Проверяем что это не то же самое наименование что и основной элемент
                main_desc = str(row.get('description', '')).strip()
                # Нормализуем пробелы для сравнения
                main_desc_normalized = main_desc.replace(' ', '').replace('-', '')
                component_normalized = component_name.replace(' ', '').replace('-', '')
                
                if component_name and component_normalized != main_desc_normalized and len(component_name) > 3:
                    podbor_found = True
                    
                    # Создаем новую строку для подбора
                    podbor_row = row.to_dict().copy()
                    podbor_row['description'] = component_name
                    podbor_row['reference'] = ''  # Подборы не имеют позиционного обозначения
                    
                    # Помечаем источник как (подбор)
                    if 'source_file' in podbor_row and pd.notna(podbor_row['source_file']):
                        source = str(podbor_row['source_file'])
                        if '(подбор)' not in source:
                            podbor_row['source_file'] = source + ' (подбор)'
                    
                    # Очищаем примечания у подбора (чтобы не было рекурсии)
                    if 'original_note' in podbor_row:
                        podbor_row['original_note'] = ''
                    if 'note' in podbor_row:
                        podbor_row['note'] = ''
                    if 'Примечание' in podbor_row:
                        podbor_row['Примечание'] = ''
                    
                    new_rows.append(podbor_row)
        
        # Если были найдены подборы, очищаем примечания у основной строки
        if podbor_found and new_rows:
            # Очищаем примечания в основной строке (первая в new_rows для этого idx)
            # Находим основную строку (та что добавлена первой в начале цикла)
            main_row_idx = len(new_rows) - 1
            while main_row_idx >= 0:
                if new_rows[main_row_idx].get('reference') == ref:
                    # Это основная строка с позиционным обозначением
                    if 'original_note' in new_rows[main_row_idx]:
                        new_rows[main_row_idx]['original_note'] = ''
                    if 'note' in new_rows[main_row_idx]:
                        new_rows[main_row_idx]['note'] = ''
                    break
                main_row_idx -= 1
    
    # Создаем новый DataFrame
    result_df = pd.DataFrame(new_rows)
    
    return result_df
