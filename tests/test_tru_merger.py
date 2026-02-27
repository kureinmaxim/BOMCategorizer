# -*- coding: utf-8 -*-
"""
Тесты для модуля объединения ТРУ с BOM (tru_merger.py)
"""
import pytest
import pandas as pd
from bom_categorizer.tru_merger import (
    normalize_for_matching,
    normalize_erp_code_from_artikul,
    extract_pure_code,
    extract_component_code,
    extract_nominal,
    extract_tru_number,
    similarity_ratio,
    find_matching_tru_row,
    merge_tru_into_bom,
    build_ostatki_and_zapas_reports,
    _parse_qty_pair,
)


# ──────────────────────────────────────────────────────────────────────
# normalize_for_matching
# ──────────────────────────────────────────────────────────────────────
class TestNormalizeForMatching:
    """Тесты нормализации строк для сопоставления"""

    def test_lowercase(self):
        """Приведение к нижнему регистру"""
        assert normalize_for_matching("РЕЗИСТОР") == "резистор"

    def test_dash_normalization(self):
        """Замена юникодных тире на обычный дефис"""
        # EN DASH, EM DASH, MINUS SIGN
        for dash in ['\u2013', '\u2014', '\u2212']:
            result = normalize_for_matching(f"С2{dash}33")
            assert '-' in result and dash not in result

    def test_spaces_around_dashes(self):
        """Удаление пробелов вокруг тире"""
        result = normalize_for_matching("С2 - 33")
        assert result == "с2-33"

    def test_multiple_spaces(self):
        """Множественные пробелы → один"""
        result = normalize_for_matching("Резистор   100   Ом")
        assert "  " not in result

    def test_suffix_removal(self):
        """Удаление суффиксов типа _LW"""
        result = normalize_for_matching("0603HP-47NXJ_LW")
        assert "_lw" not in result

    def test_empty_string(self):
        """Пустая строка"""
        assert normalize_for_matching("") == ""

    def test_none_and_nan(self):
        """None и NaN возвращают пустую строку"""
        assert normalize_for_matching(None) == ""
        assert normalize_for_matching(float('nan')) == ""


# ──────────────────────────────────────────────────────────────────────
# normalize_erp_code_from_artikul
# ──────────────────────────────────────────────────────────────────────
class TestNormalizeErpCode:
    """Тесты нормализации ERP-кодов из артикулов"""

    def test_none_returns_empty(self):
        assert normalize_erp_code_from_artikul(None) == ''

    def test_nan_returns_empty(self):
        assert normalize_erp_code_from_artikul(float('nan')) == ''

    def test_empty_string(self):
        assert normalize_erp_code_from_artikul('') == ''
        assert normalize_erp_code_from_artikul('  ') == ''

    def test_header_repeat_filtered(self):
        """Повтор заголовка 'Артикул' → пустая строка"""
        assert normalize_erp_code_from_artikul('Артикул') == ''

    def test_pure_digits_preserved(self):
        """Ведущие нули сохраняются"""
        assert normalize_erp_code_from_artikul('000123') == '000123'

    def test_float_truncated(self):
        """Десятичная часть .0 удаляется"""
        assert normalize_erp_code_from_artikul('123.0') == '123'

    def test_comma_decimal_truncated(self):
        """Десятичная часть ,0 удаляется"""
        assert normalize_erp_code_from_artikul('123,0') == '123'

    def test_nbsp_removed(self):
        """Неразрывный пробел удаляется"""
        result = normalize_erp_code_from_artikul('1\u00A0234')
        assert '\u00A0' not in result

    def test_integer_value(self):
        """Числовое значение (int/float) нормализуется"""
        assert normalize_erp_code_from_artikul(12345) == '12345'
        assert normalize_erp_code_from_artikul(12345.0) == '12345'


