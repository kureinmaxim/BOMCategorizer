"""
Тесты для модуля классификации компонентов
"""
import pytest
from bom_categorizer.classifiers import classify_row


class TestBasicClassification:
    """Тесты базовой классификации"""
    
    def test_resistor_classification(self):
        """Тест классификации резисторов"""
        # Стандартный резистор
        result = classify_row('R1', 'Резистор 100 Ом ± 5% - М', None, None, strict=False)
        assert result == 'resistors', f"Expected 'resistors', got '{result}'"
        
        # Резистор с разными единицами
        result = classify_row('R2', 'Резистор 1 кОм ± 1% - Т', None, None, strict=False)
        assert result == 'resistors'
        
        # P-серия резисторов
        result = classify_row('', 'P1 - 12 - 0,125 - 100 Ом ± 5% - М', None, None, strict=False)
        assert result == 'resistors'
    
    def test_capacitor_classification(self):
        """Тест классификации конденсаторов"""
        result = classify_row('C1', 'Конденсатор 100 нФ ± 10%', None, None, strict=False)
        assert result == 'capacitors'
        
        result = classify_row('C2', 'К10-17Б 0,1 мкФ', None, None, strict=False)
        assert result == 'capacitors'
    
    def test_ic_classification(self):
        """Тест классификации микросхем"""
        # Отечественные микросхемы
        result = classify_row('DD1', '1594ТЛ2Т', None, None, strict=False)
        assert result == 'ics'
        
        result = classify_row('DA1', 'К1533ЛА3', None, None, strict=False)
        assert result == 'ics'
        
        # Импортные микросхемы
        result = classify_row('U1', 'HMC435AMS8GE', None, None, strict=False)
        assert result == 'ics'
    
    def test_semiconductor_classification(self):
        """Тест классификации полупроводников"""
        # Диоды
        result = classify_row('VD1', 'Диод 1N4148', None, None, strict=False)
        assert result == 'semiconductors'
        
        # Транзисторы
        result = classify_row('VT1', 'Транзистор 2N2222', None, None, strict=False)
        assert result == 'semiconductors'
        
        # Оптопары
        result = classify_row('', 'Оптопара PC817', None, None, strict=False)
        assert result == 'semiconductors'
    
    def test_connector_classification(self):
        """Тест классификации разъемов"""
        result = classify_row('X1', 'Разъем SMA-female', None, None, strict=False)
        assert result == 'connectors'
        
        result = classify_row('J1', 'Розетка USB Type-C', None, None, strict=False)
        assert result == 'connectors'
    
    def test_optical_classification(self):
        """Тест классификации оптических компонентов"""
        result = classify_row('', 'Модуль оптический 10G', None, None, strict=False)
        assert result == 'optics'
        
        # Адаптер оптический должен классифицироваться как optics
        result = classify_row('', 'Адаптер оптический FC/APC', None, None, strict=False)
        assert result == 'optics'
    
    def test_power_module_classification(self):
        """Тест классификации модулей питания"""
        result = classify_row('', 'Преобразователь DC-DC 5V -> 3.3V', None, None, strict=False)
        assert result == 'power_modules'
        
        result = classify_row('', 'Источник питания AC-DC 12V', None, None, strict=False)
        assert result == 'power_modules'
    
    def test_debug_boards_classification(self):
        """Тест классификации отладочных плат и СВЧ модулей"""
        # Делители Qualwave - СВЧ модули
        result = classify_row('', 'Делитель мощности Qualwave', None, None, strict=False)
        assert result == 'rf_modules'
        
        # Ответвитель - СВЧ модули
        result = classify_row('', 'Ответвитель СВЧ 10дБ', None, None, strict=False)
        assert result in ['rf_modules', 'dev_boards']
    
    def test_cable_classification(self):
        """Тест классификации кабелей"""
        result = classify_row('', 'Кабель RG-58', None, None, strict=False)
        assert result == 'cables'
        
        result = classify_row('', 'Провод МГТФ 0.5', None, None, strict=False)
        assert result == 'cables'
    
    def test_inductor_classification(self):
        """Тест классификации индуктивностей"""
        result = classify_row('L1', 'Дроссель 10 мкГн', None, None, strict=False)
        assert result == 'inductors'
        
        result = classify_row('L2', 'Индуктивность 100 нГн', None, None, strict=False)
        assert result == 'inductors'
    
    def test_unclassified(self):
        """Тест для нераспознанных компонентов"""
        result = classify_row('', 'Непонятный компонент XYZ123', None, None, strict=False)
        assert result == 'unclassified'
    
    def test_other_classification(self):
        """Тест классификации прочих компонентов"""
        result = classify_row('', 'Предохранитель 1A', None, None, strict=False)
        assert result == 'others'


class TestAdvancedClassification:
    """Тесты продвинутой классификации"""
    
    def test_classification_with_note(self):
        """Тест классификации с учетом примечания"""
        result = classify_row(
            'R1',
            'Неизвестное название',
            None,
            None,
            strict=False,
            note='Резистор 100 Ом'
        )
        assert result == 'resistors'
    
    def test_strict_mode(self):
        """Тест строгого режима классификации"""
        # В нестрогом режиме пустое описание -> может быть non_bom или unclassified
        result = classify_row('', '', None, None, strict=False)
        assert result in ['non_bom', 'unclassified']
        
        # В строгом режиме тоже
        result = classify_row('', '', None, None, strict=True)
        assert result in ['non_bom', 'unclassified']
    
    def test_normalization_affects_classification(self):
        """Тест что нормализация влияет на классификацию"""
        # С пробелами и без - должны классифицироваться одинаково
        result1 = classify_row('', 'P1-12-0,1-100 Ом 5%-Т', None, None, strict=False)
        result2 = classify_row('', 'P1 - 12 - 0,1 - 100 Ом ± 5% - Т', None, None, strict=False)
        assert result1 == result2 == 'resistors'
    
    def test_special_characters_handling(self):
        """Тест обработки специальных символов"""
        # Проверка что символы ± корректно обрабатываются
        result = classify_row('R1', 'Резистор 100 Ом ± 5%', None, None, strict=False)
        assert result == 'resistors'
    
    def test_case_insensitivity(self):
        """Тест что классификация не зависит от регистра"""
        result1 = classify_row('R1', 'РЕЗИСТОР 100 ОМ', None, None, strict=False)
        result2 = classify_row('R1', 'резистор 100 ом', None, None, strict=False)
        result3 = classify_row('R1', 'Резистор 100 Ом', None, None, strict=False)
        
        assert result1 == result2 == result3 == 'resistors'


class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_empty_inputs(self):
        """Тест пустых входных данных"""
        result = classify_row('', '', None, None, strict=False)
        assert result in ['non_bom', 'unclassified']
    
    def test_none_inputs(self):
        """Тест None входных данных"""
        result = classify_row(None, None, None, None, strict=False)
        assert result in ['non_bom', 'unclassified']
    
    def test_very_long_description(self):
        """Тест очень длинного описания"""
        long_desc = 'Резистор ' + 'X' * 1000 + ' 100 Ом'
        result = classify_row('R1', long_desc, None, None, strict=False)
        assert result == 'resistors'
    
    def test_unicode_characters(self):
        """Тест юникод символов"""
        result = classify_row('R1', 'Резистор 100 Ом ± 5% 🔥', None, None, strict=False)
        assert result == 'resistors'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
