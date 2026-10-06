# -*- coding: utf-8 -*-
"""
Утилиты и вспомогательные функции

Содержит:
- Нормализация имен колонок
- Поиск колонок по альтернативным именам
- Проверка наличия ключевых слов
- Регулярные выражения для распознавания номиналов
"""

import re
import math
import unicodedata
from numbers import Real
from typing import List, Optional


QUANTITY_COLUMNS = ['шт.', 'шт', 'qty', 'quantity', 'количество', 'кол-во', 'кол.', '_merged_qty_']

# Коды собственных разработок встречаются в документах в нескольких видах:
# «ДЕ1», «ДЕ-1», «ДЕ 1.234.005», «DE1» и иногда с потерянной первой буквой: «Е1».
# Последний вариант принимаем только при наличии цифрового кода, чтобы не ловить
# обычные слова и обозначения компонентов.
OUR_DEVELOPMENT_RE = re.compile(
    r'(?<![\wА-Яа-яЁё])((?:д\s*[-._]?\s*[еe]|d\s*[-._]?\s*[еe]|[еe])\s*'
    r'\s*[-._]?\s*(?:№\s*)?(?:\d+|один|два|три|четыре|пять|шесть|семь|восемь|девять|десять)'
    r'(?:\s*[-.]?\s*\d+){0,3})(?![\wА-Яа-яЁё])',
    re.IGNORECASE,
)


def contains_our_development_code(value) -> bool:
    """Return whether text contains a DE/ДЕ own-development identifier."""
    if value is None:
        return False
    return bool(OUR_DEVELOPMENT_RE.search(str(value)))


def normalize_special_letters(value: str) -> str:
    """Normalize Word/Symbol-font variants used for the first letter of ДЕ codes."""
    text = unicodedata.normalize('NFKC', str(value or ''))
    # Word can leave zero-width/formatting marks around a symbol-font glyph.
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
    # In documents using Symbol/Wingdings the Cyrillic Д can surface as a pilcrow.
    text = re.sub(r'(?<![\wА-Яа-яЁё])¶(?=\s*[eе]\s*[-._]?\s*\d)', 'д', text,
                  flags=re.IGNORECASE)
    # Mathematical/Latin d used as the first glyph of the mixed DE code is
    # canonicalized to Cyrillic д so the exported code remains recognizable.
    text = re.sub(r'(?<![\wА-Яа-яЁё])d(?=\s*[eе]\s*[-._]?\s*\d)', 'д', text,
                  flags=re.IGNORECASE)
    # In some DOC->DOCX conversions the first glyph is dropped completely,
    # leaving ``e5.067.066-03``.  A multi-part identifier in this position is
    # an own-development code, so restore the missing Cyrillic ``д``.
    text = re.sub(
        r'(?<![\wА-Яа-яЁё])[eе](?=\s*[-._]?\s*\d+(?:\s*[.-]\s*\d+){1,3}(?:\b|$))',
        'де', text, flags=re.IGNORECASE)
    return text


def parse_number(value) -> Optional[float]:
    """Parse a complete localized number; distinguish missing/invalid values from zero."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Real):
        return float(value) if math.isfinite(value) else None
    text = str(value).strip()
    # Пробелы допускаются только как разделители групп по три цифры.
    text = text.replace('\u00a0', ' ').replace('\u202f', ' ')
    if not re.fullmatch(r'[+-]?(?:\d{1,3}(?: \d{3})+|\d+)(?:[.,]\d+)?', text):
        return None
    number = float(text.replace(' ', '').replace(',', '.'))
    return number if math.isfinite(number) else None


def require_number(value) -> float:
    """Reject invalid quantities instead of silently fabricating a number."""
    result = parse_number(value)
    if result is None:
        raise ValueError(f'Некорректное или отсутствующее число: {value!r}')
    return result


def format_number(value) -> str:
    """Format a quantity without discarding its fractional part."""
    return format(float(value), '.15g')


def normalize_column_names(columns: List[str]) -> List[str]:
    """
    Нормализует имена колонок (lowercase, strip)
    
    Args:
        columns: Список имен колонок
        
    Returns:
        Список нормализованных имен
    """
    normalized = []
    for name in columns:
        if name is None:
            normalized.append("")
            continue
        normalized.append(str(name).strip().lower())
    return normalized


def find_column(possible_names: List[str], columns: List[str]) -> Optional[str]:
    """
    Ищет колонку по списку возможных имен
    
    Args:
        possible_names: Список возможных имен колонки
        columns: Список имен колонок в DataFrame
        
    Returns:
        Найденное имя колонки или None
    """
    # Имена колонок сохраняем, поиск выполняем без учета регистра.
    actual = {str(c).strip().lower(): c for c in columns}
    for candidate in possible_names:
        if str(candidate).strip().lower() in actual:
            return actual[str(candidate).strip().lower()]
    # Если не нашли точное совпадение, ищем частичное (колонка начинается с candidate)
    for candidate in possible_names:
        for col in columns:
            if str(col).strip().lower().startswith(str(candidate).strip().lower()):
                return col
    return None


def has_any(text: str, keywords: List[str]) -> bool:
    """
    Проверяет наличие хотя бы одного ключевого слова в тексте
    
    Args:
        text: Текст для проверки
        keywords: Список ключевых слов
        
    Returns:
        True если хотя бы одно слово найдено
    """
    if not isinstance(text, str):
        return False
    lower = text.lower()
    return any(k in lower for k in keywords)


# Регулярные выражения для распознавания номиналов компонентов
RESISTOR_VALUE_RE = re.compile(
    r"(?i)\b\d+(?:[\.,]\d+)?\s*(?:ом|ohm|k\s*ohm|kohm|к\s*ом|ком|m\s*ohm|mohm|м\s*ом|мом)\b"
)

CAP_VALUE_RE = re.compile(
    r"(?i)\b\d+(?:[\.,]\d+)?\s*(?:pf|nf|uf|µf|μf|ф|пф|нф|мкф)\b"
)

IND_VALUE_RE = re.compile(
    r"(?i)\b\d+(?:[\.,]\d+)?\s*(?:nh|uh|µh|μh|mh|h|нгн|мкгн|мгн|гн)\b"
)

# Регулярные выражения для парсинга текстовых данных
LINE_SPLIT_RE = re.compile(r"\s{2,}|\t|;|,\s?(?=\S)")
POS_PREFIX_RE = re.compile(r"^(?:[A-ZА-Я]+\d+(?:[-,;\s]*[A-ZА-Я]*\d+)*)$", re.IGNORECASE)