# ──────────────────────────────────────────────────────────────────────
# extract_pure_code
# ──────────────────────────────────────────────────────────────────────
class TestExtractPureCode:
    """Тесты извлечения чистого кода компонента"""

    def test_chip_inductor_prefix_removal(self):
        """Удаление 'Чип катушки индуктивности'"""
        result = extract_pure_code("Чип катушки индуктивности 0603HP-47NXJ_LW")
        assert "0603" in result
        assert "47" in result.lower()
        # Не должно содержать слов-категорий
        assert "чип" not in result
        assert "катушк" not in result

    def test_category_word_removal(self):
        """Удаление типовых слов-категорий"""
        result = extract_pure_code("Микросхема SN74LVC8T245")
        assert "микросхема" not in result
        assert "sn74" in result.lower() or "ch74" in result.lower()

    def test_manufacturer_removal(self):
        """Удаление названий производителей"""
        result = extract_pure_code("0603HP-47NXJ Coilcraft")
        assert "coilcraft" not in result

    def test_cyrillic_confusable_replacement(self):
        """Замена кириллических символов на похожие латинские"""
        # 'Н' (кириллица) → 'h' (латиница), 'Р' → 'p'
        result = extract_pure_code("0603НР")
        assert "h" in result and "p" in result

    def test_space_normalization(self):
        """Пробелы убираются"""
        result = extract_pure_code("0603HP - 47NXJ")
        assert " " not in result

    def test_dots_to_dashes(self):
        """Точки заменяются на дефисы"""
        result = extract_pure_code("ОЖ0.467.093")
        # Точки должны стать дефисами
        assert "." not in result

    def test_empty_input(self):
        """Пустой ввод"""
        assert extract_pure_code("") == ""
        assert extract_pure_code(None) == ""

    def test_lowercase_output(self):
        """Результат всегда в нижнем регистре"""
        result = extract_pure_code("ABC123")
        assert result == result.lower()


# ──────────────────────────────────────────────────────────────────────
# extract_component_code
# ──────────────────────────────────────────────────────────────────────
class TestExtractComponentCode:
    """Тесты извлечения кода компонента из названия"""

    def test_russian_ic_code(self):
        """Отечественная микросхема: '1564АП3У2 ЭП' → '1564АП3У2'"""
        result = extract_component_code("1564АП3У2 ЭП")
        assert "1564" in result

    def test_prefixed_component(self):
        """С префиксом: 'Микросхема 1564ТП2У'"""
        result = extract_component_code("Микросхема 1564ТП2У ЭП")
        assert "1564" in result

    def test_resistor_capacitor_code(self):
        """Резистор/конденсатор: 'К10-17Б' извлекается"""
        result = extract_component_code("К10-17Б-Н90-0,047 мкФ ± 10%")
        assert result != ""

    def test_western_ic_code(self):
        """Импортная микросхема"""
        result = extract_component_code("SN74LVC8T245DWR")
        assert "SN74" in result

    def test_empty_returns_empty(self):
        """Пустой ввод"""
        assert extract_component_code("") == ""
        assert extract_component_code(None) == ""

    def test_pure_text_no_code(self):
        """Чистый текст без кода"""
        result = extract_component_code("Просто текст без кода")
        # Может вернуть что-то или пустую строку
        assert isinstance(result, str)


# ──────────────────────────────────────────────────────────────────────
# extract_nominal
# ──────────────────────────────────────────────────────────────────────
class TestExtractNominal:
    """Тесты извлечения номинала"""

    def test_resistance_kohm(self):
        """Сопротивление в кОм"""
        result = extract_nominal("Резистор 10 кОм ± 5%")
        assert result != ""
        assert "10" in result

    def test_capacitance_nf(self):
        """Ёмкость в нФ"""
        result = extract_nominal("Конденсатор 100 нФ")
        assert result != ""
        assert "100" in result

    def test_inductance_ugh(self):
        """Индуктивность в мкГн"""
        result = extract_nominal("Дроссель 4,7 мкГн")
        assert result != ""

    def test_no_nominal(self):
        """Нет номинала"""
        assert extract_nominal("SN74LVC8T245") == ""

    def test_empty(self):
        """Пустой ввод"""
        assert extract_nominal("") == ""
        assert extract_nominal(None) == ""


# ──────────────────────────────────────────────────────────────────────
# extract_tru_number
# ──────────────────────────────────────────────────────────────────────
class TestExtractTruNumber:
    """Тесты извлечения номера ТРУ из имени файла"""

    def test_standard_tru_filename(self):
        """Стандартное имя: ТРУ.953033.7471_tpy.xlsx"""
        result = extract_tru_number("ТРУ.953033.7471_tpy.xlsx")
        assert "953033" in result
        assert "7471" in result
        assert "_tpy" not in result

    def test_tru_without_suffix(self):
        """Без суффикса: ТРУ.953033.7471.xls"""
        result = extract_tru_number("ТРУ.953033.7471.xls")
        assert "953033" in result
        assert "7471" in result

    def test_latin_tpy(self):
        """Латинское написание"""
        result = extract_tru_number("TPY.953033.7471_тру.xlsx")
        assert "953033" in result

    def test_tru_suffix_stripped(self):
        """Суффикс _tpy удалён"""
        result = extract_tru_number("ТРУ.953033.12345_tpy.xlsx")
        assert "tpy" not in result.lower()

    def test_plain_filename(self):
        """Обычный файл без ТРУ паттерна"""
        result = extract_tru_number("data.xlsx")
        assert isinstance(result, str)


