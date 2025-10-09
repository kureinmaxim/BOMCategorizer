# -*- coding: utf-8 -*-
"""
Форматирование и очистка данных компонентов

Основные функции:
- clean_component_name: очистка названий от префиксов и нормализация единиц
- extract_nominal_value: извлечение номинала для сортировки
- extract_tu_code: извлечение технических условий (ТУ)
- parse_smd_code: парсинг SMD кодов резисторов и конденсаторов
"""

import re
import math
from typing import Optional, Tuple, Any


def clean_component_name(original_text: str, note: str = "") -> str:
    """
    Очищает наименование компонента от префиксов типа "РЕЗИСТОР", "КОНДЕНСАТОР" и т.д.
    Нормализует единицы измерения (ОМ -> Ом, КОМ -> кОм и т.д.)
    Убирает $ и $$ в конце
    
    Args:
        original_text: Исходный текст наименования
        note: Примечание (может содержать тип компонента из группового заголовка)
        
    Returns:
        Очищенное наименование
    """
    if not original_text:
        return ""
    
    text = str(original_text).strip()
    
    # Нормализуем множественные пробелы (заменяем несколько пробелов на один)
    text = re.sub(r'\s+', ' ', text)
    
    # Component type prefixes (sorted by length, longest first)
    component_types = [
        'ЧИП КАТУШКИ ИНДУКТИВНОСТЬ',
        'ЧИП КОНДЕНСАТОР КЕРАМИЧЕСКИЙ',
        'ЧИП КАТУШКА ИНДУКТИВНОСТЬ',
        'МАТРИЦА ТРАНЗИСТОРНАЯ',
        'ТРАНЗИСТОРНАЯ МАТРИЦА',
        'ИНДИКАТОР ЕДИНИЧНЫЙ',
        'НАБОР РЕЗИСТОРОВ',
        'НАБОР КОНДЕНСАТОРОВ',
        'НАБОР МИКРОСХЕМ',
        'ПЛАТА ИНСТРУМЕНТАЛЬНАЯ',
        'ОПТИЧЕСКИЙ МОДУЛЬ',
        'МОДУЛЬ ПИТАНИЯ',
        'МИКРОСХЕМА',
        'РЕЗИСТОР',
        'КОНДЕНСАТОР',
        'ИНДУКТИВНОСТЬ',
        'ИНДИКАТОР',
        'ДРОССЕЛЬ',
        'ДИОД',
        'СТАБИЛИТРОН',
        'ТРАНЗИСТОР',
        'ГЕНЕРАТОР',
        'ОПТРОН',
        'РАЗЪЕМ',
        'РАЗЪЁМ',
        'ВИЛКА',
        'КАБЕЛЬ',
        'ПРЕДОХРАНИТЕЛЬ',
    ]
    
    # Check if note contains a component type (from group header)
    note_lower = note.lower() if note else ""
    extracted_type = ""
    for comp_type in component_types:
        if comp_type.lower() in note_lower:
            extracted_type = comp_type
            break
    
    # Remove component type prefix if present
    text_upper = text.upper()
    removed_prefix = None
    
    for comp_type in component_types:
        if text_upper.startswith(comp_type):
            # Исключение: не удаляем "ВИЛКА" для компонентов Harting
            if comp_type == 'ВИЛКА' and ('harting' in text.lower() or 'sek' in text.lower()):
                continue
            text = text[len(comp_type):].strip()
            removed_prefix = comp_type
            break
    
    # If a prefix was removed but wasn't "extracted" from note, it means it was part of the name
    # In that case, we've already removed it.
    # If it was extracted from note (group header), it should already be removed from text.
    
    # Обработка паттерна "артикул [код]" - удаляем слово "артикул", оставляя производителя и код
    # Пример: "Analog Device, артикул EVAL-ADF4351EB1Z" → "Analog Device EVAL-ADF4351EB1Z"
    # Производитель нужен для извлечения в колонку ТУ функцией extract_tu_code
    if re.search(r'артикул', text, re.IGNORECASE):
        # Удаляем слова "артикул", ":", оставляя производителя и код
        text = re.sub(r'[,\s]*артикул[:\s]*', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()  # Нормализуем пробелы
    
    # Normalize units
    text = re.sub(r'(\d)\s*ОМ\b', r'\1 Ом', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*КОМ\b', r'\1 кОм', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*МОМ\b', r'\1 МОм', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*ПФ\b', r'\1 пФ', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*НФ\b', r'\1 нФ', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*МКФ\b', r'\1 мкФ', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*МФ\b', r'\1 мФ', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*ГН\b', r'\1 Гн', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*МГН\b', r'\1 мГн', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s*МКГН\b', r'\1 мкГн', text, flags=re.IGNORECASE)
    
    # Normalize manufacturer prefixes (e.g., ", ф.Qualwave" to " ф.Qualwave")
    text = re.sub(r',\s*ф\.', ' ф.', text)
    
    # Убираем ВСЕ символы $ из текста (в начале, середине, конце)
    text = text.replace('$', '').strip()
    
    return text


def extract_nominal_value(text: str, category: str) -> Optional[float]:
    """
    Извлекает номинальное значение компонента для сортировки
    
    Args:
        text: Текст с номиналом (описание компонента)
        category: Категория компонента ('resistors', 'capacitors', 'inductors')
        
    Returns:
        Числовое значение в базовых единицах (Ом, Ф, Гн) или None
    """
    if not text:
        return None
    
    text = str(text).lower()
    
    # Try SMD codes first (for imported components)
    if category == "resistors":
        smd = _parse_smd_resistor(text)
        if smd is not None:
            return smd
    elif category == "capacitors":
        smd = _parse_smd_capacitor(text)
        if smd is not None:
            return smd
    elif category == "inductors":
        smd = _parse_smd_inductor(text)
        if smd is not None:
            return smd
    
    # Resistors: Ом, кОм, МОм
    if category == "resistors":
        patterns = [
            (r'[-\s](\d+(?:[.,]\d+)?)\s*мом', 1e6),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*mω', 1e6),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*ком', 1e3),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*kω', 1e3),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*ом', 1.0),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*ω', 1.0),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*ohm', 1.0),
        ]
    # Capacitors: пФ, нФ, мкФ, мФ
    elif category == "capacitors":
        patterns = [
            (r'[-\s](\d+(?:[.,]\d+)?)\s*мф', 1e-3),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*mf', 1e-3),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*мкф', 1e-6),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*[uμ]f', 1e-6),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*нф', 1e-9),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*nf', 1e-9),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*пф', 1e-12),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*pf', 1e-12),
        ]
    # Inductors: Гн, мГн, мкГн, нГн
    elif category == "inductors":
        patterns = [
            (r'[-\s](\d+(?:[.,]\d+)?)\s*гн', 1.0),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*h\b', 1.0),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*мгн', 1e-3),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*mh', 1e-3),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*мкгн', 1e-6),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*[uμ]h', 1e-6),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*нгн', 1e-9),
            (r'[-\s](\d+(?:[.,]\d+)?)\s*nh', 1e-9),
        ]
    else:
        return None
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            value_str = match.group(1).replace(',', '.')
            try:
                value = float(value_str) * multiplier
                return value
            except ValueError:
                continue
    
    return None


