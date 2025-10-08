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
from typing import List, Optional


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
    # Сначала ищем точное совпадение
    for candidate in possible_names:
        if candidate in columns:
            return candidate
    # Если не нашли точное совпадение, ищем частичное (колонка начинается с candidate)
    for candidate in possible_names:
        for col in columns:
            if col.startswith(candidate):
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