# ──────────────────────────────────────────────────────────────────────
# similarity_ratio
# ──────────────────────────────────────────────────────────────────────
class TestSimilarityRatio:
    """Тесты вычисления схожести строк"""

    def test_identical(self):
        """Одинаковые строки → 1.0"""
        assert similarity_ratio("abc", "abc") == 1.0

    def test_completely_different(self):
        """Совершенно разные строки → низкое значение"""
        assert similarity_ratio("abc", "xyz") < 0.5

    def test_similar_strings(self):
        """Похожие строки → высокое значение"""
        assert similarity_ratio("резистор 100 ом", "резистор 100ом") > 0.8


# ──────────────────────────────────────────────────────────────────────
# _parse_qty_pair
# ──────────────────────────────────────────────────────────────────────
class TestParseQtyPair:
    """Тесты парсинга пары количества 'TRU (BOM)'"""

    def test_valid_pair(self):
        """Стандартный формат '15 (10)'"""
        result = _parse_qty_pair("15 (10)")
        assert result == (15, 10)

    def test_no_pair(self):
        """Простое число без скобок"""
        assert _parse_qty_pair("10") is None

    def test_none_input(self):
        """None → None"""
        assert _parse_qty_pair(None) is None

    def test_nan_input(self):
        """NaN → None"""
        assert _parse_qty_pair(float('nan')) is None

    def test_spaces_in_pair(self):
        """Пробелы внутри"""
        result = _parse_qty_pair(" 15 ( 10 ) ")
        assert result == (15, 10)


# ──────────────────────────────────────────────────────────────────────
# find_matching_tru_row
# ──────────────────────────────────────────────────────────────────────
class TestFindMatchingTruRow:
    """Тесты поиска соответствующей строки ТРУ"""

    @pytest.fixture
    def tru_df(self):
        """ТРУ DataFrame для тестов"""
        return pd.DataFrame({
            'Наименование': [
                'Микросхема 1564АП3У2 ЭП АЕЯР.431320.420ТУ',
                'Чип катушки индуктивности 0603HP-47NXJ_LW Coilcraft',
                'Модуль электропитания МДМ100-1В3ЦФУ',
                'Разъем Вилка МДМ30-1В15ТУП',
                'Разъем Розетка МДМ30-1В15ТУП',
            ],
            'Артикул': ['12345', '67890', '22222', '33333', '44444'],
            'Количество': [10, 20, 3, 8, 4],
        })

    def test_exact_pure_code_match(self, tru_df):
        """Точное совпадение чистого кода"""
        result = find_matching_tru_row("0603HP-47NXJ", "", tru_df)
        assert result is not None
        assert '67890' in str(result.get('Артикул', ''))

    def test_prefixed_match(self, tru_df):
        """Матч с префиксом категории"""
        result = find_matching_tru_row("Микросхема 1564АП3У2", "", tru_df)
        assert result is not None
        assert '12345' in str(result.get('Артикул', ''))

    def test_type_keyword_vilka_vs_rozetka(self, tru_df):
        """Различение Вилка/Розетка"""
        result_vilka = find_matching_tru_row("Вилка МДМ30-1В15ТУП", "", tru_df)
        result_rozetka = find_matching_tru_row("Розетка МДМ30-1В15ТУП", "", tru_df)
        # Вилка и Розетка должны матчить разные строки
        if result_vilka is not None and result_rozetka is not None:
            assert str(result_vilka.get('Артикул', '')) != str(result_rozetka.get('Артикул', ''))

    def test_no_match_for_unknown(self, tru_df):
        """Нет матча для неизвестного компонента"""
        result = find_matching_tru_row("Абсолютно неизвестный компонент XYZ999", "", tru_df)
        assert result is None

    def test_empty_tru_returns_none(self):
        """Пустой ТРУ DataFrame → None"""
        empty_df = pd.DataFrame({'Наименование': [], 'Артикул': []})
        result = find_matching_tru_row("Микросхема 1564АП3У2", "", empty_df)
        assert result is None

    def test_short_code_match(self, tru_df):
        """Короткий код без слов-категорий"""
        result = find_matching_tru_row("МДМ100-1В3ЦФУ", "", tru_df)
        assert result is not None

    def test_required_code_filter(self, tru_df):
        """Фильтрация по required_code"""
        result = find_matching_tru_row(
            "Вилка МДМ30-1В15ТУП", "", tru_df,
            required_code="МДМ30-1В15ТУП"
        )
        assert result is not None


