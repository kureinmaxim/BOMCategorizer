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
from typing import Optional, Any

from .utils import has_any, RESISTOR_VALUE_RE, CAP_VALUE_RE, IND_VALUE_RE


def classify_row(
    ref: Optional[str], 
    description: Optional[str], 
    value: Optional[str], 
    partname: Optional[str], 
    strict: bool, 
    source_file: Optional[str] = None, 
    note: Optional[str] = None
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
        note: Примечания
        
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

    # Create text blob early for use in reference-based checks (теперь включая note!)
    text_blob = " ".join([desc, val, part, note_text])

    # Refdes first where reliable
    ref_prefix = ref.split(" ")[0].upper() if ref else ""
    ref_prefix = re.sub(r"\d.*$", "", ref_prefix)  # take letters before digits

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
    # ВТОРОЙ ПРИОРИТЕТ: Наши разработки (платы, модули и т.д.)
    # Компоненты с кодами АМФИ, которые НЕ являются стандартными ЭРИ
    # ===================================================================
    if has_any(text_blob, ["амфи.", "амфи ", "мвок", "наша разработ", "собственной разработ", 
                           "шск-м", "плата контроллера шск", "плата преобразователя уровней"]):
        return "our_developments"

    # ===================================================================
    # ВЫСШИЙ ПРИОРИТЕТ: Явное указание типа компонента в описании
    # Если в описании есть явные слова-маркеры категории - это главное!
    # ===================================================================
    
    # Резисторы
    if has_any(text_blob, ["резистор", "resistor", "сопротивлен"]):
        return "resistors"
    
    # Конденсаторы (но НЕ делители мощности!)
    if has_any(text_blob, ["конденсатор", "capacitor"]):
        # Исключаем делители мощности - они идут в dev_boards
        # Проверяем с одним и двумя пробелами (в реальных данных могут быть лишние пробелы)
        if not has_any(text_blob, ["делитель мощности", "делитель  мощности", "power divider"]):
            return "capacitors"
    
    # Микросхемы (но НЕ оптические модули и модули связи с "ic" в названии производителя!)
    # Исключаем компоненты с явными маркерами оптики или модулей связи
    if has_any(text_blob, ["микросхем", "интегральная схема"]):
        return "ics"
    # Проверяем "ic" только если НЕТ оптических маркеров или модулей связи/аттенюаторов
    if has_any(text_blob, ["ic ", " ic", "chip ", " chip"]):
        if not has_any(text_blob, ["оптич", "optical", "photonic", "передающий", "приемный", "electronic", 
                                    "quantic", "ebyte", "nt1", "аттенюатор", "attenuator"]):
            return "ics"
    
    # Дроссели/Индуктивности
    if has_any(text_blob, ["дроссель", "микродроссель", "inductor", "катушка индуктивности", "индуктивность", "сердечник", "core"]):
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
        "оптоволокон", "fiber optic", "мвол", "линия многоканальная задержки",
        "коммутатор оптический", "оптический коммутатор", "optical switch",
        "кабель оптический", "оптический кабель", "optical cable"
    ]):
        return "optics"
    
    # Любой компонент с "оптическ" в начале/конце слова -> optics
    # (оптический, оптическая, оптическое, оптические)
    if "оптическ" in text_blob or "optical" in text_blob:
        return "optics"
    
    # Кабели (НЕ оптические - они уже обработаны выше!)
    if has_any(text_blob, ["кабель", "cable", "провод ", "wire ", "патч-корд", "патч корд"]):
        return "cables"
    
    # Модули питания
    if has_any(text_blob, ["модуль питания", "power module", "преобразователь питания", "dc/dc", "dc-dc"]):
        return "power_modules"

    # PRIORITY 1: Check context-specific categories FIRST (before generic prefixes)
    # Check if this is a board/PCB file (self-reference: description is just the filename)
    if src_file and desc:
        file_base = src_file.split('/')[-1].split('\\')[-1].rsplit('.', 1)[0].lower()
        desc_lower = desc.lower()
        
        component_keywords = ['резистор', 'конденсатор', 'микросхема', 'разъем', 'диод', 'индуктор', 'дроссель',
                             'транзистор', 'стабилитрон', 'генератор', 'вилка', 'розетка', 'кабель']
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
    
    # СВЧ компоненты (аттенюаторы, делители, ответвители) от специфичных производителей
    if has_any(text_blob, ["аттенюатор", "attenuator", "делитель мощности", "делитель  мощности", "power divider", 
                           "ответвитель направленный", "ограничитель", "линия задержек"]):
        # ВАЖНО: Только НЕ-оптические компоненты!
        if not has_any(text_blob, ["оптич", "optical", "fc/apc", "fc/upc", "fiber"]):
            if has_any(text_blob, ["qualwave", "mini-circuits", "api technologies", "weinschel", "a-info", "gigabaudics", 
                                   "quantic pmi", "quantic", "pmi", "jfw", "umcc"]):
                return "rf_modules"
            # Аттенюаторы без явного производителя также идут в rf_modules (СВЧ компоненты)
            # НО! Только если есть явные маркеры СВЧ (BW, VAT, ZX76 и т.д.)
            if has_any(text_blob, ["bw - ", "bw-", " vat - ", "vat-", "zx76", "zx60"]):
                return "rf_modules"
    
    # Оборудование RITTAL всегда в "Другие"
    if has_any(text_blob, ["rittal"]):
        return "others"
    
    # Нагрузка согласованная в "СВЧ модули"
    if has_any(text_blob, ["нагрузка согласованная", "согласованная нагрузка", "matched load"]):
        return "rf_modules"
    
    # Вентили в индуктивности
    if has_any(text_blob, ["вентиль свч", "вентиль вч", "circulator", "isolator", "ферритов", "прибор фвк", "прибор фквн", "фвк3-", "фквн3-"]):
        return "inductors"
    
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
    
    # PRIORITY 2: Heuristics by ref (only if we have a real ref column)
    if ref:
        if ref_prefix.startswith("R"):
            return "resistors"
        if ref_prefix.startswith("C"):
            return "capacitors"
        if ref_prefix.startswith("L"):
            return "inductors"
        if ref_prefix.startswith(("U", "DD", "DA", "IC")):
            return "ics"
        if ref_prefix.startswith(("J", "X", "P", "K", "XS", "XP", "JTAG")):
            return "connectors"
        # Prefix "A" or "А" (latin or cyrillic) -> отладочные платы
        if ref_prefix in ("A", "А"):
            return "dev_boards"
        # Russian prefix "А" for attenuators
        if ref_prefix.startswith(("А", "A")) and len(ref_prefix) > 2:
            # ВАЖНО: Только ОПТИЧЕСКИЕ аттенюаторы идут в optics
            if has_any(text_blob, ["аттенюат", "ослабител", "attenuator"]):
                # Проверяем, оптический ли это аттенюатор
                if has_any(text_blob, ["оптич", "optical", "fc/apc", "fc/upc", "fiber"]):
                    return "optics"
                else:
                    # СВЧ/электрические аттенюаторы -> отладочные платы и модули
                    return "dev_boards"
        # Prefix "W" often used for RF modules
        if ref_prefix.startswith("W"):
            if has_any(text_blob, ["свч", "rf", "линия задержек", "delay line", "усилитель", "делитель", "сумматор", "splitter", "combiner", "amplifier"]):
                return "rf_modules"
        if ref_prefix.startswith("WS"):
            return "rf_modules"
        if ref_prefix.startswith("WU"):
            return "rf_modules"
        # Prefix "H" for indicators/LEDs
        if ref_prefix.startswith("H"):
            return "semiconductors"
        # Prefix "V", "VT", "Q" for transistors
        if ref_prefix.startswith(("V", "VT", "Q")):
            if has_any(text_blob, ["микросхем", "микросхема"]):
                return "ics"
            return "semiconductors"
        # Prefix "D" for diodes
        if ref_prefix.startswith("D"):
            if has_any(text_blob, ["микросхем", "микросхема"]):
                return "ics"
            return "semiconductors"
        # Prefix "S" for switches/buttons
        if ref_prefix.startswith("S"):
            if has_any(text_blob, ["переключ", "тумблер", "кнопка", "switch", "button", "toggle"]):
                return "others"

    # Russian and English keywords
    if RESISTOR_VALUE_RE.search(text_blob) or has_any(text_blob, ["резист", "resistor"]):
        return "resistors"

    if CAP_VALUE_RE.search(text_blob) or has_any(text_blob, ["конденс", "capacitor", "tantalum", "ceramic", "к10-", "к53-"]):
        # Исключаем делители мощности (могут содержать номиналы, похожие на емкость)
        if not has_any(text_blob, ["делитель мощности", "делитель  мощности", "power divider"]):
            return "capacitors"

    if IND_VALUE_RE.search(text_blob) or has_any(text_blob, ["дросс", "индукт", "inductor", "ferrite", "феррит", "катушка", "choke", "вентиль"]):
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
        "свч", "вч ", "rf ", "microwave", "mini-circuits", "planar monolithics", "pmi", "ghz", "lna", "rf amp",
        "линия задержек", "delay line", "делитель мощности", "сумматор", "splitter", "combiner", "усилител",
        "polaris", "gigabaudics", "etl systems", "vat-", "zx60", "pne-l", "ответвитель", "coupler", "фазовращатель",
        "phase shifter", "детектор", "detector", "ограничитель", "limiter", "корректор ачх", "equalizer", "qpd", "power divider"
    ]):
        # НО! Не Qualwave аттенюаторы QFA
        if has_any(text_blob, ["аттенюатор qfa", "qfa"]) and not has_any(text_blob, ["qpd"]):
            return "others"
        return "rf_modules"

    if has_any(text_blob, [
        "кабель", "cable", "шлейф", "провод", "wire", "patch cord", "jumper"
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