def extract_tu_code(text: str) -> Tuple[str, str]:
    """
    Извлекает код ТУ или производителя из текста
    
    Args:
        text: Исходный текст
        
    Returns:
        Кортеж (очищенный текст без ТУ/производителя, извлеченный ТУ код или производитель)
    """
    if not text:
        return "", ""
    
    text_str = str(text).strip()
    
    # Паттерны для ТУ (Technical Specifications codes)
    tu_patterns = [
        # Буквенно-цифровые коды с точками (начинающиеся с букв или цифр)
        (r'([А-ЯЁа-яё]{2,}\.\d+[\d\.\-]*\s*ТУ)', re.IGNORECASE),        # АЛЯР.434110.005ТУ, аА0.339.189ТУ
        (r'([А-ЯЁа-яё]{1,2}\d+\.\d+[\d\.\-]*\s*ТУ)', re.IGNORECASE),    # И93.456.000ТУ, И93.456.001 ТУ
        (r'(\d+[А-ЯЁа-яё]+\d+\.\d+[\d\.\-]*\s*ТУ)', re.IGNORECASE),     # 1Х3.438.000ТУ, 2А5.123.456ТУ
        (r'([А-ЯЁа-яё]{2,}[\d\.\-]+\s*ТУ)', re.IGNORECASE),             # ШКАБ434110002ТУ, АЕЯР431200424-07ТУ
        (r'(\d+[А-ЯЁа-яё]+[\d\.\-]+\s*ТУ)', re.IGNORECASE),             # Цифра+буквы+цифры без первой точки
        # ТУ в начале строки
        (r'ТУ\s+([\d\-]+)', 0),                                          # ТУ 6329-019-07614320-99
    ]
    
    tu_code = ""
    clean_text = text_str
    
    # Сначала ищем ТУ коды (приоритет для отечественных компонентов)
    for pattern, flags in tu_patterns:
        match = re.search(pattern, text_str, flags) if flags else re.search(pattern, text_str)
        if match:
            if pattern.startswith('ТУ'):
                tu_code = 'ТУ ' + match.group(1)
            else:
                tu_code = match.group(1)
            clean_text = re.sub(pattern, '', clean_text, flags=flags) if flags else re.sub(pattern, '', clean_text)
            clean_text = clean_text.strip()
            break
    
    # Если ТУ не найден, ищем производителя
    if not tu_code:
        manufacturer = ""
        
        # Список известных производителей (в порядке от более специфичных к менее)
        # Сначала идут полные названия, потом сокращения (чтобы избежать ложных срабатываний)
        known_manufacturers = [
            'Texas Instruments',
            'MAXIM INTEGRATED',
            'Maxim Integrated',
            'Analog Devices',
            'Analog Device',  # Вариант без 's'
            'MINI-CIRCUITS',
            'Mini-Circuits',
            'ROSENBERGER',
            'Rosenberger',
            'COILCRAFT',
            'Coilcraft',
            'MURATA',
            'Murata',
            'HARTING',
            'Harting',
            'HITTITE',
            'Hittite',
            # Сокращения (добавляем в конец списка, чтобы полные названия имели приоритет)
            'TI',  # Texas Instruments
            'ADI',  # Analog Devices
            'Maxim',
        ]
        
        # Словарь нормализации: сокращение -> полное название
        # Ключи в ВЕРХНЕМ РЕГИСТРЕ для корректного сравнения
        manufacturer_aliases = {
            'TI': 'Texas Instruments',
            'ADI': 'Analog Devices',
            'ANALOG DEVICE': 'Analog Devices',  # Нормализация варианта без 's'
            'MAXIM': 'Maxim Integrated',
            'MAXIM INTEGRATED': 'Maxim Integrated',
        }
        
        # 1. Сначала ищем "ф." + производитель (высокий приоритет)
        # Паттерн для извлечения производителя после "ф." или "ф ."
        # Ищем "ф." или "ф ." и берем все до конца строки или до запятой/точки с запятой
        mfr_pattern = r'\s*ф\s*\.\s*([A-Za-zА-ЯЁа-яё][A-Za-zА-ЯЁа-яё\s\-\.]+?)(?:\s*$|,|;|\s+\d)'
        match = re.search(mfr_pattern, clean_text, re.IGNORECASE)
        
        if match:
            manufacturer = match.group(1).strip()
            # Удаляем "ф." и производителя из текста
            clean_text = re.sub(mfr_pattern, '', clean_text, flags=re.IGNORECASE)
            clean_text = clean_text.strip()
            
            # Нормализуем производителя сразу (преобразуем сокращения в полные названия)
            manufacturer_upper = manufacturer.upper()
            if manufacturer_upper in manufacturer_aliases:
                manufacturer = manufacturer_aliases[manufacturer_upper]
        else:
            # 2. Ищем известного производителя в начале строки (второй приоритет)
            for mfr in known_manufacturers:
                # Проверяем, начинается ли текст с производителя (с учетом регистра)
                if clean_text.upper().startswith(mfr.upper()):
                    manufacturer = mfr
                    # Удаляем производителя из начала текста
                    clean_text = clean_text[len(mfr):].strip()
                    
                    # Нормализуем производителя
                    manufacturer_upper = manufacturer.upper()
                    if manufacturer_upper in manufacturer_aliases:
                        manufacturer = manufacturer_aliases[manufacturer_upper]
                    break
            
            # 3. Если не нашли в начале, ищем производителя в любом месте текста (третий приоритет)
            if not manufacturer:
                text_upper = clean_text.upper()
                for mfr in known_manufacturers:
                    mfr_upper = mfr.upper()
                    
                    # Для коротких сокращений (2-3 символа) проверяем, что это отдельное слово
                    if len(mfr) <= 3:
                        # Используем word boundary (\b) для поиска целого слова
                        pattern = r'\b' + re.escape(mfr) + r'\b'
                        match = re.search(pattern, clean_text, re.IGNORECASE)
                        if match:
                            manufacturer = mfr
                            # Удаляем найденное слово
                            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
                            clean_text = clean_text.strip()
                            break
                    else:
                        # Для длинных названий ищем как подстроку
                        if mfr_upper in text_upper:
                            manufacturer = mfr
                            # Удаляем производителя из текста (case-insensitive)
                            clean_text = re.sub(re.escape(mfr), '', clean_text, flags=re.IGNORECASE)
                            clean_text = clean_text.strip()
                            break
        
        if manufacturer:
            # Нормализуем производителя (преобразуем сокращения в полные названия)
            manufacturer_upper = manufacturer.upper()
            if manufacturer_upper in manufacturer_aliases:
                tu_code = manufacturer_aliases[manufacturer_upper]
            else:
                tu_code = manufacturer
    
    return clean_text, tu_code


