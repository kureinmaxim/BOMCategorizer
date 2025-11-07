"""
Модуль для извлечения замен и подборов из примечаний DOC файлов
"""

import re
import pandas as pd


def extract_podbor_elements(df: pd.DataFrame) -> pd.DataFrame:
    """
    Извлекает замены и подборы из примечания и добавляет их как отдельные строки
    
    Два типа:
    1. ЗАМЕНЫ - альтернативные компоненты (с ключевыми словами "замена", "допуск")
       Пример: "Допуск. замена на AD9221AR, ф.Analog Devices"
       
    2. ПОДБОРЫ - варианты номиналов для одного типа компонента
       Пример: "1 кОм; 1,87 кОм" или "100 пФ, 150 пФ"
    
    Args:
        df: DataFrame с распарсенными данными
        
    Returns:
        DataFrame с добавленными элементами замен и подборов
    """
    if df.empty:
        return df
    
    # Проверяем наличие нужных колонок
    if 'original_note' not in df.columns and 'note' not in df.columns and 'Примечание' not in df.columns:
        return df
    
    new_rows = []
    
    for idx, row in df.iterrows():
        # Проверяем наличие позиционного обозначения (основной элемент)
        ref = str(row.get('reference', '')).strip() if pd.notna(row.get('reference')) else ''
        
        # Получаем примечание (приоритет: original_note → note → Примечание)
        note = ''
        if 'original_note' in df.columns and pd.notna(row.get('original_note')):
            note = str(row.get('original_note')).strip()
        elif 'note' in df.columns and pd.notna(row.get('note')):
            note = str(row.get('note')).strip()
        elif 'Примечание' in df.columns and pd.notna(row.get('Примечание')):
            note = str(row.get('Примечание')).strip()
        
        # DEBUG: Выводим информацию о строке
        # if 'C21' in ref or 'C22' in ref:
        #     print(f"  [DEBUG-C] {ref} - note: '{note[:60] if note else '(пусто)'}', len: {len(note)}")
        
        # Проверяем, содержит ли примечание служебную фразу (не подборы!)
        is_service_note = bool(note and ('допускается отсутствие' in note.lower() or 'справ.' in note.lower()))
        
        # Проверяем есть ли подборы/замены в примечании
        # НЕ извлекаем подборы из служебных фраз типа "допускается отсутствие"
        has_podbor = bool(note and ref and (',' in note or ';' in note or 'замена' in note.lower()) and not is_service_note)
        
        # Если есть подборы - нужно обработать note у оригинального компонента
        # (чтобы список подборов не попал в ТУ/Примечание оригинала)
        if has_podbor:
            row_dict = row.to_dict()
            
            # ВАЖНО: Если в note есть ТУ-код или производитель, сохраняем его!
            # Проверяем паттерн ТУ: "АЛЯР.434110.005ТУ" или "ОЖ0.460.107ТУ"
            # Или производитель: Mini-Circuits, Hittite и т.д.
            current_note = row_dict.get('note', '')
            
            # Проверяем есть ли это замена (содержит "замена" в original_note)
            orig_note_val = row_dict.get('original_note', '')
            is_replacement = bool(orig_note_val and 'замена' in orig_note_val.lower())
            
            # Определяем, что в note: ТУ, производитель или список подборов
            has_tu_in_note = bool(current_note and ('ТУ' in current_note or re.search(r'[А-ЯЁ]{2,}\.\d+[\d\.\-]*ТУ', current_note)))
            has_commas_in_note = bool(current_note and (',' in current_note or ';' in current_note))
            is_short_note = bool(current_note and len(current_note) < 50)
            
            # Если в note есть список артикулов (запятые + длина > 30), это подборы - очищаем
            looks_like_podbor_list = has_commas_in_note and len(current_note) > 30
            
            if has_tu_in_note:
                # В note есть ТУ-код - сохраняем его
                pass
            elif is_replacement and current_note:
                # Это замена и в note есть производитель - сохраняем
                pass
            elif is_short_note and not has_commas_in_note:
                # В note производитель (короткая строка без разделителей) - сохраняем
                pass
            elif looks_like_podbor_list:
                # В note список подборов - очищаем!
                row_dict['note'] = ''
            else:
                # Другие случаи - очищаем для безопасности
                row_dict['note'] = ''
            
            # original_note и Примечание всегда очищаем (там подборы/замены)
            if 'original_note' in row_dict:
                row_dict['original_note'] = ''
            if 'Примечание' in row_dict:
                row_dict['Примечание'] = ''
            new_rows.append(row_dict)
        else:
            # Нет подборов - добавляем как есть
            new_rows.append(row.to_dict())
        
        # Только для строк с позиционным обозначением ищем подборы/замены
        if not ref or not note:
            continue
        
        # Определяем тип: ЗАМЕНА или ПОДБОР
        # ВАЖНО: "допуск" и "допускается" проверяем ТОЛЬКО в контексте замены!
        # "допуск. замена" → это замена
        # "допускается отсутствие" → это НЕ замена, это подбор!
        note_lower = note.lower()
        
        # Проверяем наличие явных маркеров замены
        has_zamena_keyword = 'замена' in note_lower or 'замен' in note_lower
        has_dopusk_context = ('допуск' in note_lower or 'допускается' in note_lower) and 'замена' in note_lower
        
        is_replacement = has_zamena_keyword or has_dopusk_context
        
        # DEBUG для C2*
        # if 'C21' in ref or 'C22' in ref:
        #     print(f"  [DEBUG-C] {ref}: is_replacement={is_replacement}, note_lower[:50]='{note_lower[:50]}'")
        
        if is_replacement:
            # Обрабатываем ЗАМЕНЫ (альтернативные компоненты)
            extracted_items = _extract_replacements(note, row)
            tag = '(замена)'
        else:
            # Обрабатываем ПОДБОРЫ (номиналы)
            extracted_items = _extract_podbors(note, row)
            tag = '(подбор)'
        
        # Добавляем найденные элементы
        if extracted_items:
            print(f"  [ПОДБОРЫ] {ref}: найдено {len(extracted_items)} элементов {tag}")
            for item in extracted_items:
                # Распаковываем: для замен это (артикул, производитель), для подборов просто строка
                if is_replacement and isinstance(item, tuple):
                    item_desc, item_manufacturer = item
                else:
                    item_desc = item if isinstance(item, str) else str(item)
                    item_manufacturer = ""
                
                print(f"    -> {item_desc}")
                new_row = row.to_dict().copy()
                
                # Удаляем производителя из description подборного элемента (если есть)
                # Производитель будет в note, не нужно дублировать
                # Стратегия: оставляем только артикул (все до первых двух+ пробелов или до "ф.")
                # Примеры:
                #   "PAT-0+           ф. Mini-Circuits" → "PAT-0+"
                #   "PAT-10+. Mini-Circuits" → "PAT-10+"
                #   "GRM1555C1H1R0B" → "GRM1555C1H1R0B"
                
                # 1. Если есть "ф." - отрезаем все до него
                if ' ф.' in item_desc or '\tф.' in item_desc:
                    item_desc_clean = re.split(r'\s+ф\.', item_desc)[0].strip()
                # 2. Если есть 2+ пробела подряд - отрезаем все после них
                elif re.search(r'\s{2,}', item_desc):
                    item_desc_clean = re.split(r'\s{2,}', item_desc)[0].strip()
                # 3. Если есть точка с пробелом или точка в конце - удаляем производителя после точки
                elif '. ' in item_desc or item_desc.endswith('.'):
                    # Удаляем "точка + пробел + слова" в конце
                    item_desc_clean = re.sub(r'\.\s+[A-Z][A-Za-z\-\s]+$', '', item_desc, flags=re.IGNORECASE).strip()
                else:
                    item_desc_clean = item_desc.strip()
                
                # Удаляем точку в конце (после всех обработок)
                item_desc_clean = item_desc_clean.rstrip('.')
                
                new_row['description'] = item_desc_clean
                new_row['reference'] = ''  # Подборы/замены не имеют позиционного обозначения
                
                # ВАЖНО: Сначала очищаем все поля с примечаниями и ТУ
                # Потом копируем только реальный ТУ (если он есть)
                new_row['note'] = ''
                new_row['original_note'] = ''
                if 'Примечание' in new_row:
                    new_row['Примечание'] = ''
                if 'ТУ' in new_row:
                    new_row['ТУ'] = ''
                if 'tu' in new_row:
                    new_row['tu'] = ''
                
                # ПРИОРИТЕТ 1: Если это замена и есть производитель из списка замен - используем его
                if is_replacement and item_manufacturer:
                    new_row['note'] = item_manufacturer
                else:
                    # ПРИОРИТЕТ 2: Копируем ТУ/производителя из оригинального компонента
                    # ТУ/производитель может быть в разных местах:
                    # 1. В колонке 'tu' или 'ТУ' (для XLSX файлов)
                    # 2. В поле 'note' или 'original_note' (для DOCX файлов, где ТУ в примечании)
                    # 3. В самом description оригинального компонента (например, "PAT-1+ ф. Mini-Circuits")
                    
                    # Сначала пытаемся извлечь производителя из description оригинального компонента
                    orig_desc = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
                    manufacturer_from_desc = ''
                    if orig_desc:
                        # Ищем паттерн "ф. Производитель" в описании оригинального компонента
                        mfr_match = re.search(r'ф\.\s*([A-Za-zА-ЯЁа-яё0-9\s\-]+)', orig_desc)
                        if mfr_match:
                            manufacturer_from_desc = mfr_match.group(1).strip()
                    
                    if 'tu' in row.index and pd.notna(row.get('tu')):
                        tu_val = str(row.get('tu')).strip()
                        # Проверяем что это реальный ТУ, а не подборы
                        if 'ту' in tu_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', tu_val):
                            new_row['tu'] = tu_val
                    elif 'ТУ' in row.index and pd.notna(row.get('ТУ')):
                        tu_val = str(row.get('ТУ')).strip()
                        # Проверяем что это реальный ТУ, а не подборы
                        if 'ту' in tu_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', tu_val):
                            new_row['ТУ'] = tu_val
                    elif 'note' in row.index and pd.notna(row.get('note')):
                        # Проверяем, что note содержит ТУ или производителя (а не подборы/замены)
                        note_val = str(row.get('note')).strip()
                        # Паттерн ТУ: АЛЯР.434110.005 ТУ или АЛЯР.431320.420ТУ
                        # Или производитель: Mini-Circuits, Hittite, и т.д.
                        if 'ту' in note_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', note_val):
                            # Это ТУ - копируем его
                            new_row['note'] = note_val
                        elif 'замена' in note_val.lower():
                            # В note текст замены - используем производителя из description
                            if manufacturer_from_desc:
                                new_row['note'] = manufacturer_from_desc
                        elif manufacturer_from_desc:
                            # В note нет ТУ, но есть производитель в description - копируем его
                            new_row['note'] = manufacturer_from_desc
                        elif len(note_val) > 0 and len(note_val) < 100 and not (',' in note_val or ';' in note_val):
                            # Возможно это производитель (короткая строка без разделителей)
                            new_row['note'] = note_val
                    elif 'original_note' in row.index and pd.notna(row.get('original_note')):
                        # Проверяем original_note на наличие ТУ
                        note_val = str(row.get('original_note')).strip()
                        if 'ту' in note_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', note_val):
                            new_row['note'] = note_val
                        elif manufacturer_from_desc:
                            # В original_note нет ТУ, но есть производитель в description
                            new_row['note'] = manufacturer_from_desc
                    elif manufacturer_from_desc:
                        # Нет note/original_note, но есть производитель в description - используем его
                        new_row['note'] = manufacturer_from_desc
                
                # Помечаем источник КОМПАКТНО
                # Вместо: "Plata_preobrz.docx (подбор) для R48*"
                # Делаем: "Plata_preobrz.docx (п/б R48*)"
                # При агрегации получится: "Plata_preobrz.docx (п/б R48*), (п/б R49*)"
                if 'source_file' in new_row and pd.notna(new_row['source_file']):
                    source = str(new_row['source_file'])
                    # Убираем старые пометки, если есть
                    source = re.sub(r'\s*,?\s*\((замена|п/б|подбор).*?\)', '', source).strip()
                    
                    # Сокращаем тег: "(подбор)" → "(п/б)", "(замена)" → "(зам)"
                    short_tag = "(п/б" if tag == "(подбор)" else "(зам"
                    
                    # Добавляем компактную пометку (без запятой перед первой пометкой)
                    new_row['source_file'] = f"{source} {short_tag} {ref})"
                
                # Примечания уже очищены выше (строки 98-105)
                # ТУ скопирован только если он действительно есть
                
                new_rows.append(new_row)
    
    # Создаем новый DataFrame
    result_df = pd.DataFrame(new_rows)
    
    return result_df


