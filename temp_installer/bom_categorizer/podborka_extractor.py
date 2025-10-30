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
        # Добавляем основную строку
        new_rows.append(row.to_dict())
        
        # Проверяем наличие позиционного обозначения (основной элемент)
        ref = str(row.get('reference', '')).strip() if pd.notna(row.get('reference')) else ''
        
        # Только для строк с позиционным обозначением ищем подборы/замены
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
        
        # DEBUG: Выводим информацию о строке
        # if 'C21' in ref or 'C22' in ref:
        #     print(f"  [DEBUG-C] {ref} - note: '{note[:60] if note else '(пусто)'}', len: {len(note)}")
        
        if not note:
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
            for item_desc in extracted_items:
                print(f"    -> {item_desc}")
                new_row = row.to_dict().copy()
                new_row['description'] = item_desc
                new_row['reference'] = ''  # Подборы/замены не имеют позиционного обозначения
                
                # Копируем ТУ из оригинального компонента (если есть)
                # ТУ может быть в разных местах:
                # 1. В колонке 'tu' или 'ТУ' (для XLSX файлов)
                # 2. В поле 'note' (для DOCX файлов, где ТУ в примечании)
                if 'tu' in row.index and pd.notna(row.get('tu')):
                    new_row['tu'] = row.get('tu')
                elif 'ТУ' in row.index and pd.notna(row.get('ТУ')):
                    new_row['ТУ'] = row.get('ТУ')
                elif 'note' in row.index and pd.notna(row.get('note')):
                    # Проверяем, что note содержит ТУ (а не подборы/замены)
                    note_val = str(row.get('note')).strip()
                    # Паттерн ТУ: АЛЯР.434110.005 ТУ или АЛЯР.431320.420ТУ
                    if 'ту' in note_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', note_val):
                        # Это ТУ - копируем его
                        new_row['note'] = note_val
                
                # Помечаем источник КОМПАКТНО
                # Вместо: "Plata_preobrz.docx (подбор) для R48*"
                # Делаем: "Plata_preobrz.docx, (п/б R48*)"
                # При агрегации получится: "Plata_preobrz.docx, (п/б R48*), (п/б R49*)"
                if 'source_file' in new_row and pd.notna(new_row['source_file']):
                    source = str(new_row['source_file'])
                    # Убираем старые пометки, если есть
                    source = re.sub(r'\s*,?\s*\((замена|п/б|подбор).*?\)', '', source).strip()
                    
                    # Сокращаем тег: "(подбор)" → "(п/б)", "(замена)" → "(зам)"
                    short_tag = "(п/б" if tag == "(подбор)" else "(зам"
                    
                    # Добавляем компактную пометку
                    new_row['source_file'] = f"{source}, {short_tag} {ref})"
                
                # Очищаем примечания (чтобы не было рекурсии)
                # Но сохраняем note, если там ТУ (мы его скопировали выше)
                if 'original_note' in new_row:
                    new_row['original_note'] = ''  # Всегда очищаем (там подборы)
                
                # note очищаем ТОЛЬКО если там НЕ ТУ
                if 'note' in new_row:
                    note_val = str(new_row.get('note', '')).strip()
                    # Если note НЕ содержит ТУ - очищаем
                    if not note_val or not ('ту' in note_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', note_val)):
                        new_row['note'] = ''
                
                if 'Примечание' in new_row:
                    new_row['Примечание'] = ''
                
                new_rows.append(new_row)
    
    # Создаем новый DataFrame
    result_df = pd.DataFrame(new_rows)
    
    return result_df


def _extract_replacements(note: str, row: dict) -> list:
    """
    Извлекает замены из примечания
    
    Пример: "Допуск. замена на AD9221AR, ф.Analog Devices"
    Результат: ["AD9221AR"]
    
    Args:
        note: Текст примечания
        row: Строка данных компонента
        
    Returns:
        Список наименований замен
    """
    replacements = []
    
    # Ищем паттерн "замена на [наименование]"
    # Паттерны для поиска замен:
    # 1. "замена на XXXXX"
    # 2. "допуск. замена на XXXXX"
    # 3. "допускается замена на XXXXX"
    
    # Паттерн для извлечения наименования после "замена на"
    patterns = [
        r'(?:замена\s+на|допуск\.\s*замена\s+на|допускается\s+замена\s+на)\s+([A-Za-zА-ЯЁа-яё0-9\-\+]+)',
        r'(?:допуск\.\s+|допускается\s+)([A-Za-zА-ЯЁа-яё0-9\-\+]+)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, note, re.IGNORECASE)
        for match in matches:
            component_name = match.group(1).strip()
            
            # Убираем производителя, если он есть (после запятой или "ф.")
            # Пример: "AD9221AR, ф.Analog Devices" → "AD9221AR"
            component_name = re.split(r',\s*ф\.|,\s*производитель', component_name, flags=re.IGNORECASE)[0].strip()
            
            # Проверяем что это не служебное слово
            skip_words = ['замена', 'допуск', 'допускается', 'на', 'или', 'и']
            if component_name.lower() in skip_words:
                continue
            
            # Проверяем что это не то же самое наименование
            main_desc = str(row.get('description', '')).strip()
            if component_name.lower() not in main_desc.lower() and len(component_name) > 3:
                # Проверяем что содержит хотя бы одну цифру (типичный признак партномера)
                if re.search(r'\d', component_name):
                    replacements.append(component_name)
    
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
    
    # Паттерны номиналов (с единицами измерения)
    # Резисторы: Ом, кОм, МОм
    # Конденсаторы: пФ, нФ, мкФ
    # Индуктивности: Гн, мГн, мкГн, нГн
    # ВАЖНО: Требуем ПРОБЕЛ перед единицей, чтобы не ловить артикулы типа GRM1555C1H1R0B
    nominal_patterns = [
        r'(\d+[,.]?\d*)\s+(МОм|мом|мом|MΩ|MΩ)',
        r'(\d+[,.]?\d*)\s+(кОм|ком|кОм|kΩ|kΩ)',
        r'(\d+[,.]?\d*)\s+(Ом|ом|Ω|Ω)',
        r'(\d+[,.]?\d*)\s+(мкФ|мкф|μF|uF)',
        r'(\d+[,.]?\d*)\s+(нФ|нф|nF)',
        r'(\d+[,.]?\d*)\s+(пФ|пф|pF)',
        r'(\d+[,.]?\d*)\s+(мГн|мгн|mH)',
        r'(\d+[,.]?\d*)\s+(мкГн|мкгн|μH|uH)',
        r'(\d+[,.]?\d*)\s+(нГн|нгн|nH)',
        r'(\d+[,.]?\d*)\s+(Гн|гн|H)',
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
    
    # Разбиваем примечание на части (по запятым и точкам с запятой)
    note_parts = re.split(r'[,;]', note_cleaned)
    
    for part in note_parts:
        part = part.strip()
        if not part:
            continue
        
        # Пропускаем строки с оставшимися служебными словами
        part_lower = part.lower()
        skip_keywords = ['примечание', 'гост', 'ту ', 'осту']
        if any(kw in part_lower for kw in skip_keywords):
            continue
        
        # Проверяем, содержит ли часть номинал
        found_nominal = None
        for pattern in nominal_patterns:
            match = re.search(pattern, part, re.IGNORECASE)
            if match:
                # Нормализуем номинал (заменяем запятую на точку для чисел)
                value = match.group(1).replace(',', '.')
                unit = match.group(2)
                
                # Приводим единицу к стандартному виду
                unit_normalized = _normalize_unit(unit)
                
                found_nominal = f"{value} {unit_normalized}"
                break
        
        if found_nominal:
            # Создаем полное описание с новым номиналом
            # Заменяем старый номинал на новый в описании
            new_desc = _replace_nominal_in_description(main_desc, found_nominal)
            if new_desc and new_desc != main_desc:
                podbors.append(new_desc)
        else:
            # Если номинал не найден, проверяем, является ли часть артикулом компонента
            # Паттерн артикула: буквы+цифры (например, GRM1555C1H1R0B, К53-65А)
            # Должен содержать хотя бы одну букву и одну цифру, длина > 5
            if len(part) > 5 and re.search(r'[A-Za-zА-ЯЁа-яё]', part) and re.search(r'\d', part):
                # Проверяем, что это не то же самое наименование
                main_desc_normalized = main_desc.replace(' ', '').replace('-', '').lower()
                part_normalized = part.replace(' ', '').replace('-', '').lower()
                
                if part_normalized not in main_desc_normalized:
                    # Это артикул - добавляем как есть
                    podbors.append(part)
    
    return podbors


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
    nominal_in_desc_pattern = r'(\d+[,.]?\d*)\s*(МОм|мом|кОм|ком|Ом|ом|мкФ|мкф|нФ|нф|пФ|пф|мГн|мгн|мкГн|мкгн|нГн|нгн|Гн|гн)'
    
    # Заменяем найденный номинал на новый
    result = re.sub(nominal_in_desc_pattern, new_nominal, desc, count=1, flags=re.IGNORECASE)
    
    return result
