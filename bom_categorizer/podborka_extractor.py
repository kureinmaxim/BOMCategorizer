"""
Модуль для извлечения замен и подборов из примечаний DOC файлов
"""

import re
import pandas as pd
import sys
from functools import wraps
import time


# ============================================================
# ЗАЩИТА ОТ ЗАВИСАНИЙ
# ============================================================

class TimeoutError(Exception):
    """Исключение при превышении времени выполнения"""
    pass


def timeout_function(max_seconds=30):
    """
    Декоратор для ограничения времени выполнения функции.
    Если функция выполняется дольше max_seconds, возвращает исходные данные.
    
    Важно: Это мягкий таймаут - он проверяет время между вызовами,
    но не прерывает выполнение regex (для этого нужен отдельный механизм).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Добавляем start_time в kwargs для проверки внутри функции
            kwargs['_start_time'] = start_time
            kwargs['_max_seconds'] = max_seconds
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                if elapsed > max_seconds * 0.8:  # Предупреждение при 80% времени
                    print(f"⚠️  Функция {func.__name__} выполнялась {elapsed:.1f}s (близко к лимиту {max_seconds}s)", 
                          file=sys.stderr, flush=True)
                return result
            except TimeoutError:
                print(f"⏱️  TIMEOUT: Функция {func.__name__} превысила лимит {max_seconds}s, возвращаю исходные данные",
                      file=sys.stderr, flush=True)
                # Возвращаем исходные данные (первый аргумент должен быть DataFrame)
                if args:
                    return args[0]
                return pd.DataFrame()
            except Exception as e:
                print(f"❌ ОШИБКА в {func.__name__}: {e}", file=sys.stderr, flush=True)
                # Возвращаем исходные данные
                if args:
                    return args[0]
                return pd.DataFrame()
        
        return wrapper
    return decorator


def check_timeout(start_time, max_seconds, context=""):
    """
    Проверяет не истекло ли время выполнения.
    Вызывается в критических точках внутри функции.
    """
    if start_time and max_seconds:
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            raise TimeoutError(f"Превышен лимит времени в {context}: {elapsed:.1f}s > {max_seconds}s")


def is_complex_string(text: str, max_length=500, max_dashes=10, max_repeating_chars=20) -> bool:
    """
    Проверяет, является ли строка слишком сложной для безопасной обработки regex.
    
    ВАЖНО: Не блокирует списки артикулов через запятую/точку с запятой,
    т.к. это валидные подборы, которые можно безопасно разбить по разделителю.
    
    Args:
        text: строка для проверки
        max_length: максимальная безопасная длина
        max_dashes: максимальное количество дефисов (вызывают backtracking)
        max_repeating_chars: максимальное количество повторяющихся символов подряд
        
    Returns:
        True если строка слишком сложная и НЕ является списком подборов
    """
    if not text:
        return False
    
    # ИСКЛЮЧЕНИЕ: Если строка содержит много запятых/точек с запятой,
    # это скорее всего список подборов (например, "2100-L-3-2-1-1-1-2, 2100-L-3-2-1-2-1-2, ...")
    # Такие строки БЕЗОПАСНЫ - мы просто разобьем их по разделителям
    comma_count = text.count(',')
    semicolon_count = text.count(';')
    total_separators = comma_count + semicolon_count
    
    # Если есть >= 3 разделителей, считаем это списком артикулов
    if total_separators >= 3:
        # Проверяем, что это действительно список (не один длинный паттерн)
        # Разбиваем по запятой/точке с запятой и проверяем длину частей
        parts = re.split(r'[,;]\s*', text)
        if len(parts) >= 3:
            # Если большинство частей короткие (< 100 символов), это список
            short_parts = sum(1 for p in parts if len(p.strip()) < 100)
            if short_parts >= len(parts) * 0.7:  # 70% частей короткие
                return False  # Это безопасный список, не блокируем
    
    # Проверка длины
    if len(text) > max_length:
        return True
    
    # Проверка количества дефисов (только если это НЕ список артикулов)
    if text.count('-') > max_dashes:
        return True
    
    # Проверка повторяющихся символов (например, "--------------------")
    for char in ['-', '_', '.', ',', ';', ' ']:
        if char * max_repeating_chars in text:
            return True
    
    return False


@timeout_function(max_seconds=60)  # Максимум 60 секунд на обработку всего файла
def extract_podbor_elements(df: pd.DataFrame, _start_time=None, _max_seconds=None) -> pd.DataFrame:
    """
    Извлекает замены и подборы из примечания и добавляет их как отдельные строки
    
    Два типа:
    1. ЗАМЕНЫ - альтернативные компоненты (с ключевыми словами "замена", "допуск")
       Пример: "Допуск. замена на AD9221AR, ф.Analog Devices"
       
    2. ПОДБОРЫ - варианты номиналов для одного типа компонента
       Пример: "1 кОм; 1,87 кОм" или "100 пФ, 150 пФ"
    
    Args:
        df: DataFrame с распарсенными данными
        _start_time: время начала (для проверки таймаута, добавляется автоматически)
        _max_seconds: максимальное время (добавляется автоматически)
        
    Returns:
        DataFrame с добавленными элементами замен и подборов
        
    Note:
        Функция защищена от зависаний:
        - Общий таймаут 60 секунд
        - Пропуск слишком сложных строк (длинных, с множеством дефисов)
        - Защита от regex catastrophic backtracking
    """
    if df.empty:
        return df
    
    # Проверяем наличие нужных колонок
    if 'original_note' not in df.columns and 'note' not in df.columns and 'Примечание' not in df.columns:
        return df
    
    new_rows = []
    
    for idx, row in df.iterrows():
        # Проверка таймаута на каждой итерации
        try:
            check_timeout(_start_time, _max_seconds, f"iteration {idx}/{len(df)}")
        except TimeoutError:
            # Если превышен таймаут, возвращаем то что успели обработать
            print(f"⏱️  TIMEOUT на итерации {idx}/{len(df)}, возвращаю частичный результат", 
                  file=sys.stderr, flush=True)
            return pd.DataFrame(new_rows)
        
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
        
        # Защита от сложных строк (могут вызвать зависание regex)
        if is_complex_string(note):
            print(f"⚠️  Пропускаю {ref}: note слишком сложная (len={len(note)}, dashes={note.count('-')})",
                  file=sys.stderr, flush=True)
            # Добавляем элемент как есть, без обработки подборов
            new_rows.append(row.to_dict())
            continue
        
        # DEBUG: Выводим информацию о строке
        # if 'C21' in ref or 'C22' in ref:
        #     print(f"  [DEBUG-C] {ref} - note: '{note[:60] if note else '(пусто)'}', len: {len(note)}")
        
        # Проверяем есть ли подборы/замены в примечании
        # Признаки подборов: запятые, точки с запятой, слово "замена"
        has_separators = bool(note and (',' in note or ';' in note))
        has_zamena = bool(note and 'замена' in note.lower())
        
        # Проверяем, содержит ли примечание служебную фразу (БЕЗ подборов!)
        # ВАЖНО: "допуск. отсутствие" может быть в КОНЦЕ списка подборов!
        # Пример: "121 кОм, 162 кОм; допуск. отсутствие" - это ПОДБОРЫ + пояснение
        # НЕ считаем служебной, если есть номиналы (Ом, кОм, мкФ и т.д.)
        has_nominals = bool(note and re.search(r'\d+(?:[,\.]\d+)?\s*(?:МОм|мом|кОм|ком|Ом|ом|мкФ|мкф|нФ|нф|пФ|пф|мГн|мгн|мкГн|мкгн)', note, re.IGNORECASE))
        is_service_note = bool(note and not has_nominals and (
            'допускается отсутствие' in note.lower() or 
            'допуск. отсутствие' in note.lower() or 
            'справ.' in note.lower()
        ))
        
        # Извлекаем подборы если есть разделители ИЛИ замена, И это НЕ служебная фраза
        has_podbor = bool(note and ref and (has_separators or has_zamena) and not is_service_note)
        
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
            # Проверяем есть ли в note номиналы (Ом, кОм, мкФ и т.д.) - признак подбора, а не производителя
            has_nominal_in_note = bool(current_note and re.search(r'\d+\s*(?:Ом|ком|кОм|мком|мкОм|мкФ|пФ|нФ|мГн|мкГн)', current_note, re.IGNORECASE))
            
            # Проверяем наличие маркера производителя
            has_manufacturer_marker = 'ф.' in current_note or 'p/n' in current_note.lower()
            
            # Если в note есть список артикулов (запятые + длина > 30) или номиналы, это подборы - очищаем
            # НО только если нет явного маркера производителя!
            looks_like_podbor_list = ((has_commas_in_note and len(current_note) > 30) or has_nominal_in_note) and not has_manufacturer_marker
            
            if has_tu_in_note:
                # В note есть ТУ-код - сохраняем его
                pass
            elif has_manufacturer_marker:
                # В note есть производитель - сохраняем его
                pass
            elif is_replacement and current_note and not has_nominal_in_note:
                # Это замена и в note есть производитель (НЕ номинал!) - сохраняем
                pass
            elif is_short_note and not has_commas_in_note and not has_nominal_in_note:
                # В note производитель (короткая строка без разделителей и номиналов) - сохраняем
                pass
            elif looks_like_podbor_list:
                # В note список подборов или номиналы - очищаем!
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
        
        # ОТЛАДКА
        
        # DEBUG для C2*
        # if 'C21' in ref or 'C22' in ref:
        #     print(f"  [DEBUG-C] {ref}: is_replacement={is_replacement}, note_lower[:50]='{note_lower[:50]}'")
        
        if is_replacement:
            # Обрабатываем ЗАМЕНЫ (альтернативные компоненты)
            # ВАЖНО: Сначала ищем подборы номиналов ДО текста замены
            # Пример: "845 Ом, допускается замена перемычкой"
            # Результат: [("845 Ом", подбор), ("Перемычка", замена)]
            
            podbor_items = _extract_podbors_before_replacement(note, row)
            
            
            
            replacement_items = _extract_replacements(note, row)
            
            
            # Добавляем подборы с тегом (подбор)
            if podbor_items:
                # print(f"  [ПОДБОРЫ] {ref}: найдено {len(podbor_items)} номиналов (подбор)")
                for item in podbor_items:
                    # print(f"    -> {item}")
                    new_row = row.to_dict().copy()
                    new_row['description'] = item
                    new_row['reference'] = f"{ref} (п/б)"
                    
                    # Копируем ТУ/производителя
                    _copy_tu_and_manufacturer(new_row, row)
                    
                    # Помечаем источник
                    if 'source_file' in new_row and pd.notna(new_row['source_file']):
                        source = str(new_row['source_file'])
                        source = re.sub(r'\s*,?\s*\((замена|п/б|подбор).*?\)', '', source).strip()
                        new_row['source_file'] = f"{source} (п/б {ref})"
                    
                    new_rows.append(new_row)
            
            # Теперь обрабатываем замены
            extracted_items = replacement_items
            tag = '(замена)'
        else:
            # Обрабатываем ПОДБОРЫ (номиналы)
            extracted_items = _extract_podbors(note, row)
            tag = '(подбор)'
        
        # Добавляем найденные элементы
        if extracted_items:
            # print(f"  [ПОДБОРЫ] {ref}: найдено {len(extracted_items)} элементов {tag}")
            for item in extracted_items:
                # Распаковываем: для замен это (артикул, производитель), для подборов просто строка
                if is_replacement and isinstance(item, tuple):
                    item_desc, item_manufacturer = item
                else:
                    item_desc = item if isinstance(item, str) else str(item)
                    item_manufacturer = ""
                
                # print(f"    -> {item_desc}")
                new_row = row.to_dict().copy()
                
                # ВАЖНО: Для ПОДБОРОВ не нужно удалять производителя!
                # Подборы - это полные описания резисторов/конденсаторов с номиналами
                # Пример: "Резистор  Р1-12-0,125-121 кОм±1%-М" - оставляем как есть
                # 
                # Удаление производителя нужно ТОЛЬКО для замен (артикулов типа "PAT-0+ ф. Mini-Circuits")
                if is_replacement:
                    # Удаляем производителя из description замены
                    # Стратегия: оставляем только артикул (все до первых двух+ пробелов или до "ф.")
                    # Примеры:
                    #   "PAT-0+           ф. Mini-Circuits" → "PAT-0+"
                    #   "PAT-10+. Mini-Circuits" → "PAT-10+"
                    
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
                else:
                    # Для ПОДБОРОВ: копируем описание из оригинала и заменяем артикул
                    # Это сохраняет префикс типа "Аттенюатор оптический" или "Резистор"
                    original_desc = str(row.get('description', '')).strip()
                    item_desc_clean = item_desc.strip()
                    
                    # Если item_desc выглядит как полное описание (содержит пробелы, префикс компонента),
                    # используем его как есть (это случай для резисторов/конденсаторов/аттенюаторов с номиналами)
                    if ' ' in item_desc_clean and any(prefix in item_desc_clean.lower() for prefix in ['резистор', 'конденсатор', 'дроссель', 'аттенюатор', 'адаптер', 'коммутатор']):
                        new_row['description'] = item_desc_clean
                    else:
                        # Иначе это просто артикул (например, "2100-L-3-2-1-1-1-2")
                        # Заменяем артикул в оригинальном описании, сохраняя префикс
                        if original_desc and item_desc_clean:
                            new_desc = _replace_artikul_in_description(original_desc, item_desc_clean)
                            if new_desc and new_desc != original_desc:
                                new_row['description'] = new_desc
                            else:
                                # Если замена не удалась, просто добавляем новый артикул к префиксу
                                # Извлекаем префикс из оригинала (первое слово или два)
                                words = original_desc.split()
                                if len(words) >= 2 and not any(c in words[0] for c in ['-', '/']):
                                    # Первые 1-2 слова - это префикс (например, "Аттенюатор оптический")
                                    prefix = ' '.join(words[:2]) if len(words) > 1 else words[0]
                                    new_row['description'] = f"{prefix} {item_desc_clean}"
                                else:
                                    new_row['description'] = item_desc_clean
                        else:
                            new_row['description'] = item_desc_clean
                # Устанавливаем reference с правильным тегом: (зам) для замен, (п/б) для подборов
                ref_tag = '(зам)' if is_replacement else '(п/б)'
                new_row['reference'] = f"{ref} {ref_tag}"
                
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
                        
                        # ВАЖНО: Если в note несколько ТУ через |, берём ПОСЛЕДНИЙ (правильный)
                        # Пример: "ОЖ0.467.093ТУ | АЛЯР.434110.005ТУ" → берём "АЛЯР.434110.005ТУ"
                        if '|' in note_val:
                            note_parts = note_val.split('|')
                            # Ищем последнюю часть с ТУ
                            for part in reversed(note_parts):
                                part = part.strip()
                                if 'ту' in part.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', part):
                                    new_row['note'] = part
                                    break
                        elif 'ту' in note_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', note_val):
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


def _extract_podbors_before_replacement(note: str, row: dict) -> list:
    """
    Извлекает подборы номиналов ДО текста замены
    
    Пример: "845 Ом, допускается замена перемычкой"
    Результат: ["Р1-12-0,1-845 Ом ±2%-Т"]
    
    Args:
        note: Текст примечания
        row: Строка данных компонента
        
    Returns:
        Список полных описаний с новыми номиналами
    """
    podbors = []
    
    # Ищем текст ДО слова "замена"
    # Паттерн: все что до "замена", "допуск", "допускается"
    before_replacement_pattern = r'^(.+?)(?:,?\s*допуск|,?\s*замена)'
    match = re.search(before_replacement_pattern, note, re.IGNORECASE)
    
    if not match:
        return podbors
    
    text_before_replacement = match.group(1).strip()
    
    # Если это пустая строка или слишком короткая - пропускаем
    if not text_before_replacement or len(text_before_replacement) < 3:
        return podbors
    
    # Используем основную функцию извлечения подборов для этого текста
    # Передаем только часть примечания ДО замены
    podbors = _extract_podbors(text_before_replacement, row)
    
    return podbors


def _copy_tu_and_manufacturer(new_row: dict, original_row: dict):
    """
    Копирует ТУ и производителя из оригинальной строки в новую
    
    Args:
        new_row: Новая строка (для подбора/замены)
        original_row: Оригинальная строка
    """
    # Очищаем все поля с примечаниями
    new_row['note'] = ''
    new_row['original_note'] = ''
    if 'Примечание' in new_row:
        new_row['Примечание'] = ''
    if 'ТУ' in new_row:
        new_row['ТУ'] = ''
    if 'tu' in new_row:
        new_row['tu'] = ''
    
    # Извлекаем производителя из description оригинала
    orig_desc = str(original_row.get('description', '')).strip() if pd.notna(original_row.get('description')) else ''
    manufacturer_from_desc = ''
    if orig_desc:
        mfr_match = re.search(r'ф\.\s*([A-Za-zА-ЯЁа-яё0-9\s\-]+)', orig_desc)
        if mfr_match:
            manufacturer_from_desc = mfr_match.group(1).strip()
    
    # Копируем ТУ/производителя из оригинала
    if 'tu' in original_row.index and pd.notna(original_row.get('tu')):
        tu_val = str(original_row.get('tu')).strip()
        if 'ту' in tu_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', tu_val):
            new_row['tu'] = tu_val
    elif 'ТУ' in original_row.index and pd.notna(original_row.get('ТУ')):
        tu_val = str(original_row.get('ТУ')).strip()
        if 'ту' in tu_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', tu_val):
            new_row['ТУ'] = tu_val
    elif 'note' in original_row.index and pd.notna(original_row.get('note')):
        note_val = str(original_row.get('note')).strip()
        
        # ВАЖНО: Если в note несколько ТУ через |, берём ПОСЛЕДНИЙ (правильный)
        # Пример: "ОЖ0.467.093ТУ | АЛЯР.434110.005ТУ" → берём "АЛЯР.434110.005ТУ"
        if '|' in note_val:
            note_parts = note_val.split('|')
            # Ищем последнюю часть с ТУ
            for part in reversed(note_parts):
                part = part.strip()
                if 'ту' in part.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', part):
                    new_row['note'] = part
                    break
        elif 'ту' in note_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', note_val):
            new_row['note'] = note_val
        elif manufacturer_from_desc:
            new_row['note'] = manufacturer_from_desc
        elif len(note_val) > 0 and len(note_val) < 100 and not (',' in note_val or ';' in note_val):
            new_row['note'] = note_val
    elif 'original_note' in original_row.index and pd.notna(original_row.get('original_note')):
        note_val = str(original_row.get('original_note')).strip()
        if 'ту' in note_val.lower() or re.search(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}', note_val):
            new_row['note'] = note_val
        elif manufacturer_from_desc:
            new_row['note'] = manufacturer_from_desc
    elif manufacturer_from_desc:
        new_row['note'] = manufacturer_from_desc


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
    # Варианты: "замена на", "допускается замена", "замена перемычкой", "Доп. замена:", "Допуск. замена:"
    pattern = r'(?:замена\s+на|допуск\.\s*замена\s*:?|допускается\s+замена\s+(?:на\s+)?|замена\s+|доп\.\s*замена:)\s*(.+?)(?:\.\s*$|$)'
    match = re.search(pattern, note, re.IGNORECASE | re.DOTALL)
    
    if not match:
        return replacements
    
    replacements_text = match.group(1).strip()
    main_desc = str(row.get('description', '')).strip()
    
    # Специальная обработка для перемычки (простой проводник)
    # "перемычкой" → "Перемычка"
    if re.match(r'^перемычк[ао][йюми]?\s*$', replacements_text, re.IGNORECASE):
        replacements.append(("Перемычка", ""))
        return replacements
    
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
    
    # КРИТИЧНО: Убираем ТУ-код из НАЧАЛА примечания!
    # Пример: "АЛЯР.434110.005ТУ 121 кОм, 162 кОм" → "121 кОм, 162 кОм"
    # Это нужно сделать ДО извлечения номиналов, чтобы ТУ не мешал
    note_cleaned = re.sub(r'^[А-ЯЁ]{4}\.\d{6}\.\d{3}ТУ\s*', '', note_cleaned, flags=re.IGNORECASE)
    
    # СНАЧАЛА извлекаем все номиналы из примечания
    # Это важно, чтобы запятая в "6,8Ом" не воспринималась как разделитель
    # ВАЖНО: Также захватываем допуск и модель после номинала, если они есть
    extracted_nominals = []
    for pattern in nominal_patterns:
        matches = re.finditer(pattern, note_cleaned, re.IGNORECASE)
        for match in matches:
            value = match.group(1).replace(',', '.')
            unit = match.group(2)
            unit_normalized = _normalize_unit(unit)
            
            # Базовый номинал
            found_nominal = f"{value} {unit_normalized}"
            
            # ВРЕМЕННО ОТКЛЮЧЕНО: Захват допуска из примечания
            # Пытаемся захватить допуск и модель ПОСЛЕ номинала
            # Паттерн: ± X% - M/Т/А и т.д.
            # text_after_nominal = note_cleaned[match.end():]
            # tolerance_pattern = r'^\s*([±]\s*\d+(?:[,.]\d+)?%?)(?:\s*[-–—]\s*([А-ЯЁA-Z]))?'
            # tolerance_match = re.match(tolerance_pattern, text_after_nominal, re.IGNORECASE)
            # 
            # if tolerance_match:
            #     # Есть допуск (и возможно модель)
            #     tolerance_part = tolerance_match.group(1).strip()  # ± X%
            #     model_part = tolerance_match.group(2)  # M, Т, А
            #     
            #     # Нормализуем знак ±
            #     tolerance_part = tolerance_part.replace('±', '±')
            #     
            #     # Формируем полный номинал с допуском
            #     found_nominal = f"{value} {unit_normalized} {tolerance_part}"
            #     
            #     # Добавляем модель если есть
            #     if model_part:
            #         found_nominal = f"{found_nominal} - {model_part}"
            
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
        
        # КРИТИЧНО: Пропускаем ТУ-коды! 
        # ТУ-коды НЕ являются подборами, это технические спецификации
        # Паттерн: XXXX.NNNNNN.NNNТУ (4 буквы + точка + 6 цифр + точка + 3 цифры + ТУ)
        # Примеры: ИУЯР.436610.015ТУ, БКЯЮ.436630.001ТУ
        if re.match(r'[А-ЯЁ]{4}\.\d{6}\.\d{3}ТУ', part, re.IGNORECASE):
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
        "Аттенюатор оптический 2100-L-3-2-1-5-1-2" + "2100-L-3-2-1-1-1-2" → "Аттенюатор оптический 2100-L-3-2-1-1-1-2"
    
    Args:
        description: Оригинальное описание компонента
        new_artikul: Новый артикул из подбора
        
    Returns:
        Описание с замененным артикулом
    """
    # Удаляем точку в конце артикула (если есть)
    new_artikul = new_artikul.rstrip('.')
    
    # БЫСТРЫЙ ПУТЬ для артикулов с множеством дефисов (типа "2100-L-3-2-1-5-1-2"):
    # Используем простой поиск последнего "токена" из цифр/букв/дефисов
    # Это БЕЗОПАСНО и быстро, без риска backtracking
    if new_artikul.count('-') > 3 or description.count('-') > 3:
        # Разбиваем описание на слова
        words = description.split()
        # Ищем слово, которое выглядит как артикул (содержит дефисы и цифры)
        for i in range(len(words)):
            word = words[i].rstrip(',.')
            # Если это артикул (содержит дефисы, цифры и буквы)
            if '-' in word and any(c.isdigit() for c in word) and any(c.isalpha() for c in word):
                # Заменяем это слово на новый артикул
                words[i] = words[i].replace(word, new_artikul)
                return ' '.join(words)
        
        # Если не нашли артикул в словах, возвращаем описание + новый артикул
        # Извлекаем префикс (первые 1-2 слова без дефисов)
        prefix_words = []
        for word in words:
            if '-' not in word and '/' not in word:
                prefix_words.append(word)
                if len(prefix_words) >= 2:
                    break
            else:
                break
        
        if prefix_words:
            return ' '.join(prefix_words) + ' ' + new_artikul
        else:
            return new_artikul
    
    # ОБЫЧНЫЙ ПУТЬ для простых артикулов (без множества дефисов):
    # Используем regex только для коротких/простых паттернов
    
    # Попытка 1: Простой артикул в конце описания (после последнего пробела)
    words = description.split()
    if len(words) > 0:
        last_word = words[-1].rstrip(',.')
        # Если последнее слово похоже на артикул
        if len(last_word) >= 3 and any(c.isdigit() for c in last_word) and any(c.isalpha() for c in last_word):
            words[-1] = words[-1].replace(last_word, new_artikul)
            return ' '.join(words)
    
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
    
    Важно: Если new_nominal содержит допуск/модель (например, "226 кОм ± 1% - M"),
    то заменяется весь остаток строки после номинала, чтобы избежать дублирования.
    """
    # Паттерн для поиска номинала в описании
    # Ищем число + единица измерения (Ом, кОм, пФ, мкФ и т.д.)
    # Паттерн для чисел: \d+(?:[,.]\d+)? - поддерживает "6,8" и "6.8" и "10"
    # Word boundary (\b) для предотвращения ложных срабатываний
    nominal_in_desc_pattern = r'\b(\d+(?:[,.]\d+)?)\s*(МОм|мом|кОм|ком|Ом|ом|мкФ|мкф|нФ|нф|пФ|пф|мГн|мгн|мкГн|мкгн|нГн|нгн|Гн|гн)\b'
    
    # Находим номинал в описании
    match = re.search(nominal_in_desc_pattern, desc, flags=re.IGNORECASE)
    if not match:
        return desc
    
    # Берем часть до номинала
    prefix = desc[:match.start()]
    
    # Проверяем, есть ли в new_nominal допуск или модель (±, %, -)
    # Если есть, то заменяем всё до конца строки
    if any(char in new_nominal for char in ['±', '%', '- M', '- Т', '- А']):
        # new_nominal содержит допуск/модель - заменяем весь остаток
        result = prefix + new_nominal
    else:
        # new_nominal - только номинал, сохраняем остаток оригинального описания
        suffix = desc[match.end():]
        result = prefix + new_nominal + suffix
    
    return result