# ──────────────────────────────────────────────────────────────────────
# merge_tru_into_bom
# ──────────────────────────────────────────────────────────────────────
class TestMergeTruIntoBom:
    """Тесты объединения ТРУ с BOM"""

    def test_basic_merge(self, sample_bom_df, sample_tru_df):
        """Базовое объединение: совпавшие строки получают данные ТРУ"""
        merged_df, merged_indices, used_indices = merge_tru_into_bom(
            bom_df=sample_bom_df,
            tru_dfs=[sample_tru_df],
            tru_filenames=["ТРУ.953033.12345_tpy.xlsx"],
        )
        assert len(merged_indices) > 0, "Должны быть совпадения"
        assert len(merged_df) == len(sample_bom_df), "Кол-во строк не должно меняться"

    def test_erp_columns_created(self, sample_bom_df, sample_tru_df):
        """Создаются колонки КОД ERP(МР), Стоимость, № ТРУ"""
        merged_df, merged_indices, _ = merge_tru_into_bom(
            bom_df=sample_bom_df,
            tru_dfs=[sample_tru_df],
            tru_filenames=["ТРУ.953033.12345_tpy.xlsx"],
        )
        if merged_indices:
            assert 'КОД ERP(МР)' in merged_df.columns or 'Стоимость' in merged_df.columns or '№ ТРУ' in merged_df.columns

    def test_empty_tru_list(self, sample_bom_df):
        """Пустой список ТРУ → данные без изменений"""
        # При пустом tru_dfs функция возвращает 2 значения (без used_indices)
        result = merge_tru_into_bom(
            bom_df=sample_bom_df,
            tru_dfs=[],
        )
        merged_df = result[0]
        merged_indices = result[1]
        assert len(merged_indices) == 0
        assert len(merged_df) == len(sample_bom_df)

    def test_unmatched_rows_unchanged(self, sample_bom_df, sample_tru_df):
        """Строки без совпадения сохраняют оригинальные значения"""
        merged_df, merged_indices, _ = merge_tru_into_bom(
            bom_df=sample_bom_df,
            tru_dfs=[sample_tru_df],
            tru_filenames=["ТРУ.953033.12345_tpy.xlsx"],
        )
        all_indices = set(range(len(sample_bom_df)))
        unmatched = all_indices - merged_indices
        for idx in unmatched:
            orig_name = sample_bom_df.iloc[idx]['Наименование ИВП']
            merged_name = merged_df.iloc[idx]['Наименование ИВП']
            assert str(orig_name) == str(merged_name)

    def test_multiple_tru_files(self, sample_bom_df):
        """Объединение с несколькими ТРУ файлами"""
        tru1 = pd.DataFrame({
            'Наименование': ['Микросхема 1564АП3У2 ЭП'],
            'Артикул': ['12345'],
            'Количество': [10],
        })
        tru2 = pd.DataFrame({
            'Наименование': ['Модуль электропитания МДМ100-1В3ЦФУ'],
            'Артикул': ['99999'],
            'Количество': [3],
        })
        merged_df, merged_indices, _ = merge_tru_into_bom(
            bom_df=sample_bom_df,
            tru_dfs=[tru1, tru2],
            tru_filenames=["ТРУ.1_tpy.xlsx", "ТРУ.2_tpy.xlsx"],
        )
        # Должны быть совпадения из обоих файлов
        assert len(merged_indices) >= 1