def _parse_smd_resistor(text: str) -> Optional[float]:
    """
    Парсит SMD код резистора (3-х или 4-х значный)
    Например: 103 = 10 * 10^3 = 10k = 10000 Ом
    
    ВАЖНО: Не срабатывает для отечественных резисторов типа "P1-12-0,125-681"
    """
    # Пропускаем, если есть явные единицы измерения (значит это не SMD код)
    if re.search(r'(ком|мом|ом|kohm|mohm|ohm)', text, re.IGNORECASE):
        return None
    
    # 3-digit code: XYZ = XY * 10^Z (после пробела или в начале, но не после дефиса/запятой)
    match = re.search(r'(?:^|\s)(\d)(\d)(\d)(?:\s|$)', text)
    if match:
        x, y, z = match.groups()
        try:
            mantissa = int(x + y)
            exponent = int(z)
            return mantissa * (10 ** exponent)
        except Exception:
            pass
    
    # 4-digit code: WXYZ = WXY * 10^Z
    match = re.search(r'(?:^|\s)(\d)(\d)(\d)(\d)(?:\s|$)', text)
    if match:
        w, x, y, z = match.groups()
        try:
            mantissa = int(w + x + y)
            exponent = int(z)
            return mantissa * (10 ** exponent)
        except Exception:
            pass
    
    return None


