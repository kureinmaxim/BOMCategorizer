# -*- coding: utf-8 -*-
"""
Парсеры для различных форматов BOM файлов

Поддерживаемые форматы:
- TXT: текстовые файлы с разделителями
- DOCX: документы Word с таблицами
- Excel: XLSX файлы
"""

import os
import re
from typing import List, Dict, Any, Optional
import pandas as pd

from .utils import LINE_SPLIT_RE, POS_PREFIX_RE

try:
    from docx import Document  # python-docx
except Exception:
    Document = None  # optional; raise if used without installed


def normalize_dashes(text: str) -> str:
    """
    Нормализует различные виды тире и дефисов к обычному дефису
    
    При конвертации .doc → .docx Word может заменять дефисы на типографские тире.
    Это функция приводит все варианты к единому формату для правильного объединения компонентов.
    
    Args:
        text: Исходный текст
        
    Returns:
        Текст с нормализованными дефисами
    """
    if not text:
        return text
    
    # Заменяем все виды тире на обычный дефис
    # U+2013: EN DASH (–)
    # U+2014: EM DASH (—)
    # U+2212: MINUS SIGN (−)
    # U+2010: HYPHEN (‐)
    # U+2011: NON-BREAKING HYPHEN (‑)
    text = text.replace('\u2013', '-')  # EN DASH
    text = text.replace('\u2014', '-')  # EM DASH
    text = text.replace('\u2212', '-')  # MINUS SIGN
    text = text.replace('\u2010', '-')  # HYPHEN
    text = text.replace('\u2011', '-')  # NON-BREAKING HYPHEN
    
    return text


def normalize_cell(s: Any) -> str:
    """Нормализует содержимое ячейки таблицы"""
    text = str(s or "").strip()
    # Нормализуем тире для корректного объединения компонентов
    text = normalize_dashes(text)
    # Удаляем непечатные символы (включая �)
    text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
    return text


def count_from_reference(ref: str) -> int:
    """
    Подсчитывает количество элементов из позиционного обозначения
    
    Examples:
        R1 -> 1
        R1, R2 -> 2
        R1-R6 -> 6
        FU1-FU6 -> 6
        C1, C2, C3-C5 -> 5
    
    Args:
        ref: Позиционное обозначение
        
    Returns:
        Количество элементов
    """
    if not ref or not ref.strip():
        return 1
    
    ref = ref.strip()
    total = 0
    
    # Разделяем по запятым
    parts = [p.strip() for p in ref.split(',')]
    
    for part in parts:
        # Проверяем на диапазон (R1-R6, FU1-FU6, и т.д.)
        range_match = re.match(r'([A-Za-z]+)(\d+)\s*[-–—]\s*([A-Za-z]+)?(\d+)', part)
        if range_match:
            prefix1 = range_match.group(1)
            num1 = int(range_match.group(2))
            prefix2 = range_match.group(3) or prefix1  # Если второй префикс отсутствует, используем первый
            num2 = int(range_match.group(4))
            
            # Подсчитываем диапазон
            if prefix1 == prefix2 and num2 >= num1:
                total += (num2 - num1 + 1)
            else:
                # Если префиксы разные или порядок неправильный, считаем как 2 элемента
                total += 2
        else:
            # Одиночный элемент
            total += 1
    
    return max(total, 1)


def parse_txt_like(path: str) -> pd.DataFrame:
    """
    Парсит текстовый файл с разделителями
    
    Args:
        path: Путь к TXT файлу
        
    Returns:
        DataFrame с колонками: reference, description, qty
    """
    rows: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="cp1251", errors="ignore") as f:
            text = f.read()
    
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = [p.strip() for p in LINE_SPLIT_RE.split(line) if p.strip()]
        if not parts:
            continue
        
        # Heuristic mapping: [pos?, name/desc, qty?]
        pos = parts[0] if POS_PREFIX_RE.match(parts[0]) else None
        qty = None
        
        # Try explicit "Nшт" or "N шт" patterns first
        m = re.search(r"(\d+)\s*(шт\.?|pcs|pieces)", line, flags=re.IGNORECASE)
        if m:
            qty = int(m.group(1))
        else:
            for p in parts[::-1]:
                if re.fullmatch(r"\d+", p):
                    qty = int(p)
                    break
        
        desc = " ".join(parts[1:-1]) if pos and len(parts) >= 2 else (" ".join(parts))
        row = {"reference": pos or "", "description": desc, "qty": qty if qty is not None else 1}
        rows.append(row)
    
    if not rows:
        # fallback: whole text in a single row
        rows = [{"description": text, "qty": 1}]
    
    return pd.DataFrame(rows)


