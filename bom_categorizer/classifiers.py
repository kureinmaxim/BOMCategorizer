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
    
    # Our developments - check before "A" prefix
    if has_any(text_blob, ["мвок", "наша разработ", "собственной разработ", "шск-м", "плата контроллера шск"]):
        return "our_developments"
    
    # ВАЖНО: Проверяем специфичные компоненты ПЕРЕД широкими категориями
    # Адаптеры в разъемы
    if has_any(text_blob, ["адаптер", "adapter"]):
        if not has_any(text_blob, ["fc/", "sc/", "lc/", "оптическ", "optical", "fiber"]):
            return "connectors"
    
    # Нагрузка согласованная в разъемы
    if has_any(text_blob, ["нагрузка согласованная", "согласованная нагрузка", "matched load"]):
        return "connectors"
    
    # Вентили в индуктивности
    if has_any(text_blob, ["вентиль свч", "вентиль вч", "circulator", "isolator", "ферритов", "прибор фвк", "прибор фквн", "фвк3-", "фквн3-"]):
        return "inductors"
    
    # Аттенюаторы QFA от Qualwave в "Другие"
    if has_any(text_blob, ["аттенюатор qfa", "attenuator qfa"]):
        return "others"
    
    # Dev boards / evaluation boards
    if has_any(text_blob, ["плата инструментальная", "evaluation board", "dev board", "отладочная плата", "плата 117212", "hittite"]):
        if not has_any(text_blob, ["делитель мощности", "power divider", "qpd", "аттенюатор qfa"]):
            if has_any(text_blob, ["qualwave", "api technologies", "weinschel", "hittite"]):
                return "dev_boards"
    
    # Optical components (широкая проверка) - check EARLY
    if has_any(text_blob, [
        "оптический модуль", "optical module", "передающий оптический", "приемный оптический",
        "mp2320", "mp2220", "fc/apc", "fc/upc",
        "оптич", "optical", "оптоволокон", "fiber", "мвол", "линия многоканальная задержки"
    ]):
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
        # Russian prefix "А" for attenuators (optics)
        if ref_prefix.startswith(("А", "A")) and len(ref_prefix) > 2:
            if has_any(text_blob, ["аттенюат", "ослабител", "attenuator", "fc/apc", "fc/upc", "оптич", "optical"]):
                return "optics"
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

    # Our developments
    if has_any(text_blob, [
        "мвок", "наша разработ", "собственной разработ", "шск-м", "плата контроллера шск", "плата преобразователя уровней", "амфи.468362", "амфи.436717"
    ]):
        return "our_developments"

    # OTHER general hardware to bucket into 'others'
    if has_any(text_blob, [
        "rittal", "шкаф", "станция", "полка", "кронштейн", "ролик", "болт", "гайка", "шайба", "клавиатура", "моноблок",
        "кабель", "клеммная", "корпус", "шасси", "стеллаж", "стойка", "провод", "розетка", "вентилятор", "генератор",
        "предохранитель", "держател", "зажим", "fuzetec", "реле", "relay", "тумблер", "фильтр", "filter",
        "сетка защитная", "коммутатор", "switch", "переход", "adapter", "линия задержки", "delay line",
        "сердечник", "core", "кварц", "quartz", "вставка плавкая"
    ]):
        return "others"

    # In strict mode, avoid loose matches
    return "unclassified"
