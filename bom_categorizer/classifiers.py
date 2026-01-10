# -*- coding: utf-8 -*-
"""
Классификация компонентов по категориям

Основная функция: classify_row()
Классификация основана на:
- Референсных обозначениях (R, C, L, U и т.д.)
- Ключевых словах в описании
- Номиналах компонентов
- Производителях и типах
"""

import re
from typing import Any, Optional

from .utils import has_any, RESISTOR_VALUE_RE, CAP_VALUE_RE, IND_VALUE_RE
from .component_database import get_component_category


def classify_row(
    ref: Optional[str], 
    description: Optional[str], 
    value: Optional[str], 
    partname: Optional[str], 
    strict: bool, 
    source_file: Optional[str] = None, 
    note: Optional[str] = None,
    group_type: Optional[str] = None
) -> str:
    """
    Классифицирует компонент по категории
    
    Args:
        ref: Позиционное обозначение (reference designator)
        description: Описание компонента
        value: Номинал компонента
        partname: Номер детали/артикул
        strict: Строгий режим классификации
        source_file: Имя исходного файла
        note: Примечания (ТУ, производитель)
        group_type: Тип компонента из группового заголовка
        
    Returns:
        Название категории (ключ)
    """
    def to_text(x: Any) -> str:
        if x is None:
            return ""
        try:
            import math
            if isinstance(x, float) and math.isnan(x):
                return ""
        except Exception:
            pass
        s = str(x)
        return s.strip()

    ref = to_text(ref)
    desc = to_text(description)
    val = to_text(value)
    part = to_text(partname)
    src_file = to_text(source_file)
    note_text = to_text(note)
    group_type_text = to_text(group_type)  # Тип из заголовка группы (DOCX)

    # Create text blob early for use in reference-based checks (теперь включая note и group_type!)
    # ВАЖНО: group_type помогает определить категорию по заголовку (например, "Чип катушки индуктивности")
    text_blob = " ".join([desc, val, part, note_text, group_type_text])
    text_blob_lower = text_blob.lower()

    # Refdes first where reliable
    ref_prefix = ref.split(" ")[0].upper() if ref else ""
    ref_prefix = re.sub(r"\d.*$", "", ref_prefix)  # take letters before digits

    # ===================================================================
    # САМЫЙ ВЫСШИЙ ПРИОРИТЕТ: Служебные записи (НЕ ИВП)
    # Ошибочные заголовки, текст из рамок документов, подписи, штампы и т.д.
    # ИСКЛЮЧЕНИЕ: Замены и подборы (у них нет ref, но они - реальные компоненты!)
    # ===================================================================
    
    # Проверяем, является ли это заменой или подбором (по source_file)
    is_replacement_or_podbor = False
    if src_file:
        # Проверяем как полные, так и сокращенные формы
        is_replacement_or_podbor = (
            '(замена)' in src_file or '(подбор)' in src_file or
            '(зам ' in src_file or '(п/б ' in src_file
        )
    
    # Проверяем отсутствие позиционного обозначения и наличие служебных слов
    # НО НЕ для замен и подборов!
    if not is_replacement_or_podbor and (not ref or not ref.strip()):
        # Служебные записи из рамок документов
        service_patterns = [
            'изм.', 'изменен', 'заменен', 'аннулирован',
            'лист регистрации', 'регистрации изменений',
            'всего листов', 'номер докум', 'подпись', 'подп.',
            'входящий', 'сопроводитель', 'копировал', 'формат',
            'дата', 'проверил', 'утвердил', 'н. контр', 'разраб.',
            'лит.', 'масса', 'масштаб', 'лист', 'докум.', 'документ',
            'перв. примен', 'справ.', 'справочн', 'спецификация',
            'перечень элементов', 'ведомость', 'штамп',
            'декада', 'год', 'месяц',
            'переменные данные', 'для исполнений'  # Добавлено
        ]
        
        if any(pattern in text_blob_lower for pattern in service_patterns):
            return "non_bom"
    
        # Очень короткие строки без позиционного обозначения - скорее всего мусор
        # НО НЕ для замен и подборов!
        if len(text_blob.strip()) < 10:
            return "non_bom"
    
        # Строки, состоящие только из чисел или спецсимволов
        if text_blob.strip() and re.fullmatch(r'[\d\s\-\.,:;/\\]+', text_blob.strip()):
            return "non_bom"

    # ===================================================================
    # САМЫЙ ВЫСШИЙ ПРИОРИТЕТ: База данных компонентов
    # Проверяем точное соответствие наименования в базе данных
    # ===================================================================
    if desc:
        db_category = get_component_category(desc)
        if db_category:
            # print(f"   🎯 Найдено в базе: {desc} → {db_category}")  # Раскомментировать для отладки
            return db_category
    
    # Также проверяем partname
    if part:
        db_category = get_component_category(part)
        if db_category:
            # print(f"   🎯 Найдено в базе: {part} → {db_category}")  # Раскомментировать для отладки
            return db_category

    # ===================================================================
    # НАИВЫСШИЙ ПРИОРИТЕТ: НАШИ РАЗРАБОТКИ
    # Любой компонент с номерами 195-, АМФИ, ГВАТ, деX. - это наши разработки
    # Это могут быть платы, блоки, модули, вентили СВЧ и т.д.
    # ВАЖНО: Если название НАЧИНАЕТСЯ с АМФИ/ГВАТ/деX. - это ВСЕГДА наши разработки!
    # Стандартные ЭРИ (резисторы, конденсаторы) с кодом АМФИ в середине - могут быть покупными
    # ===================================================================
    
    # КРИТИЧЕСКИ ВАЖНО: Если наименование НАЧИНАЕТСЯ с "ГВАТ"/"ГВАТ.", "АМФИ"/"АМФИ." или "де"/"деX." - это ВСЕГДА наши разработки!
    # Независимо от типа компонента (даже если это резистор, конденсатор и т.д.)
    # Это относится к оригинальным, подборным и заменяемым компонентам
    desc_upper = to_text(description).upper().strip()
    desc_lower = to_text(description).lower().strip()
    
    if desc_upper.startswith("ГВАТ") or desc_upper.startswith("ГВАТ."):
        return "our_developments"
    
    if desc_upper.startswith("АМФИ") or desc_upper.startswith("АМФИ."):
        return "our_developments"
    
    # Проверка децимальных номеров в начале названия (де4.835.001 и т.д.)
    # Паттерн: название начинается с "де" + цифра + точка (например, де4.)
    if re.match(r"^де\d+\.", desc_lower):
        return "our_developments"
    
    # Проверка децимальных номеров в любом месте текста (де4.835.001 и т.д.)
    # Паттерн: "де" + цифра + точка (например, де4.)
    if re.search(r"де\d+\.", text_blob_lower):
        return "our_developments"
    
    if has_any(text_blob, [
        "195-9530", "195-", "амфи.", "амфи ", "гват.", "гват ", "игнд.", "игнд ",
        "шск-м", "плата контроллера шск", "плата преобразователя уровней",
        "бз шск-м", "бф шск-м", "наша разработ", "собственной разработ"
    ]):
        # Исключаем ТОЛЬКО стандартные ЭРИ и КРЕПЕЖ
        # (резисторы, конденсаторы с кодом АМФИ - это покупные, Шайба ОСТ - это крепеж)
        standard_components = ["резистор", "конденсатор", "дроссель", "индуктивност", "микродроссель",
                               "винт", "гайка", "шайба", "болт", "заклёпка", "заклепка"]
        is_standard_component = any(comp in text_blob_lower for comp in standard_components)
        
        if not is_standard_component:
            return "our_developments"

    # Доп. правило: децимальные номера "де<цифра>" считаем нашими разработками
    # (но только если есть цифра после "де", чтобы не ловить обычные слова)
    if re.search(r"\bде\s*\d+", text_blob_lower):
        return "our_developments"
    
    # ===================================================================
    # НАИВЫСШИЙ ПРИОРИТЕТ: Явные типы компонентов (ВАЖНЕЕ кода АМФИ!)
    # Если явно указан тип (резистор, конденсатор, микродроссель и т.д.),
    # то классифицируем по типу, ДАЖЕ если есть код АМФИ
    # ===================================================================
    
    # Микродроссель/Дроссель - в индуктивности (даже с кодом АМФИ)
    if has_any(text_blob, ["микродроссель", "дроссель", "индуктивность", "сердечник"]):
        return "inductors"
    
    # Резистор - в резисторы (даже с кодом АМФИ)
    if has_any(text_blob, ["резистор ", " резистор"]):
        return "resistors"
    
    # Конденсатор - в конденсаторы (даже с кодом АМФИ)
    if has_any(text_blob, ["конденсатор ", " конденсатор"]):
        return "capacitors"
    
    # Предохранитель - в другие (даже с кодом АМФИ)
    if has_any(text_blob, ["предохранитель", "fuse", "fuzetec"]):
        return "others"
    
    # ===================================================================
    # ВЫСШИЙ ПРИОРИТЕТ: Явное указание типа компонента в описании
    # Если в описании есть явные слова-маркеры категории - это главное!
    # ===================================================================
    
    # Резисторы (НО НЕ с кодом ГВАТ или АМФИ - это наши разработки!)
    if has_any(text_blob, ["резистор", "resistor", "сопротивлен"]):
        # Исключаем ГВАТ и АМФИ - это наши разработки!
        if not has_any(text_blob, ["гват.", "гват ", "амфи.", "амфи "]):
            return "resistors"
    
    # Конденсаторы (но НЕ делители мощности!)
    if has_any(text_blob, ["конденсатор", "capacitor"]):
        # Исключаем делители мощности - они идут в dev_boards
        # Проверяем с одним и двумя пробелами (в реальных данных могут быть лишние пробелы)
        if not has_any(text_blob, ["делитель мощности", "делитель  мощности", "power divider"]):
            return "capacitors"
    
    # Микросхемы (но НЕ оптические модули и модули связи с "ic" в названии производителя!)
    # ВАЖНО: Аттенюаторы теперь НЕ классифицируются как микросхемы - они идут в СВЧ модули!
    if has_any(text_blob, ["микросхем", "интегральная схема"]):
        return "ics"
    # Производители микросхем: Analog Devices (HMC), Mini-Circuits (РАТ, PE)
    # ВАЖНО: "pat - " с пробелом для нормализованных названий типа "PAT - 15+"
    if has_any(text_blob, ["hmc", "рат-", "pat-", "pat - ", "рат - ", "pe43", "pe44"]):
        return "ics"
    # Проверяем "ic" только если НЕТ оптических маркеров или модулей связи
    if has_any(text_blob, ["ic ", " ic", "chip ", " chip"]):
        if not has_any(text_blob, ["оптич", "optical", "photonic", "передающий", "приемный", "electronic", 
                                    "quantic", "ebyte", "nt1"]):
            return "ics"
    
    # Дроссели/Индуктивности
    if has_any(text_blob, ["дроссель", "микродроссель", "inductor", "катушка индуктивности", "индуктивность", "сердечник", "core", "катушки индуктивности"]):
        return "inductors"
    
    # Полупроводники (диоды, транзисторы, стабилитроны, оптроны)
    if has_any(text_blob, ["диод ", " диод", "diode", "транзистор", "transistor", "стабилитрон", "оптрон", "optocoupler"]):
        return "semiconductors"
    
    # Разъемы
    if has_any(text_blob, ["разъем", "connector", "вилка ", "розетка ", "socket", "plug", "переход "]):
        return "connectors"
    
    # ===================================================================
    # КРИТИЧЕСКИ ВАЖНО: Оптические компоненты проверяем ПЕРЕД кабелями!
    # Любой компонент со словом "оптическ" должен попасть в optics
    # ===================================================================
    
    # Оптические модули и компоненты
    if has_any(text_blob, [
        "оптический модуль", "optical module", "передающий оптический", "приемный оптический",
        "оптический аттенюатор", "аттенюатор оптический", "optical attenuator",
        "mp2320", "mp2220", "fc/apc", "fc/upc", "соединительный оптический",
        "оптоволокон", "fiber optic", "мвол", "мвок", "линия многоканальная задержки",
        "коммутатор оптический", "оптический коммутатор", "optical switch",
        "кабель оптический", "оптический кабель", "optical cable"
    ]):
        return "optics"
    
    # Любой компонент с "оптическ" в начале/конце слова -> optics
    # (оптический, оптическая, оптическое, оптические)
    if "оптическ" in text_blob or "optical" in text_blob:
        return "optics"
    
    # Кабели (НЕ оптические - они уже обработаны выше!)
    if has_any(text_blob, ["кабель", "cable", "провод", "wire", "патч-корд", "патч корд", "кабельн", "сборка кабельная", "шлейф"]):
        return "cables"
    
    # Модули питания
    if has_any(text_blob, ["модуль питания", "модуль электропитания", "электропитания модуль", "power module", "преобразователь питания", "dc/dc", "dc-dc"]):
        return "power_modules"

    # PRIORITY 1: Check context-specific categories FIRST (before generic prefixes)
    # Check if this is a board/PCB file (self-reference: description is just the filename)
    if src_file and desc:
        file_base = src_file.split('/')[-1].split('\\')[-1].rsplit('.', 1)[0].lower()
        desc_lower = desc.lower()
        
        component_keywords = ['резистор', 'конденсатор', 'микросхема', 'разъем', 'диод', 'индуктор', 'дроссель',
                             'транзистор', 'стабилитрон', 'генератор', 'вилка', 'розетка', 'кабель',
                             'делитель', 'аттенюатор', 'вентиль', 'усилитель', 'смеситель', 'фильтр']
        is_component = any(kw in desc_lower for kw in component_keywords)
        
        if not is_component and file_base in desc_lower.replace('.xlsx', '').replace('.xls', ''):
            desc_clean = desc_lower.replace('.xlsx', '').replace('.xls', '').replace(' ', '').replace('_', '')
            file_clean = file_base.replace(' ', '').replace('_', '')
            if desc_clean == file_clean or desc_clean.startswith(file_clean) or file_clean in desc_clean:
                return "our_developments"
    
    # ВАЖНО: Проверяем специфичные компоненты ПЕРЕД широкими категориями
    # Адаптеры в разъемы
    if has_any(text_blob, ["адаптер", "adapter"]):
        if not has_any(text_blob, ["fc/", "sc/", "lc/", "оптическ", "optical", "fiber"]):
            return "connectors"
    
    # СВЧ компоненты (аттенюаторы, делители, ответвители)
    # ВАЖНО: ВСЕ аттенюаторы (не оптические) попадают в СВЧ модули!
    if has_any(text_blob, ["аттенюатор", "attenuator"]):
        # ВАЖНО: Только НЕ-оптические компоненты!
        if not has_any(text_blob, ["оптич", "optical", "fc/apc", "fc/upc", "fiber"]):
            return "rf_modules"
    
    # Другие СВЧ компоненты от специфичных производителей
    if has_any(text_blob, ["делитель мощности", "делитель  мощности", "power divider", 
                           "ответвитель направленный", "ограничитель", "линия задержек"]):
        # ВАЖНО: Только НЕ-оптические компоненты!
        if not has_any(text_blob, ["оптич", "optical", "fc/apc", "fc/upc", "fiber"]):
            if has_any(text_blob, ["qualwave", "mini-circuits", "api technologies", "weinschel", "a-info", "gigabaudics", 
                                   "quantic pmi", "quantic", "pmi", "jfw", "umcc"]):
                return "rf_modules"
    
    # Оборудование RITTAL всегда в "Другие"
    if has_any(text_blob, ["rittal"]):
        return "others"
    
    # Нагрузка согласованная в "СВЧ модули"
    if has_any(text_blob, ["нагрузка согласованная", "согласованная нагрузка", "matched load"]):
        return "rf_modules"
    
    # Вентили СВЧ/ВЧ в "СВЧ модули" (circulator, isolator)
    # Также добавляем ВЧ-переключатели и MTS-18 сюда
    if has_any(text_blob, ["вентиль свч", "вентиль вч", "circulator", "isolator", "прибор фвк", "прибор фквн", "фвк3-", "фквн3-",
                           "вч-переключатель", "rf switch", "switch rf", "zaswa", "msp2ta",
                           "mts-18", "mts 18", "mts18", "mts - 18"]):
        return "rf_modules"
    
    # Вентили с кодами ГВАТ (наши разработки СВЧ) в "СВЧ модули"
    if has_any(text_blob, ["вентиль"]) and has_any(text_blob, ["гват"]):
        return "rf_modules"
    
    # MTS-18XL-B (Mechanical Transfer Switch) -> Moved to RF Modules above
    # if has_any(text_blob, ["mts-18xl", "mts-18", "mts 18", "mts18"]):
    #     return "others"

    # Dev boards / evaluation boards / коммутаторы / модули связи
    if has_any(text_blob, ["плата инструментальная", "evaluation board", "dev board", "отладочная плата", "плата 117212",
                           "коммутатор", "nt1", "модуль связи"]):
        if has_any(text_blob, ["qualwave", "api technologies", "weinschel", "hittite", "planet", "коммутатор", 
                               "ebyte", "chengdu ebyte", "nt1"]):
            return "dev_boards"
    
    # Широкая проверка оптических компонентов (если не попали выше)
    if has_any(text_blob, ["оптич", "optical"]):
        return "optics"
    
    # Optical modules with U prefix - check before "U" prefix for ICs
    if ref and ref_prefix.startswith("U"):
        if has_any(text_blob, ["оптический", "optical", "передающий", "приемный"]):
            return "optics"
    
    # ===================================================================
    # ГРУППOВЫЕ ЗАГОЛОВКИ: Тип компонента из заголовка документа
    # Этот приоритет ВЫШЕ чем определение по префиксу reference!
    # Если в документе был явный заголовок "Микросхемы", то все элементы
    # в этом разделе должны классифицироваться как микросхемы, даже если
    # у них префикс D, V, или другой нестандартный префикс.
    # ===================================================================
    group_type_text = to_text(group_type)
    if group_type_text:
        group_lower = group_type_text.lower()
        if 'микросхем' in group_lower:
            return "ics"
        elif 'резистор' in group_lower:
            return "resistors"
        elif 'конденсатор' in group_lower:
            return "capacitors"
        elif 'дроссел' in group_lower or 'индуктивност' in group_lower:
            return "inductors"
        elif 'разъем' in group_lower or 'разьем' in group_lower:
            return "connectors"
        elif 'диод' in group_lower and 'светодиод' not in group_lower:
            return "semiconductors"
        elif 'транзистор' in group_lower:
            return "semiconductors"
        elif 'стабилитрон' in group_lower:
            return "semiconductors"
        elif 'светодиод' in group_lower:
            return "semiconductors"
        elif 'кабел' in group_lower or 'провод' in group_lower:
            return "cables"
        elif 'трансформатор' in group_lower:
            return "inductors"
    
    # PRIORITY 2: Heuristics by ref (only if we have a real ref column)
    if ref:
        if ref_prefix.startswith("R"):
            return "resistors"
        if ref_prefix.startswith("C"):
            return "capacitors"
        if ref_prefix.startswith("L"):
            return "inductors"
        # Российские обозначения микросхем: DD, DA, D (цифровые и аналоговые)
        # DD - цифровые микросхемы, DA - аналоговые, D - цифровые (старое обозначение)
        # U - также микросхемы, НО проверяем оптические модули
        if ref_prefix.startswith("U"):
            # Проверяем оптические модули (передающие, приемные)
            if has_any(text_blob, [
                "оптический модуль", "optical module", 
                "передающий оптический", "приемный оптический",
                "mp2320", "mp2220", "sfp", "qsfp"
            ]):
                return "optics"
            # Иначе это микросхема
            return "ics"
        if ref_prefix.startswith(("DD", "DA", "IC")):
            return "ics"
        # Префикс "D" по умолчанию - микросхемы (в российской практике)
        # Исключение: если явно указано что это диод, стабилитрон и т.д.
        if ref_prefix.startswith("D") and not ref_prefix.startswith(("DD", "DA")):
            # Проверяем, не является ли это явно диодом/стабилитроном
            if has_any(text_blob, ["диод", "diode", "стабилитрон", "zener", "выпрямител", "светодиод", "led"]):
                return "semiconductors"
            # Если есть код ТУ с типичным форматом микросхемы или явные признаки микросхемы - это микросхема
            if has_any(text_blob, ["ту", "tu", "аеяр", "аенв", "аляр", "sn74", "ad9", "lmk", "hmc", "ti", "texas instruments", "analog devices"]):
                return "ics"
            # По умолчанию D* считаем микросхемой
            return "ics"
        if ref_prefix.startswith(("J", "P", "K", "XT", "XS", "XP", "XW", "JTAG")):
            return "connectors"
        # Prefix "X" - нужна проверка (может быть разъем или другое)
        if ref_prefix.startswith("X"):
            # Если это разъем, адаптер - в connectors
            if has_any(text_blob, ["разъем", "connector", "адаптер", "adapter", "вилка", "розетка", "jack", "plug", "socket"]):
                return "connectors"
            # Иначе тоже в connectors (по умолчанию для X)
            return "connectors"
        # Prefix "G" for generators
        if ref_prefix.startswith("G"):
            # Если это модуль питания - в power_modules
            if has_any(text_blob, ["модуль питания", "power module", "шск-м"]):
                return "power_modules"
            # Иначе в others (генераторы, кварцы и т.д.)
            return "others"
        # Prefix "F" or "FU" for fuses (предохранители)
        if ref_prefix.startswith(("F", "FU")):
            return "others"
        # Prefix "A" or "А" (latin or cyrillic) - умная логика
        # Проверяем наименование для точной классификации
        if ref_prefix.startswith(("A", "А")):
            # 1. Оптические компоненты (линии задержки, кабели, модули)
            if has_any(text_blob, [
                "мволз", "линия задержки", "оптический", "optical", 
                "fc/apc", "fc/upc", "sc/apc", "lc/apc",
                "кабель соединительный оптический", "патч-корд оптич"
            ]):
                return "optics"
            # 2. Наши разработки (платы с нашими номерами или АМФИ/ГВАТ/ИГНД/деX...)
            if has_any(text_blob, [
                "195-9530", "195-", "гват", "амфи", "игнд",
                "плата контроллера", "плата шск", "шск-м",
                "наша разработка", "собственной разработ"
            ]):
                return "our_developments"
            # 3. Коммутаторы оптические
            if has_any(text_blob, ["коммутатор", "мвок"]):
                return "optics"
            # 4. Аттенюаторы (оптические или СВЧ)
            if has_any(text_blob, ["аттенюат", "ослабител", "attenuator"]):
                # Проверяем, оптический ли это аттенюатор
                if has_any(text_blob, ["оптич", "optical", "fc/apc", "fc/upc", "fiber"]):
                    return "optics"
                else:
                    # СВЧ/электрические аттенюаторы -> СВЧ модули
                    return "rf_modules"
            # 5. По умолчанию для A* без явных признаков → dev_boards
            return "dev_boards"
        # Prefix "WS" and "WU" - specific RF module prefixes (check BEFORE "W")
        if ref_prefix.startswith("WS"):
            return "rf_modules"
        if ref_prefix.startswith("WU"):
            return "rf_modules"
        # Prefix "W" often used for RF modules (check AFTER WS/WU)
        if ref_prefix.startswith("W"):
            # Всегда в rf_modules для W-префиксов (корректоры, усилители, вентили, аттенюаторы и т.д.)
            # Типичные СВЧ компоненты с префиксом W
            if has_any(text_blob, [
                "свч", "вч", "rf", "вентиль", "circulator", "isolator",
                "линия задержек", "delay line", "усилитель", "amplifier", "lna",
                "делитель", "сумматор", "splitter", "combiner", "divider",
                "корректор ачх", "equalizer", "аттенюат", "attenuator",
                "фазовращатель", "phase shifter", "детектор", "detector",
                "ограничитель", "limiter", "смеситель", "mixer"
            ]):
                return "rf_modules"
            # Если нет явных маркеров, но префикс W - всё равно в rf_modules (по умолчанию)
            return "rf_modules"
        # Prefix "H" for indicators/LEDs
        if ref_prefix.startswith("H"):
            return "semiconductors"
        # Prefix "VD" for diodes and zener diodes (Russian standard)
        if ref_prefix.startswith("VD"):
            return "semiconductors"
        # Prefix "V", "VT", "Q" for transistors
        if ref_prefix.startswith(("V", "VT", "Q")):
            if has_any(text_blob, ["микросхем", "микросхема"]):
                return "ics"
            return "semiconductors"
        # Prefix "S" for switches/buttons/optical switches
        if ref_prefix.startswith("S"):
            # Проверяем, не оптический ли это коммутатор
            if has_any(text_blob, ["коммутатор", "мвок", "optical switch"]):
                return "optics"
            # Обычные переключатели, кнопки
            if has_any(text_blob, ["переключ", "тумблер", "кнопка", "switch", "button", "toggle"]):
                return "others"

    # Russian and English keywords
    if RESISTOR_VALUE_RE.search(text_blob) or has_any(text_blob, ["резист", "resistor"]):
        return "resistors"

    if CAP_VALUE_RE.search(text_blob) or has_any(text_blob, ["конденс", "capacitor", "tantalum", "ceramic", "к10-", "к53-"]):
        # Исключаем делители мощности (могут содержать номиналы, похожие на емкость)
        if not has_any(text_blob, ["делитель мощности", "делитель  мощности", "power divider"]):
            return "capacitors"

    if IND_VALUE_RE.search(text_blob) or has_any(text_blob, ["дросс", "индукт", "inductor", "ferrite", "феррит", "катушка", "choke"]):
        return "inductors"
    
    # Предохранители - check BEFORE semiconductors and ICs
    if has_any(text_blob, ["предохранитель", "fuse", "fuzetec"]):
        return "others"
    
    # Semiconductors (диоды, транзисторы, стабилитроны, оптроны) - check BEFORE ICs
    if has_any(text_blob, [
        "диод", "стабилитрон", "транзистор", "оптрон", "оптопар", "2с630", "2т630", "индикатор", 
        "led ", "svetodiod", "indicator", "transistor", "optocoupler", "thyristor", "тиристор",
        "mosfet", "igbt", "triac", "симистор", "полевой транзистор", "биполярный транзистор"
    ]):
        return "semiconductors"

    if has_any(text_blob, [
        "микросхем", " ic", "mcu", "контроллер", "процессор", "оп-амп", "op-amp", "opamp", "adc", "dac", "fpga",
        "asic", "драйвер ", "компаратор", "стабил", "регулятор", "transceiver", "sn74", "ti ", "stm32", "lmk", "ad9"
    ]):
        return "ics"

    if has_any(text_blob, [
        "разъем", "разъём", "connector", "header", "socket", "rj45", "rj11", "sma", "bnc", "terminal", "клемм",
        "штырь", "pin header", "fpc", "ffc", "din", "dc jack", "barrel", "штекер", "вилка", "розетка", "d-sub", "harting"
    ]):
        return "connectors"

    if has_any(text_blob, [
        "отладоч", " dev board", "evaluation", "eval", "nucleo", "arduino", "raspberry",
        "esp32", "stm32 nucleo", "breakout", "fmc", "carrier", "ultrazed", "microzed", "picozed", "zedboard",
        "zynq", "som ", "system on module", "voyager", "tinypilot", "плата инструментальная", "evaluation board",
        "development board", "отладочная плата", "aes-zu"
    ]):
        return "dev_boards"

    # New categories
    if has_any(text_blob, [
        "оптичес", "лазер", "оптопара", "led ", "светодиод", "fiber", "оптоволок", "sfp", "qsfp", "transceiver module",
        "аттенюат", "ослабител", "fc/apc", "fc/upc", "sc/apc", "lc/apc", "pigtail", "патч-корд оптич"
    ]):
        return "optics"

    if has_any(text_blob, [
        "свч", "вч ", "вч-", "rf ", "microwave", "mini-circuits", "planar monolithics", "pmi", "ghz", "lna", "rf amp",
        "линия задержек", "delay line", "делитель мощности", "сумматор", "splitter", "combiner", "усилител",
        "polaris", "gigabaudics", "etl systems", "vat-", "zx60", "pne-l", "ответвитель", "coupler", "фазовращатель",
        "phase shifter", "детектор", "detector", "ограничитель", "limiter", "корректор ачх", "equalizer", "qpd", "power divider"
    ]):
        # НО! Не Qualwave аттенюаторы QFA
        if has_any(text_blob, ["аттенюатор qfa", "qfa"]) and not has_any(text_blob, ["qpd"]):
            return "others"
        return "rf_modules"

    if has_any(text_blob, [
        "кабель", "cable", "шлейф", "провод", "wire", "patch cord", "патч-корд", "патч корд", 
        "jumper", "кабельн", "сборка кабельная"
    ]):
        return "cables"

    if has_any(text_blob, [
        "модуль питания", "power module", "dc-dc", "ac-dc", "buck", "boost", "источник питания", "блок питания", "psu",
        "converter", "электропитания", "мдм10", "мдм20", "мдм30", "мдм50", "мдм60", "мдм100", "мдм160", "мдм600",
        "маа20", "маа400", "маа600"
    ]):
        return "power_modules"

    # OTHER general hardware to bucket into 'others'
    if has_any(text_blob, [
        "rittal", "шкаф", "станция", "полка", "кронштейн", "ролик", "болт", "гайка", "шайба", "клавиатура", "моноблок",
        "кабель", "клеммная", "корпус", "шасси", "стеллаж", "стойка", "провод", "розетка", "вентилятор", "генератор",
        "предохранитель", "держател", "зажим", "fuzetec", "реле", "relay", "тумблер", "фильтр", "filter",
        "сетка защитная", "коммутатор", "switch", "переход", "adapter", "линия задержки", "delay line",
        "кварц", "quartz", "вставка плавкая"
    ]):
        return "others"

    # In strict mode, avoid loose matches
    return "unclassified"