def parse_docx(path: str) -> pd.DataFrame:
    """
    Парсит DOCX файл с таблицами
    
    Args:
        path: Путь к DOCX файлу
        
    Returns:
        DataFrame с колонками: zone, reference, description, qty, note
    """
    if Document is None:
        raise SystemExit("python-docx is required to parse DOCX. Install with pip install python-docx")
    
    doc = Document(path)
    extracted: List[Dict[str, Any]] = []

    def guess_header_index(table) -> int:
        """Определяет индекс строки-заголовка в таблице"""
        max_scan = min(5, len(table.rows))
        header_keywords = ["наимен", "обознач", "кол.", "кол ", "кол", "примеч"]
        for i in range(max_scan):
            row_texts = [normalize_cell(c.text).lower() for c in table.rows[i].cells]
            hits = sum(any(hk in t for hk in header_keywords) for t in row_texts)
            if hits >= 2:
                return i
        return 0

    # Parse tables with header detection
    for table in doc.tables:
        if not table.rows:
            continue
        
        header_idx = guess_header_index(table)
        header_cells = [normalize_cell(c.text).strip() for c in table.rows[header_idx].cells]
        header_norm = [h.lower() for h in header_cells]

        # Find column indices by common names
        def find_col_idx(candidates: List[str]) -> Optional[int]:
            for i, h in enumerate(header_norm):
                for cand in candidates:
                    if cand in h:
                        return i
            return None

        idx_zone = find_col_idx(["зона"])  # optional
        idx_ref = find_col_idx(["поз", "обозн"])  # позиционное обозначение
        idx_name = find_col_idx(["наимен"])  # наименование
        idx_qty = find_col_idx(["кол.", "кол ", "кол", "количество"])  # количество
        idx_note = find_col_idx(["примеч"])  # опционально

        # Переменные для хранения текущего ТУ и типа компонента из заголовка группы
        current_group_tu = ""
        current_group_type = ""

        for tr in table.rows[header_idx + 1:]:
            vals = [normalize_cell(c.text) for c in tr.cells]
            if not any(v.strip() for v in vals):
                continue
            
            zone = vals[idx_zone] if idx_zone is not None and idx_zone < len(vals) else ""
            ref = vals[idx_ref] if idx_ref is not None and idx_ref < len(vals) else ""
            name = vals[idx_name] if idx_name is not None and idx_name < len(vals) else ""
            qty_raw = vals[idx_qty] if idx_qty is not None and idx_qty < len(vals) else ""
            note = vals[idx_note] if idx_note is not None and idx_note < len(vals) else ""
            original_note = note  # Сохранить оригинальное примечание для извлечения подборов
            
            # Проверить, является ли это строкой-заголовком группы
            section_headers = [
                'конденсаторы', 'резисторы', 'микросхемы', 'дроссели', 'индуктивности',
                'разъемы', 'диоды', 'транзисторы', 'кабели', 'модули',
                'набор резисторов', 'набор конденсаторов', 'набор микросхем',
                'трансформаторы', 'датчики', 'реле', 'предохранители', 
                'оптопары', 'оптроны', 'светодиоды', 'стабилитроны',
                'вариаторы', 'переключатели', 'кнопки', 'тумблеры',
                'фильтры', 'антенны', 'радиаторы', 'крепеж',
                'провода', 'жгуты', 'шлейфы', 'платы',
                'корпуса', 'панели', 'винты', 'гайки',
                'изделия', 'детали', 'прочие элементы'
            ]
            name_lower = name.strip().lower()
            
            is_group_header = False
            
            # Проверка группового заголовка: должно быть БЕЗ ref и qty И начинаться с типа компонента
            if not ref.strip() and not qty_raw.strip():
                # Проверяем только начало строки с типом компонента (не ТУ-коды!)
                if any(name_lower.startswith(section) for section in section_headers):
                    is_group_header = True
                # ИЛИ строка содержит ТОЛЬКО обозначение типа (К10-, К53-, Р1-, и т.д.) + ТУ-код
                # Паттерн: буквы+цифры (тип) + пробелы + ТУ-код, БЕЗ детального описания
                elif re.match(r'^[А-ЯЁ]+[\d\-]+\s+[А-ЯЁ]{2,}[\.\d]+\s*ТУ\s*$', name.strip(), re.IGNORECASE):
                    is_group_header = True
                # ИЛИ строка содержит ТОЛЬКО ТУ-код без детального наименования (короткая строка)
                elif len(name.strip()) < 30:
                    has_tu_code = re.search(r'([А-ЯЁ]{2,}[\.\d]+ТУ)', name) or re.search(r'ТУ\s+[\d\-]+', name)
                    if has_tu_code:
                        is_group_header = True
            
            if is_group_header:
                # Извлекаем ТУ
                tu_pattern1 = r'([А-ЯЁ]{2,}\.\d+[\d\.\-]*\s*ТУ)'
                tu_match1 = re.search(tu_pattern1, name)
                if tu_match1:
                    current_group_tu = tu_match1.group(1)
                else:
                    tu_pattern2 = r'([А-ЯЁ]{2,}[\d\.]+\s*ТУ)'
                    tu_match2 = re.search(tu_pattern2, name)
                    if tu_match2:
                        current_group_tu = tu_match2.group(1)
                    else:
                        tu_pattern3 = r'ТУ\s+([\d\-]+)'
                        tu_match3 = re.search(tu_pattern3, name)
                        if tu_match3:
                            current_group_tu = 'ТУ ' + tu_match3.group(1)
                        else:
                            current_group_tu = ""
                
                # Извлекаем тип компонента
                type_text = name
                if current_group_tu:
                    type_text = type_text.replace(current_group_tu, '')
                type_text = re.sub(r'\s+[А-ЯЁ]+\d+[\dА-ЯЁ\-]*', '', type_text)
                type_text = re.sub(r'\s+[А-ЯЁ]+\.\d+[\d\.]*', '', type_text)
                current_group_type = type_text.strip()
                
                continue  # Пропускаем строку-заголовок
            
            # ===================================================================
            # ОБЪЕДИНЕНИЕ МНОГОСТРОЧНЫХ ПРИМЕЧАНИЙ
            # Если строка БЕЗ reference, БЕЗ name, НО С note - это продолжение
            # примечания для предыдущего компонента
            # ===================================================================
            if not ref.strip() and not name.strip() and note.strip() and extracted:
                # Это продолжение примечания для последнего компонента
                last_item = extracted[-1]
                current_note = last_item.get('original_note', '')
                if current_note:
                    # Объединяем через пробел (запятая уже есть в конце предыдущей части)
                    last_item['original_note'] = current_note.strip() + ' ' + note.strip()
                    last_item['note'] = last_item['original_note']  # Обновляем note тоже
                else:
                    last_item['original_note'] = note.strip()
                    last_item['note'] = note.strip()
                continue  # Пропускаем эту строку, т.к. мы уже добавили примечание

            # If header wasn't detected, try fallback mapping
            if not any([ref, name, qty_raw]) and len(vals) >= 2:
                name = " ".join(vals[:-1])
                qty_raw = vals[-1]

            # parse qty
            qty = None
            m = re.search(r"(\d+)", str(qty_raw))
            if m:
                try:
                    qty = int(m.group(1))
                except Exception:
                    qty = 1

            # Проверить, есть ли в наименовании информация о производителе (формат "ф. Производитель")
            manufacturer_in_name = ""
            if name:
                # Ищем паттерн "ф. Производитель" в конце или середине строки
                mfr_pattern = r'\s+ф\.\s*([A-Za-z0-9\s\-]+)'
                mfr_match = re.search(mfr_pattern, name)
                if mfr_match:
                    manufacturer_in_name = mfr_match.group(1).strip()
                    # Удаляем информацию о производителе из наименования
                    name = re.sub(mfr_pattern, '', name).strip()
            
            # Добавить ТОЛЬКО ТУ из заголовка группы в note (НЕ тип компонента!)
            # Тип компонента из заголовка может быть неточным и перевесить правильную классификацию
            if current_group_tu and manufacturer_in_name:
                # Есть и ТУ из заголовка, и производитель из наименования
                note = current_group_tu + ' | ' + manufacturer_in_name
            elif current_group_tu:
                # Только ТУ из заголовка
                note = current_group_tu
            elif manufacturer_in_name:
                # Только производитель из наименования
                note = manufacturer_in_name

            # Не добавлять строку без данных
            if not ref.strip() and not name.strip():
                continue
            
            # Фильтровать служебные записи (Изм., Лист регистрации, и т.д.)
            name_check = name.lower().strip()
            service_keywords = [
                'изм.', 'изме-ненных', 'заме-ненных', 'аннули-рован', 'всего листов', 
                'номер докум', 'входя-щий', 'сопрово-дитель', 'подп.',
                'лист регистрации', 'регистрации изменений'
            ]
            if any(kw in name_check for kw in service_keywords):
                continue
            
            # Обработать строки "ф. Производитель" (без reference)
            # Это строка с производителем для ПРЕДЫДУЩЕГО элемента
            if not ref.strip() and name.strip().startswith('ф.'):
                if extracted:
                    manufacturer_text = name.strip()
                    # Извлечь производителя (после "ф.")
                    mfr_match = re.search(r'ф\.\s*(.+)', manufacturer_text)
                    if mfr_match:
                        manufacturer = mfr_match.group(1).strip()
                        # Добавить производителя к note последнего элемента
                        # ИСПРАВЛЕНО: Порядок изменён на "ТУ | manufacturer" для правильной обработки
                        if extracted[-1]['note']:
                            # Если note уже содержит ТУ-код, добавляем производителя ПОСЛЕ разделителя
                            extracted[-1]['note'] = extracted[-1]['note'] + ' | ' + manufacturer
                        else:
                            # Если note пустой, добавляем только производителя
                            extracted[-1]['note'] = manufacturer
                continue
            
            # Убираем запятую в конце названия (если есть)
            name = name.rstrip(',').strip()

            # Если количество не указано явно, пытаемся посчитать из reference (например, FU1-FU6 = 6)
            if qty is None or qty == 0:
                qty = count_from_reference(ref)
            
            # Определить нужно ли использовать group_type для этого элемента
            # Сбрасываем group_type если элемент явно не принадлежит к текущей группе
            use_group_type = current_group_type
            if ref.strip():
                # Проверяем префикс позиционного обозначения
                ref_prefix = re.sub(r'\d.*$', '', ref.split()[0].upper()) if ref else ""
                
                # Если группа "Резисторы", но префикс НЕ R - сбрасываем
                if current_group_type and 'резистор' in current_group_type.lower() and not ref_prefix.startswith('R'):
                    use_group_type = ""
                # Если группа "Конденсаторы", но префикс НЕ C - сбрасываем
                elif current_group_type and 'конденсатор' in current_group_type.lower() and not ref_prefix.startswith('C'):
                    use_group_type = ""
                # Если группа "Микросхемы", но префикс НЕ DA/DD/U - сбрасываем
                elif current_group_type and 'микросхем' in current_group_type.lower() and not ref_prefix.startswith(('DA', 'DD', 'U', 'IC')):
                    use_group_type = ""
                # Если группа "Индуктивности", но префикс НЕ L - сбрасываем
                elif current_group_type and ('дроссел' in current_group_type.lower() or 'индуктивност' in current_group_type.lower()) and not ref_prefix.startswith('L'):
                    use_group_type = ""
                # Если группа "Разъемы", но префикс НЕ X/XS/J/P - сбрасываем
                elif current_group_type and 'разъем' in current_group_type.lower() and not ref_prefix.startswith(('X', 'J', 'P')):
                    use_group_type = ""

            row = {
                "zone": zone,
                "reference": ref,
                "description": name if name else note,
                "qty": qty,
                "note": note,  # ТУ и производитель, НЕ тип компонента
                "group_type": use_group_type,  # Тип компонента для классификации (может быть сброшен)
                "original_note": original_note,  # Оригинальное примечание для подборов
            }
            extracted.append(row)

    # Additionally parse free text paragraphs (fallback)
    for p in doc.paragraphs:
        t = normalize_cell(p.text)
        if not t:
            continue
        
        # Фильтровать служебные записи из параграфов
        t_check = t.lower().strip()
        service_keywords = [
            'изм.', 'изме-ненных', 'заме-ненных', 'аннули-рован', 'всего листов', 
            'номер докум', 'входя-щий', 'сопрово-дитель', 'подп.',
            'лист регистрации', 'регистрации изменений'
        ]
        if any(kw in t_check for kw in service_keywords):
            continue
        
        parts = [s.strip() for s in LINE_SPLIT_RE.split(t) if s.strip()]
        if parts:
            pos = parts[0] if POS_PREFIX_RE.match(parts[0]) else ""
            m = re.search(r"(\d+)\s*(шт\.?|pcs|pieces)?", t, flags=re.IGNORECASE)
            qty = int(m.group(1)) if m else 1
            desc = " ".join(parts[1:]) if pos else " ".join(parts)
            extracted.append({"reference": pos, "description": desc, "qty": qty})

    if not extracted:
        extracted = [{"description": " ".join(normalize_cell(p.text) for p in doc.paragraphs), "qty": 1}]
    
    return pd.DataFrame(extracted)
