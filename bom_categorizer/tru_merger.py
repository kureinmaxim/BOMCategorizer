# -*- coding: utf-8 -*-
"""
Модуль для объединения данных из файлов ТРУ с BOM файлами.

Функции:
- normalize_for_matching: нормализация строк для сопоставления
- merge_tru_into_bom: основная функция объединения
- apply_merge_styles: применение стилей к изменённым строкам
"""

import re
import pandas as pd
from typing import List, Dict, Tuple, Optional, Set
from difflib import SequenceMatcher
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


# Цвета для форматирования
MERGED_ROW_FILL = PatternFill(start_color='E3F2FD', end_color='E3F2FD', fill_type='solid')  # Бледно-голубая
MERGED_NAME_FONT = Font(color='1a237e', bold=False)  # Тёмно-синий
OLD_QTY_FONT = Font(color='FF0000')  # Красный для старого количества


def normalize_for_matching(text: str) -> str:
    """
    Нормализует строку для сопоставления:
    - Удаляет лишние пробелы
    - Заменяет разные виды тире на обычный дефис
    - Приводит к нижнему регистру
    """
    if not text or pd.isna(text):
        return ""
    
    text = str(text).strip()
    
    # Заменяем разные виды тире и пробелов
    text = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]', '-', text)  # Различные тире
    text = re.sub(r'\s+', ' ', text)  # Множественные пробелы → один
    text = re.sub(r'\s*-\s*', '-', text)  # Пробелы вокруг тире
    
    return text.lower()