def _parse_smd_capacitor(text: str) -> Optional[float]:
    """
    Парсит SMD код конденсатора (обычно буквенно-цифровой)
    Например: 106 = 10 * 10^6 пФ = 10 мкФ = 1e-5 Ф
    """
    # Пропускаем, если есть явные единицы измерения
    if re.search(r'(пф|нф|мкф|мф|pf|nf|uf|mf)', text, re.IGNORECASE):
        return None
    
    # Similar to resistor, but in picofarads
    match = re.search(r'(?:^|\s)(\d)(\d)(\d)(?:\s|$)', text)
    if match:
        x, y, z = match.groups()
        try:
            mantissa = int(x + y)
            exponent = int(z)
            pf_value = mantissa * (10 ** exponent)
            return pf_value * 1e-12  # Convert to Farads
        except Exception:
            pass
    
    return None


def _parse_smd_inductor(text: str) -> Optional[float]:
    """
    Парсит SMD код индуктивности
    Обычно в нГн, формат аналогичен резисторам
    """
    # Пропускаем, если есть явные единицы измерения
    if re.search(r'(гн|мгн|мкгн|нгн|h\b|mh|uh|nh)', text, re.IGNORECASE):
        return None
    
    match = re.search(r'(?:^|\s)(\d)(\d)(\d)(?:\s|$)', text)
    if match:
        x, y, z = match.groups()
        try:
            mantissa = int(x + y)
            exponent = int(z)
            nh_value = mantissa * (10 ** exponent)
            return nh_value * 1e-9  # Convert to Henries
        except Exception:
            pass
    
    return None