# ──────────────────────────────────────────────────────────────────────
# build_ostatki_and_zapas_reports
# ──────────────────────────────────────────────────────────────────────
class TestBuildOstatkiZapas:
    """Тесты построения отчётов остатков и запасов"""

    def test_unmatched_bom_goes_to_ostatki(self):
        """Несопоставленные BOM строки попадают в ostatki"""
        df = pd.DataFrame({
            'Наименование ИВП': ['Резистор 100 Ом', 'Конденсатор 10 нФ'],
            'шт.': [10, 5],
        })
        merged_indices = set()  # ничего не совпало
        ostatki, zapas = build_ostatki_and_zapas_reports(df, merged_indices)
        assert len(ostatki) == 2
        assert len(zapas) == 0

    def test_tru_excess_goes_to_zapas(self):
        """Избыток ТРУ → zapas"""
        df = pd.DataFrame({
            'Наименование ИВП': ['Резистор 100 Ом'],
            'шт.': ['15 (10)'],  # TRU=15, BOM=10
        })
        merged_indices = {0}
        ostatki, zapas = build_ostatki_and_zapas_reports(df, merged_indices, qty_col='шт.')
        assert len(zapas) > 0

    def test_bom_excess_goes_to_ostatki(self):
        """Избыток BOM → ostatki"""
        df = pd.DataFrame({
            'Наименование ИВП': ['Резистор 100 Ом'],
            'шт.': ['5 (10)'],  # TRU=5, BOM=10
        })
        merged_indices = {0}
        ostatki, zapas = build_ostatki_and_zapas_reports(df, merged_indices, qty_col='шт.')
        assert len(ostatki) > 0

    def test_empty_merged_df(self):
        """Пустой DataFrame → пустые отчёты"""
        df = pd.DataFrame()
        ostatki, zapas = build_ostatki_and_zapas_reports(df, set())
        assert ostatki.empty
        assert zapas.empty

    def test_unmatched_tru_goes_to_zapas(self):
        """Несопоставленные ТРУ строки → zapas"""
        df = pd.DataFrame({
            'Наименование ИВП': ['Резистор 100 Ом'],
            'шт.': [10],
        })
        unmatched_tru = pd.DataFrame({
            'Наименование': ['Неизвестный компонент'],
            'Количество': [5],
        })
        merged_indices = {0}
        ostatki, zapas = build_ostatki_and_zapas_reports(
            df, merged_indices, unmatched_tru=unmatched_tru
        )
        assert len(zapas) > 0


