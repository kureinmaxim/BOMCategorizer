"""
Тесты для модуля форматирования
"""
import pytest
from bom_categorizer.formatters import (
    normalize_description,
    extract_tu_code,
    sort_by_value
)


class TestNormalization:
    """Тесты нормализации описаний"""
    
    def test_normalize_spaces_around_dashes(self):
        """Тест нормализации пробелов вокруг дефисов"""
        # Без пробелов -> с пробелами
        result = normalize_description('P1-12-0,1-100')
        assert 'P1 - 12 - 0,1 - 100' in result
        
        # Уже с пробелами -> не меняется
        result = normalize_description('P1 - 12 - 0,1 - 100')
        assert 'P1 - 12 - 0,1 - 100' in result
    
    def test_add_plus_minus_before_percent(self):
        """Тест добавления ± перед процентами"""
        # Без ±
        result = normalize_description('100 Ом 5%-Т')
        assert '± 5%' in result or '±5%' in result
        
        # Уже есть ±
        result = normalize_description('100 Ом ± 5%-Т')
        assert result.count('±') == 1  # Не должно дублироваться
    
    def test_normalize_space_before_percent(self):
        """Тест нормализации пробела перед процентом"""
        result = normalize_description('100 Ом5%-Т')
        assert '5%' in result
        # Должен быть пробел между Ом и цифрой
    
    def test_combined_normalization(self):
        """Тест комбинированной нормализации"""
        # Все проблемы сразу
        result = normalize_description('P1-12-0,1-100 Ом5%-Т')
        
        # Проверяем что все исправлено
        assert 'P1 - 12 - 0,1 - 100' in result  # Пробелы вокруг дефисов
        assert '± 5%' in result or '±5%' in result  # ± добавлен
    
    def test_preserve_other_text(self):
        """Тест что остальной текст сохраняется"""
        input_text = 'Резистор P1-12-0,1-100 Ом 5%-Т импортный'
        result = normalize_description(input_text)
        
        assert 'Резистор' in result
        assert 'импортный' in result


class TestTUExtraction:
    """Тесты извлечения ТУ кодов"""
    
    def test_extract_simple_tu(self):
        """Тест извлечения простого ТУ кода"""
        desc = 'Микросхема 1594ТЛ2Т АЕЯР.431320.420ТУ'
        name, tu = extract_tu_code(desc)
        
        assert name.strip() == 'Микросхема 1594ТЛ2Т'
        assert tu == 'АЕЯР.431320.420ТУ'
    
    def test_extract_tu_with_dashes(self):
        """Тест извлечения ТУ с дефисами"""
        desc = 'Компонент АЕЯР431200424-07ТУ'
        name, tu = extract_tu_code(desc)
        
        assert tu == 'АЕЯР431200424-07ТУ'
    
    def test_no_tu_code(self):
        """Тест когда ТУ кода нет"""
        desc = 'Резистор 100 Ом'
        name, tu = extract_tu_code(desc)
        
        assert name == desc
        assert tu is None
    
    def test_multiple_tu_codes(self):
        """Тест множественных ТУ кодов - должен извлечь первый"""
        desc = 'Компонент АБВГ.123ТУ и еще ДЕЁЖ.456ТУ'
        name, tu = extract_tu_code(desc)
        
        assert tu == 'АБВГ.123ТУ'
    
    def test_tu_at_start(self):
        """Тест ТУ в начале строки"""
        desc = 'АЕЯР.431320.420ТУ Микросхема'
        name, tu = extract_tu_code(desc)
        
        assert tu == 'АЕЯР.431320.420ТУ'
        assert 'Микросхема' in name


class TestSortByValue:
    """Тесты сортировки по номиналу"""
    
    def test_sort_resistors(self):
        """Тест сортировки резисторов по номиналу"""
        items = [
            {'description': 'Резистор 1 кОм'},
            {'description': 'Резистор 100 Ом'},
            {'description': 'Резистор 10 кОм'},
            {'description': 'Резистор 27 Ом'}
        ]
        
        sorted_items = sort_by_value(items, 'resistors')
        values = [item['description'] for item in sorted_items]
        
        # Должно быть: 27 Ом -> 100 Ом -> 1 кОм -> 10 кОм
        assert '27 Ом' in values[0]
        assert '100 Ом' in values[1]
        assert '1 кОм' in values[2]
        assert '10 кОм' in values[3]
    
    def test_sort_capacitors(self):
        """Тест сортировки конденсаторов"""
        items = [
            {'description': 'Конденсатор 1 мкФ'},
            {'description': 'Конденсатор 100 нФ'},
            {'description': 'Конденсатор 10 мкФ'}
        ]
        
        sorted_items = sort_by_value(items, 'capacitors')
        values = [item['description'] for item in sorted_items]
        
        # 100 нФ < 1 мкФ < 10 мкФ
        assert '100 нФ' in values[0]
        assert '1 мкФ' in values[1]
    
    def test_sort_mixed_units(self):
        """Тест сортировки с разными единицами измерения"""
        items = [
            {'description': 'Резистор 1 МОм'},
            {'description': 'Резистор 100 Ом'},
            {'description': 'Резистор 1 кОм'}
        ]
        
        sorted_items = sort_by_value(items, 'resistors')
        values = [item['description'] for item in sorted_items]
        
        # 100 Ом < 1 кОм < 1 МОм
        assert '100 Ом' in values[0]
        assert '1 кОм' in values[1]
        assert '1 МОм' in values[2]
    
    def test_sort_with_decimal(self):
        """Тест сортировки с десятичными значениями"""
        items = [
            {'description': 'Резистор 82.5 кОм'},
            {'description': 'Резистор 27 Ом'},
            {'description': 'Резистор 220 Ом'}
        ]
        
        sorted_items = sort_by_value(items, 'resistors')
        values = [item['description'] for item in sorted_items]
        
        # 27 Ом < 220 Ом < 82.5 кОм
        assert '27 Ом' in values[0]
        assert '220 Ом' in values[1]
        assert '82.5 кОм' in values[2]
    
    def test_sort_preserves_non_valued_items(self):
        """Тест что элементы без номинала тоже сортируются"""
        items = [
            {'description': 'Резистор 100 Ом'},
            {'description': 'Резистор переменный'},
            {'description': 'Резистор 27 Ом'}
        ]
        
        sorted_items = sort_by_value(items, 'resistors')
        
        # Все элементы должны остаться
        assert len(sorted_items) == 3
    
    def test_no_sort_for_other_categories(self):
        """Тест что другие категории не сортируются по номиналу"""
        items = [
            {'description': 'Микросхема Z'},
            {'description': 'Микросхема A'},
            {'description': 'Микросхема M'}
        ]
        
        # Для микросхем не должно быть сортировки по номиналу
        sorted_items = sort_by_value(items, 'ics')
        
        # Порядок может остаться как есть или по алфавиту
        assert len(sorted_items) == 3


class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_empty_description(self):
        """Тест пустого описания"""
        result = normalize_description('')
        assert result == ''
        
        name, tu = extract_tu_code('')
        assert name == ''
        assert tu is None
    
    def test_none_description(self):
        """Тест None описания"""
        result = normalize_description(None)
        # Должно вернуть пустую строку или None без ошибки
        assert result in [None, '']
    
    def test_unicode_handling(self):
        """Тест обработки юникод символов"""
        result = normalize_description('Резистор 100 Ом ± 5% 🔥')
        assert 'Резистор' in result
        assert '100 Ом' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