def _extract_replacements(note: str, row: dict) -> list:
    """
    Извлекает замены из примечания с производителями
    
    Пример 1: "50HFFA-010-2/6SMA, ф. JFW; QFA1802-18-1-S, ф. Qualwave"
    Пример 2: "Доп. замена: Розетка D-SUB p/n: 09 67 025 4715, ф. Harting"
    
    Результат: [("50HFFA-010-2/6SMA", "JFW"), ("Розетка D-SUB p/n: 09 67 025 4715", "Harting"), ...]
    
    Args:
        note: Текст примечания
        row: Строка данных компонента
        
    Returns:
        Список кортежей (наименование, производитель)
    """
    replacements = []
    
    # Ищем текст после различных вариантов "замена"
    # Варианты: "замена на", "допускается замена на", "Доп. замена:"
    pattern = r'(?:замена\s+на|допуск\.\s*замена\s+на|допускается\s+замена\s+на|доп\.\s*замена:)\s+(.+?)(?:\.\s*$|$)'
    match = re.search(pattern, note, re.IGNORECASE | re.DOTALL)
    
    if not match:
        return replacements
    
    replacements_text = match.group(1).strip()
    main_desc = str(row.get('description', '')).strip()
    
    # Нормализуем переносы строк: объединяем многострочные описания
    # "Розетка D-SUB\np/n: 09 67 025 4715, ф. Harting" → "Розетка D-SUB p/n: 09 67 025 4715, ф. Harting"
    replacements_text = re.sub(r'\n+', ' ', replacements_text).strip()
    replacements_text = re.sub(r'\s+', ' ', replacements_text)  # Нормализуем множественные пробелы
    
    # Разбиваем по точкам с запятой - это границы между группами разных производителей
    # Пример: "50HFFA-010-2/6SMA, ф. JFW; QFA1802-18-1-S, QFA1802-18-3-S, ф. Qualwave"
    groups = [g.strip() for g in replacements_text.split(';')]
    
    for group in groups:
        if not group or len(group) < 3:
            continue
        
        # Ищем производителя в группе (ф. ...)
        mfr_pattern = r'ф\.\s*([A-Za-z][A-Za-z0-9\s\-]+?)(?:\s*$|[,;])'
        mfr_match = re.search(mfr_pattern, group)
        
        manufacturer = mfr_match.group(1).strip() if mfr_match else ""
        
        # Убираем производителя из группы, остается описание с артикулом
        group_without_mfr = re.sub(r',?\s*ф\.\s*[A-Za-z][A-Za-z0-9\s\-]+', '', group).strip()
        
        # Для разъемов и других компонентов, где артикул может быть в формате "p/n: ..."
        # Не разделяем по запятым если это одна сложная строка
        # Проверяем: если есть "p/n:" и только одна запятая (перед производителем), это один компонент
        if 'p/n:' in group_without_mfr.lower() or 'p/n ' in group_without_mfr.lower():
            # Один компонент с артикулом p/n
            parts = [group_without_mfr]
        else:
            # Разделяем артикулы по запятым
            parts = [p.strip().rstrip('.').strip() for p in group_without_mfr.split(',')]
        
        for part in parts:
            # Проверяем что это не пустая строка
            if not part or len(part) < 3:
                continue
            
            # Проверяем что это похоже на компонент (содержит буквы и цифры/символы)
            # Для разъемов допускаем пробелы и специальные символы
            if re.search(r'[A-Za-zА-ЯЁа-яё]', part):
                # Проверяем что это не то же самое наименование
                if part.lower().strip() != main_desc.lower().strip():
                    replacements.append((part.strip(), manufacturer))
    
    return replacements