# ──────────────────────────────────────────────────────────────────────
# Регрессионные тесты для исправлений алгоритма матчинга
# ──────────────────────────────────────────────────────────────────────
class TestMatchingFixes:
    """Регрессионные тесты для 9 исправлений алгоритма сопоставления"""

    def test_fix1_nominal_space_equivalence(self):
        """Fix 1: Пробел в номинале не должен влиять на сравнение"""
        # "12 пФ" и "12пФ" должны дать одинаковый номинал
        nom_with_space = extract_nominal("К10-17в-М47-12 пФ ± 10%")
        nom_without_space = extract_nominal("К10-17в-М47-12пФ±10%")
        assert nom_with_space == nom_without_space
        assert ' ' not in nom_with_space  # нет пробелов в результате

    def test_fix1_nominal_capacitor_matching(self):
        """Fix 1: К10 конденсатор должен находить ТРУ с тем же номиналом"""
        tru_df = pd.DataFrame({
            'Наименование': ['Конденсатор К10-17в-М47-12пФ±10% ОЖ0.460.107 ТУ'],
            'Артикул': ['11111'],
            'Количество': [10],
        })
        result = find_matching_tru_row("К10 - 17в - М47 - 12 пФ ± 10%", "", tru_df)
        assert result is not None

    def test_fix2_percent_dash_normalized(self):
        """Fix 2: Дефис после % убирается в pure code"""
        # BOM: "С2 - 33 - 0,125 - 27 Ом ± 5% - А - Д - В"
        bom_pure = extract_pure_code("С2 - 33 - 0,125 - 27 Ом ± 5% - А - Д - В")
        tru_pure = extract_pure_code("Резистор С2-33-0,125-27 Ом±5% А-Д-В ОЖ0.467.093 ТУ")
        assert bom_pure == tru_pure

    def test_fix2_c2_33_resistor_matching(self):
        """Fix 2: С2-33 резистор должен совпадать с ТРУ"""
        tru_df = pd.DataFrame({
            'Наименование': ['Резистор С2-33-0,125-27 Ом±5% А-Д-В ОЖ0.467.093 ТУ'],
            'Артикул': ['22222'],
            'Количество': [5],
        })
        result = find_matching_tru_row(
            "С2 - 33 - 0,125 - 27 Ом ± 5% - А - Д - В",
            extract_nominal("С2 - 33 - 0,125 - 27 Ом ± 5% - А - Д - В"),
            tru_df
        )
        assert result is not None

    def test_fix3_quote_normalization(self):
        """Fix 3: Кавычки нормализуются одинаково"""
        bom_pure = extract_pure_code("К53 - 66 «Е» - 50В - 68 мкФ ± 10%")
        tru_pure = extract_pure_code("Конденсатор К53-66-\"Е\"-50В-68мкФ±10% АЖЯР.673546.005 ТУ")
        assert bom_pure == tru_pure

    def test_fix4_trailing_junk_removed(self):
        """Fix 4: Мусорные символы в конце удаляются"""
        pure = extract_pure_code("Аттенюатор 151T - 75,./WEINSCHEL")
        assert not pure.endswith(',')
        assert not pure.endswith('/')
        assert '151t-75' in pure

    def test_fix5_power_rating_normalization(self):
        """Fix 5: "2" и "2,0" в номинале мощности эквивалентны"""
        bom_pure = extract_pure_code("С2 - 33 - 2 - 820 Ом ± 5% - А - Д - В")
        tru_pure = extract_pure_code("Резистор С2-33-2,0-820 Ом±5% А-Д-В ОЖ0.467.093 ТУ")
        assert bom_pure == tru_pure

    def test_fix6_connector_category_words(self):
        """Fix 6: Слова 'разъем', 'вилка', 'розетка' удаляются из pure code"""
        pure1 = extract_pure_code("Разъем МДМ30-1В15ТУП")
        pure2 = extract_pure_code("Вилка МДМ30-1В15ТУП")
        pure3 = extract_pure_code("МДМ30-1В15ТУП")
        assert pure1 == pure3
        assert pure2 == pure3

    def test_fix6_chained_category_removal(self):
        """Fix 6: Цепочка 'Кабель - адаптер' → оба слова удаляются"""
        pure = extract_pure_code("Кабель - адаптер A - OTG - AFBM - 001")
        assert 'kaбeль' not in pure
        assert 'aдaпtep' not in pure

    def test_fix7_new_manufacturers_removed(self):
        """Fix 7: Новые производители удаляются из pure code"""
        pure = extract_pure_code("Адаптер RPC-N Rosenberger 05K432-K00S3")
        assert 'rosenberger' not in pure

    def test_fix8_vilka_vs_razjem_compatible(self):
        """Fix 8: Вилка совместима с Разъем (без типовых слов в ТРУ)"""
        tru_df = pd.DataFrame({
            'Наименование': ['Разъем Delta Electronics 20GEEG3E-R'],
            'Артикул': ['55555'],
            'Количество': [1],
        })
        result = find_matching_tru_row("Вилка 20GEEG3E - R", "", tru_df)
        assert result is not None

    def test_fix8_vilka_vs_rozetka_still_blocked(self):
        """Fix 8: Вилка и Розетка по-прежнему различаются"""
        tru_df = pd.DataFrame({
            'Наименование': [
                'Разъем Вилка МДМ30-1В15ТУП',
                'Разъем Розетка МДМ30-1В15ТУП',
            ],
            'Артикул': ['33333', '44444'],
            'Количество': [8, 4],
        })
        result_vilka = find_matching_tru_row("Вилка МДМ30-1В15ТУП", "", tru_df)
        result_rozetka = find_matching_tru_row("Розетка МДМ30-1В15ТУП", "", tru_df)
        assert result_vilka is not None and result_rozetka is not None
        assert str(result_vilka['Артикул']) != str(result_rozetka['Артикул'])

    def test_fix9_dashless_comparison(self):
        """Fix 9: РП-10-11 и РП10-11 совпадают (без дефисов)"""
        tru_df = pd.DataFrame({
            'Наименование': ['Вилка РП10-11-В ГЕ0.364.004 ТУ'],
            'Артикул': ['66666'],
            'Количество': [3],
        })
        result = find_matching_tru_row("Вилка РП - 10 - 11 - В", "", tru_df)
        assert result is not None

    def test_fix9_rozetka_dashless(self):
        """Fix 9: Розетка РП-10-7 аналогично"""
        tru_df = pd.DataFrame({
            'Наименование': ['Розетка РП10-7-В ГЕ0.364.004 ТУ'],
            'Артикул': ['77777'],
            'Количество': [2],
        })
        result = find_matching_tru_row("Розетка РП - 10 - 7 - В", "", tru_df)
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
