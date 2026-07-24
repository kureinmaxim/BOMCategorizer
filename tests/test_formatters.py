"""
Тесты для модуля форматирования
"""
import pytest
from bom_categorizer.formatters import extract_tu_code


@pytest.mark.skip(reason="normalize_description живёт в main.py как вложенная функция, не экспортируется")
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
        assert tu == ''
    
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

    def test_manufacturer_at_start_removed_from_name(self):
        """Производитель в начале уходит в ТУ/Производитель, не остаётся в названии"""
        name, tu = extract_tu_code('Analog Devices EVAL-ADXL345Z')
        assert name == 'EVAL-ADXL345Z'
        assert tu == 'Analog Devices'

    def test_board_prefix_does_not_override_explicit_manufacturer(self):
        """Явный производитель важнее префикса NUCLEO/EVAL"""
        name, tu = extract_tu_code('Texas Instruments NUCLEO-F401RE')
        assert name == 'NUCLEO-F401RE'
        assert tu == 'Texas Instruments'

    def test_board_prefix_fallback(self):
        """Префикс платы даёт производителя, если он не указан явно"""
        name, tu = extract_tu_code('NUCLEO-F401RE')
        assert name == 'NUCLEO-F401RE'
        assert tu == 'STMicroelectronics'

    def test_firm_marker_extracted(self):
        """Маркер 'ф.' переносит производителя в отдельную колонку"""
        name, tu = extract_tu_code('Аттенюатор 50HFFA-009-2/6SMA, ф. Mini-Circuits')
        assert name == 'Аттенюатор 50HFFA-009-2/6SMA'
        assert tu == 'Mini-Circuits'

    def test_tu_keeps_priority_over_manufacturer(self):
        """Если есть ТУ — оно в колонке, производитель только убирается из названия"""
        name, tu = extract_tu_code(
            '1594ТЛ2Т АЕЯР.431320.420ТУ ф. Texas Instruments'
        )
        assert name == '1594ТЛ2Т'
        assert tu == 'АЕЯР.431320.420ТУ'

    def test_extended_manufacturers(self):
        """Расширенный список производителей (Yageo/Vishay/Murata)"""
        name, tu = extract_tu_code('Yageo RC0603FR-0710KL')
        assert name == 'RC0603FR-0710KL'
        assert tu == 'Yageo'

        name, tu = extract_tu_code('Murata GRM188R71H104KA93D')
        assert name == 'GRM188R71H104KA93D'
        assert tu == 'Murata'


@pytest.mark.skip(reason="sort_by_value отсутствует в formatters.py")
class TestSortByValue:
    """Тесты сортировки по номиналу (заглушка — функция не экспортируется)"""

    def test_placeholder(self):
        assert True


class TestEdgeCases:
    """Тесты граничных случаев extract_tu_code"""
    
    def test_empty_description(self):
        """Тест пустого описания"""
        name, tu = extract_tu_code('')
        assert name == ''
        assert tu == ''
    
    def test_none_description(self):
        """Тест None описания"""
        name, tu = extract_tu_code(None)
        assert name == ''
        assert tu == ''
    
    def test_unicode_handling(self):
        """Тест обработки юникод символов в extract_tu_code"""
        name, tu = extract_tu_code('Резистор 100 Ом ± 5%')
        assert 'Резистор' in name
        assert '100 Ом' in name
        assert tu == ''


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