def extract_nominal(text: str) -> str:
    """
    Извлекает номинал из названия компонента.
    Примеры: "10 кОм", "100 нФ", "4.7 мкФ"
    """
    if not text:
        return ""
    
    # Паттерн для номинала: число + единица измерения
    patterns = [
        r'(\d+[\.,]?\d*)\s*(к[Оо]м|[Мм][Оо]м|[Оо]м|н[Фф]|мк[Фф]|п[Фф]|м[Гг]н|мк[Гг]н|н[Гг]н)',
        r'(\d+[\.,]?\d*)\s*(kOhm|MOhm|Ohm|nF|uF|pF|mH|uH|nH)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, str(text), re.IGNORECASE)
        if match:
            return normalize_for_matching(match.group(0))
    
    return ""


def similarity_ratio(a: str, b: str) -> float:
    """Вычисляет степень схожести двух строк (0.0 - 1.0)"""
    return SequenceMatcher(None, a, b).ratio()


def find_matching_tru_row(
    bom_name: str,
    bom_nominal: str,
    tru_df: pd.DataFrame,
    name_col: str = 'Наименование',
    min_name_similarity: float = 0.90
) -> Optional[pd.Series]:
    """
    Ищет соответствующую строку в ТРУ DataFrame.
    
    Args:
        bom_name: Название из BOM (Наименование ИВП)
        bom_nominal: Номинал из BOM (если есть)
        tru_df: DataFrame из файла ТРУ
        name_col: Название колонки с наименованием в ТРУ
        min_name_similarity: Минимальный порог совпадения названия (0.0-1.0)
    
    Returns:
        Строка из ТРУ или None
    """
    if name_col not in tru_df.columns:
        return None
    
    norm_bom_name = normalize_for_matching(bom_name)
    norm_bom_nominal = extract_nominal(bom_name)
    
    best_match = None
    best_similarity = 0.0
    
    for idx, row in tru_df.iterrows():
        tru_name = str(row.get(name_col, ''))
        norm_tru_name = normalize_for_matching(tru_name)
        
        # Сравниваем названия
        name_sim = similarity_ratio(norm_bom_name, norm_tru_name)
        
        if name_sim < min_name_similarity:
            continue
        
        # Если есть номинал в BOM, проверяем 100% совпадение
        if norm_bom_nominal:
            tru_nominal = extract_nominal(tru_name)
            if tru_nominal and tru_nominal != norm_bom_nominal:
                continue  # Номинал не совпал — пропускаем
        
        # Нашли подходящее совпадение
        if name_sim > best_similarity:
            best_similarity = name_sim
            best_match = row
    
    return best_match


def merge_tru_into_bom(
    bom_df: pd.DataFrame,
    tru_dfs: List[pd.DataFrame],
    bom_name_col: str = 'Наименование ИВП',
    bom_qty_col: str = 'шт.',
    tru_name_col: str = 'Наименование',
    tru_article_col: str = 'Артикул',
    tru_qty_col: str = 'Количество',
    tru_cost_col: str = 'Стоимость'
) -> Tuple[pd.DataFrame, Set[int]]:
    """
    Объединяет данные из ТРУ файлов с BOM DataFrame.
    
    Args:
        bom_df: DataFrame из BOM файла
        tru_dfs: Список DataFrame из ТРУ файлов
        bom_name_col: Колонка с названием в BOM
        bom_qty_col: Колонка с количеством в BOM
        tru_name_col: Колонка с названием в ТРУ
        tru_article_col: Колонка с артикулом в ТРУ
        tru_qty_col: Колонка с количеством в ТРУ
        tru_cost_col: Колонка со стоимостью в ТРУ
    
    Returns:
        (обновлённый DataFrame, множество индексов изменённых строк)
    """
    result_df = bom_df.copy()
    merged_indices: Set[int] = set()
    
    # Объединяем все ТРУ в один DataFrame
    combined_tru = pd.concat(tru_dfs, ignore_index=True) if tru_dfs else pd.DataFrame()
    
    if combined_tru.empty:
        return result_df, merged_indices
    
    # Убедимся что нужные колонки существуют в BOM
    if 'КОД ERP(МР)' not in result_df.columns:
        result_df['КОД ERP(МР)'] = ''
    if 'Стоимость' not in result_df.columns:
        result_df['Стоимость'] = ''
    
    # Обрабатываем каждую строку BOM
    for idx, bom_row in result_df.iterrows():
        bom_name = bom_row.get(bom_name_col, '')
        
        if not bom_name or pd.isna(bom_name):
            continue
        
        # Ищем совпадение в ТРУ
        tru_match = find_matching_tru_row(
            bom_name=str(bom_name),
            bom_nominal=extract_nominal(str(bom_name)),
            tru_df=combined_tru,
            name_col=tru_name_col,
            min_name_similarity=0.90
        )
        
        if tru_match is None:
            continue
        
        # Нашли совпадение — обновляем данные
        merged_indices.add(idx)
        
        # 1. КОД ERP(МР) ← Артикул
        if tru_article_col in tru_match.index:
            article = tru_match[tru_article_col]
            if article and not pd.isna(article):
                result_df.at[idx, 'КОД ERP(МР)'] = str(article).strip()
        
        # 2. Стоимость ← Стоимость из ТРУ
        if tru_cost_col in tru_match.index:
            cost = tru_match[tru_cost_col]
            if cost and not pd.isna(cost):
                result_df.at[idx, 'Стоимость'] = cost
        
        # 3. Количество: TRU_qty (BOM_qty) если разное
        if tru_qty_col in tru_match.index and bom_qty_col in result_df.columns:
            tru_qty = tru_match[tru_qty_col]
            bom_qty = bom_row.get(bom_qty_col, '')
            
            if tru_qty and not pd.isna(tru_qty):
                try:
                    tru_qty_num = float(tru_qty)
                    bom_qty_num = float(bom_qty) if bom_qty and not pd.isna(bom_qty) else 0
                    
                    if tru_qty_num != bom_qty_num and bom_qty_num > 0:
                        # Формат: "15 (10)" где 15 — из ТРУ, 10 — исходное
                        new_qty_str = f"{int(tru_qty_num)} ({int(bom_qty_num)})"
                        result_df.at[idx, bom_qty_col] = new_qty_str
                    elif bom_qty_num == 0:
                        result_df.at[idx, bom_qty_col] = int(tru_qty_num)
                except (ValueError, TypeError):
                    pass
    
    return result_df, merged_indices


def apply_merge_styles(
    worksheet,
    merged_rows: Set[int],
    name_col_idx: int = 2,
    qty_col_idx: int = 4,
    header_row: int = 1
):
    """
    Применяет стили к изменённым строкам в Excel worksheet.
    
    Args:
        worksheet: openpyxl worksheet
        merged_rows: Множество индексов строк (0-based из pandas)
        name_col_idx: Индекс колонки "Наименование ИВП" (1-based)
        qty_col_idx: Индекс колонки "шт." (1-based)
        header_row: Номер строки заголовка
    """
    thin_border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    for pandas_idx in merged_rows:
        # Конвертируем pandas index (0-based) в Excel row (1-based + header)
        excel_row = pandas_idx + header_row + 1
        
        # Применяем стили ко всей строке
        for col_idx in range(1, worksheet.max_column + 1):
            cell = worksheet.cell(row=excel_row, column=col_idx)
            
            # Заливка — бледно-голубая
            cell.fill = MERGED_ROW_FILL
            cell.border = thin_border
            
            # Шрифт наименования — тёмно-синий
            if col_idx == name_col_idx:
                cell.font = MERGED_NAME_FONT
            
            # Проверяем количество с форматом "X (Y)"
            if col_idx == qty_col_idx:
                cell_value = str(cell.value) if cell.value else ''
                if '(' in cell_value and ')' in cell_value:
                    # TODO: В openpyxl нельзя сделать часть текста красным
                    # Можно использовать RichText, но это сложнее
                    # Пока оставляем весь текст как есть
                    pass