def _extract_podbors(note: str, row: dict) -> list:
    """
    Извлекает подборы (номиналы) из примечания
    
    Пример для R48*: "1 кОм; 1,87 кОм"
    Результат: ["Р1-12-0,1-1 кОм ±2%-Т", "Р1-12-0,1-1,87 кОм ±2%-Т"]
    
    Args:
        note: Текст примечания
        row: Строка данных компонента
        
    Returns:
        Список полных описаний с новыми номиналами
    """
    podbors = []
    
    # Получаем основное описание
    main_desc = str(row.get('description', '')).strip()
    
    # ВАЖНО: Для некоторых компонентов (PAT, оптика, специфичные модули)
    # производитель может быть в note, а не в description
    # Для стандартных резисторов/конденсаторов производитель обычно НЕ указывается!
    note_val = str(row.get('note', '')).strip() if pd.notna(row.get('note')) else ''
    
    # Если note содержит разделитель | - берем последнюю часть (там может быть производитель)
    if '|' in note_val:
        parts = note_val.split('|')
        mfr_candidate = parts[-1].strip()
    else:
        mfr_candidate = note_val
    
    # Проверяем типичные паттерны производителей (ТОЛЬКО для специфичных компонентов!)
    # Для стандартных резисторов/конденсаторов с ТУ - производитель НЕ нужен
    mfr_patterns = ['mini-circuit', 'murata', 'coilcraft', 'tdk', 'yageo', 'vishay', 'kemet', 
                    'panasonic', 'analog devices', 'hittite', 'api technologies']
    
    if mfr_candidate and len(mfr_candidate) < 100:
        # Проверяем что это известный производитель
        if any(mfr in mfr_candidate.lower() for mfr in mfr_patterns):
            # Проверяем что это НЕ подбор (нет запятых/точек с запятой)
            if not any(sep in mfr_candidate for sep in [',', ';']):
                # Это производитель - добавляем к описанию
                main_desc = f"{main_desc} ф. {mfr_candidate}"
    
    # Паттерны номиналов (с единицами измерения)
    # Резисторы: Ом, кОм, МОм
    # Конденсаторы: пФ, нФ, мкФ
    # Индуктивности: Гн, мГн, мкГн, нГн
    # ВАЖНО: Пробел между числом и единицей ОПЦИОНАЛЬНЫЙ (\s*) для поддержки "6,8Ом" и "6,8 Ом"
    # Паттерн для чисел: \d+(?:[,.]\d+)? - поддерживает "6,8" и "6.8" и "10"
    # Word boundary (\b) в начале, чтобы не ловить артикулы типа "GRM1555C1H100G"
    nominal_patterns = [
        r'\b(\d+(?:[,.]\d+)?)\s*(МОм|мом|мом|MΩ|MΩ)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(кОм|ком|кОм|kΩ|kΩ)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(Ом|ом|Ω|Ω)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(мкФ|мкф|μF|uF)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(нФ|нф|nF)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(пФ|пф|pF)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(мГн|мгн|mH)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(мкГн|мкгн|μH|uH)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(нГн|нгн|nH)\b',
        r'\b(\d+(?:[,.]\d+)?)\s*(Гн|гн|H)\b',
    ]
    
    # Убираем служебные фразы ИЗ ВСЕГО примечания (ДО разбиения)
    # Это важно, чтобы не потерять артикулы в конце примечания
    # Например: "GRM1555C1H270G, допускается отсутствие" → "GRM1555C1H270G"
    note_cleaned = note
    cleanup_phrases = [
        r'допускается\s+отсутствие\.?',
        r'допускается\s+замена',
        r'справ\.?',
        r'см\.\s+примечание',
    ]
    for phrase in cleanup_phrases:
        note_cleaned = re.sub(phrase, '', note_cleaned, flags=re.IGNORECASE)
    
    # СНАЧАЛА извлекаем все номиналы из примечания
    # Это важно, чтобы запятая в "6,8Ом" не воспринималась как разделитель
    extracted_nominals = []
    for pattern in nominal_patterns:
        matches = re.finditer(pattern, note_cleaned, re.IGNORECASE)
        for match in matches:
            value = match.group(1).replace(',', '.')
            unit = match.group(2)
            unit_normalized = _normalize_unit(unit)
            found_nominal = f"{value} {unit_normalized}"
            extracted_nominals.append((match.start(), match.end(), found_nominal))
    
    # Если нашли номиналы, обрабатываем их
    if extracted_nominals:
        for start, end, nominal in extracted_nominals:
            new_desc = _replace_nominal_in_description(main_desc, nominal)
            if new_desc and new_desc != main_desc:
                podbors.append(new_desc)
        
        # Ранний выход - номиналы обработаны
        return podbors
    
    # Если номиналов нет, разбиваем примечание на части (по запятым и точкам с запятой)
    # для поиска артикулов
    note_parts = re.split(r'[,;]', note_cleaned)
    
    # Дополнительное разбиение: если в части есть несколько артикулов через пробел
    # Например: "PAT-3+ PAT-4+" → ["PAT-3+", "PAT-4+"]
    expanded_parts = []
    for part in note_parts:
        part = part.strip()
        if not part:
            continue
        
        # Паттерн для артикулов с + в конце (Mini-Circuits стиль)
        # Пример: PAT-1+, ZX60-P103LN+
        if re.search(r'[A-Z0-9\-]+\+\s+[A-Z0-9\-]+\+', part, re.IGNORECASE):
            # Разбиваем по пробелам между артикулами
            sub_parts = re.findall(r'[A-Z0-9А-ЯЁ\-]+\+', part, re.IGNORECASE)
            expanded_parts.extend(sub_parts)
        else:
            expanded_parts.append(part)
    
    # Обрабатываем артикулы (если номиналов не было найдено ранее)
    for part in expanded_parts:
        part = part.strip().rstrip('.')  # Удаляем точку в конце
        if not part:
            continue
        
        # Пропускаем строки с оставшимися служебными словами
        part_lower = part.lower()
        skip_keywords = ['примечание', 'гост', 'ту ', 'осту']
        if any(kw in part_lower for kw in skip_keywords):
            continue
        
        # Проверяем, является ли часть артикулом компонента
        # Паттерн артикула: буквы+цифры (например, GRM1555C1H1R0B, К53-65А, PAT-2+)
        # Должен содержать хотя бы одну букву и одну цифру, длина > 3
        if len(part) > 3 and re.search(r'[A-Za-zА-ЯЁа-яё]', part) and re.search(r'\d', part):
            # Проверяем, что это не то же самое наименование
            main_desc_normalized = main_desc.replace(' ', '').replace('-', '').lower()
            part_normalized = part.replace(' ', '').replace('-', '').lower()
            
            if part_normalized not in main_desc_normalized:
                # Это артикул - заменяем его в оригинальном описании
                # чтобы сохранить контекст (производителя, модель и т.д.)
                new_desc = _replace_artikul_in_description(main_desc, part)
                
                if new_desc and new_desc != main_desc:
                    podbors.append(new_desc)
                else:
                    # Если не удалось заменить - добавляем как есть
                    # (для случаев когда описание не содержит артикул)
                    podbors.append(part)
    
    return podbors


def _replace_artikul_in_description(description: str, new_artikul: str) -> str:
    """
    Заменяет артикул в описании на новый, сохраняя остальной контекст
    
    Примеры:
        "PAT-0+ ф. Mini-Circuits" + "PAT-1+" → "PAT-1+ ф. Mini-Circuits"
        "GRM1885C2A100J, ф. Murata" + "GRM1885C2A150J" → "GRM1885C2A150J, ф. Murata"
        "Конденсатор К53-65 100 мкФ" + "К53-65А" → "Конденсатор К53-65А 100 мкФ"
    
    Args:
        description: Оригинальное описание компонента
        new_artikul: Новый артикул из подбора
        
    Returns:
        Описание с замененным артикулом
    """
    # Удаляем точку в конце артикула (если есть)
    new_artikul = new_artikul.rstrip('.')
    
    # Паттерн для поиска артикула в описании
    # Артикул: буквы/цифры/дефис/плюс, длина >= 3
    # Должен быть до запятой, "ф.", или в начале строки
    
    # Попытка 1: Артикул в начале строки до первой запятой или "ф."
    match = re.search(r'^([A-Z0-9А-ЯЁ\-\+]+(?:\s*[A-Z0-9А-ЯЁ\-\+]+)*?)(?:\s*[,.]|\s+ф\.)', 
                     description, re.IGNORECASE)
    if match:
        old_artikul = match.group(1).strip()
        # Проверяем что найденный артикул содержит и буквы и цифры
        if re.search(r'[A-Za-zА-ЯЁа-яё]', old_artikul) and re.search(r'\d', old_artikul):
            # Заменяем старый артикул на новый
            new_desc = description.replace(old_artikul, new_artikul, 1)
            return new_desc
    
    # Попытка 2: Артикул в начале строки (если нет запятой/ф.)
    match = re.search(r'^([A-Z0-9А-ЯЁ\-\+]+)', description, re.IGNORECASE)
    if match:
        old_artikul = match.group(1).strip()
        if len(old_artikul) >= 3:
            if re.search(r'[A-Za-zА-ЯЁа-яё]', old_artikul) and re.search(r'\d', old_artikul):
                new_desc = description.replace(old_artikul, new_artikul, 1)
                return new_desc
    
    # Попытка 3: Если в description есть производитель (ф. ...) - добавляем его к новому артикулу
    # Это для случаев когда подборный артикул не похож на оригинальный
    # Пример: "PAT-0+ ф. Mini-Circuits" + "PAT-2+" → "PAT-2+ ф. Mini-Circuits"
    # ВАЖНО: Делаем это ТОЛЬКО для специфичных производителей (не для стандартных ТУ!)
    mfr_match = re.search(r'ф\.\s*(.+?)(?:\s*,|$)', description, re.IGNORECASE)
    if mfr_match:
        mfr = mfr_match.group(1).strip()
        # Проверяем что это известный производитель (не просто ТУ или случайный текст)
        known_mfrs = ['mini-circuit', 'murata', 'coilcraft', 'tdk', 'yageo', 'vishay', 
                      'kemet', 'panasonic', 'analog', 'hittite', 'api', 'qualwave']
        if any(known in mfr.lower() for known in known_mfrs):
            return f"{new_artikul} ф. {mfr}"
    
    # Если не удалось найти артикул для замены - возвращаем новый артикул
    # (для случаев типа "Аттенюатор" → нужно вернуть "PAT-1+")
    return new_artikul


def _normalize_unit(unit: str) -> str:
    """Нормализует единицу измерения к стандартному виду"""
    unit_lower = unit.lower()
    
    # Сопротивление
    if unit_lower in ['мом', 'mω', 'mω']:
        return 'МОм'
    elif unit_lower in ['ком', 'кОм', 'kω', 'kω']:
        return 'кОм'
    elif unit_lower in ['ом', 'ω', 'ω']:
        return 'Ом'
    
    # Емкость
    elif unit_lower in ['мкф', 'μf', 'uf']:
        return 'мкФ'
    elif unit_lower in ['нф', 'nf']:
        return 'нФ'
    elif unit_lower in ['пф', 'pf']:
        return 'пФ'
    
    # Индуктивность
    elif unit_lower in ['мгн', 'mh']:
        return 'мГн'
    elif unit_lower in ['мкгн', 'μh', 'uh']:
        return 'мкГн'
    elif unit_lower in ['нгн', 'nh']:
        return 'нГн'
    elif unit_lower in ['гн', 'h']:
        return 'Гн'
    
    return unit


def _replace_nominal_in_description(desc: str, new_nominal: str) -> str:
    """
    Заменяет номинал в описании компонента
    
    Пример:
        desc = "Р1-12-0,1-536 Ом ±2%-Т"
        new_nominal = "1 кОм"
        result = "Р1-12-0,1-1 кОм ±2%-Т"
    """
    # Паттерн для поиска номинала в описании
    # Ищем число + единица измерения (Ом, кОм, пФ, мкФ и т.д.)
    # Паттерн для чисел: \d+(?:[,.]\d+)? - поддерживает "6,8" и "6.8" и "10"
    # Word boundary (\b) для предотвращения ложных срабатываний
    nominal_in_desc_pattern = r'\b(\d+(?:[,.]\d+)?)\s*(МОм|мом|кОм|ком|Ом|ом|мкФ|мкф|нФ|нф|пФ|пф|мГн|мгн|мкГн|мкгн|нГн|нгн|Гн|гн)\b'
    
    # Заменяем найденный номинал на новый
    result = re.sub(nominal_in_desc_pattern, new_nominal, desc, count=1, flags=re.IGNORECASE)
    
    return result
