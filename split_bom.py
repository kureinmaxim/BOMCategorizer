import argparse
import os
import sys
import re
import json
from typing import List, Optional, Dict, Any, Iterable, Tuple, Union

import pandas as pd

try:
    from docx import Document  # python-docx
except Exception:
    Document = None  # optional; raise if used without installed


def normalize_column_names(columns: List[str]) -> List[str]:
    normalized = []
    for name in columns:
        if name is None:
            normalized.append("")
            continue
        normalized.append(str(name).strip().lower())
    return normalized


def find_column(possible_names: List[str], columns: List[str]) -> Optional[str]:
    for candidate in possible_names:
        if candidate in columns:
            return candidate
    return None


def has_any(text: str, keywords: List[str]) -> bool:
    if not isinstance(text, str):
        return False
    lower = text.lower()
    return any(k in lower for k in keywords)


RESISTOR_VALUE_RE = re.compile(r"(?i)\b\d+(?:[\.,]\d+)?\s*(?:ом|ohm|k\s*ohm|kohm|к\s*ом|ком|m\s*ohm|mohm|м\s*ом|мом)\b")
CAP_VALUE_RE = re.compile(r"(?i)\b\d+(?:[\.,]\d+)?\s*(?:pf|nf|uf|µf|μf|ф|пф|нф|мкф)\b")
IND_VALUE_RE = re.compile(r"(?i)\b\d+(?:[\.,]\d+)?\s*(?:nh|uh|µh|μh|mh|h|нгн|мкгн|мгн|гн)\b")


# NEW: lightweight parser for TXT/DOCX tables and lines
LINE_SPLIT_RE = re.compile(r"\s{2,}|\t|;|,\s?(?=\S)" )
POS_PREFIX_RE = re.compile(r"^(?:[A-ZА-Я]+\d+(?:[-,;\s]*[A-ZА-Я]*\d+)*)$", re.IGNORECASE)


def parse_txt_like(path: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="cp1251", errors="ignore") as f:
            text = f.read()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = [p.strip() for p in LINE_SPLIT_RE.split(line) if p.strip()]
        if not parts:
            continue
        # Heuristic mapping: [pos?, name/desc, qty?]
        pos = parts[0] if POS_PREFIX_RE.match(parts[0]) else None
        qty = None
        # Try explicit "Nшт" or "N шт" patterns first
        m = re.search(r"(\d+)\s*(шт\.?|pcs|pieces)", line, flags=re.IGNORECASE)
        if m:
            qty = int(m.group(1))
        else:
            for p in parts[::-1]:
                if re.fullmatch(r"\d+", p):
                    qty = int(p)
                    break
        desc = " ".join(parts[1:-1]) if pos and len(parts) >= 2 else (" ".join(parts))
        row = {"reference": pos or "", "description": desc, "qty": qty if qty is not None else 1}
        rows.append(row)
    if not rows:
        # fallback: whole text in a single row
        rows = [{"description": text, "qty": 1}]
    return pd.DataFrame(rows)


def parse_docx(path: str) -> pd.DataFrame:
    if Document is None:
        raise SystemExit("python-docx is required to parse DOCX. Install with pip install python-docx")
    doc = Document(path)
    extracted: List[Dict[str, Any]] = []

    def guess_header_index(table) -> int:
        max_scan = min(5, len(table.rows))
        header_keywords = ["наимен", "обознач", "кол.", "кол ", "кол", "примеч"]
        for i in range(max_scan):
            row_texts = [normalize_cell(c.text).lower() for c in table.rows[i].cells]
            hits = sum(any(hk in t for hk in header_keywords) for t in row_texts)
            if hits >= 2:
                return i
        return 0

    # Parse tables with header detection
    for table in doc.tables:
        if not table.rows:
            continue
        header_idx = guess_header_index(table)
        header_cells = [normalize_cell(c.text).strip() for c in table.rows[header_idx].cells]
        header_norm = [h.lower() for h in header_cells]

        # Find column indices by common names
        def find_col_idx(candidates: List[str]) -> Optional[int]:
            for i, h in enumerate(header_norm):
                for cand in candidates:
                    if cand in h:
                        return i
            return None

        idx_zone = find_col_idx(["зона"])  # optional
        idx_ref = find_col_idx(["поз", "обозн"])  # позиционное обозначение
        idx_name = find_col_idx(["наимен"])  # наименование
        idx_qty = find_col_idx(["кол.", "кол ", "кол", "количество"])  # количество
        idx_note = find_col_idx(["примеч"])  # опционально

        for tr in table.rows[header_idx + 1:]:
            vals = [normalize_cell(c.text) for c in tr.cells]
            if not any(v.strip() for v in vals):
                continue
            zone = vals[idx_zone] if idx_zone is not None and idx_zone < len(vals) else ""
            ref = vals[idx_ref] if idx_ref is not None and idx_ref < len(vals) else ""
            name = vals[idx_name] if idx_name is not None and idx_name < len(vals) else ""
            qty_raw = vals[idx_qty] if idx_qty is not None and idx_qty < len(vals) else ""
            note = vals[idx_note] if idx_note is not None and idx_note < len(vals) else ""

            # If header wasn't detected, try fallback mapping by last column digits
            if not any([ref, name, qty_raw]) and len(vals) >= 2:
                name = " ".join(vals[:-1])
                qty_raw = vals[-1]

            # parse qty
            qty = None
            m = re.search(r"(\d+)", str(qty_raw))
            if m:
                try:
                    qty = int(m.group(1))
                except Exception:
                    qty = 1

            row = {
                "zone": zone,
                "reference": ref,
                "description": name if name else note,
                "qty": qty if qty is not None else 1,
                "note": note,
            }
            extracted.append(row)

    # Additionally parse free text paragraphs (fallback)
    for p in doc.paragraphs:
        t = normalize_cell(p.text)
        if not t:
            continue
        parts = [s.strip() for s in LINE_SPLIT_RE.split(t) if s.strip()]
        if parts:
            pos = parts[0] if POS_PREFIX_RE.match(parts[0]) else ""
            m = re.search(r"(\d+)\s*(шт\.?|pcs|pieces)?", t, flags=re.IGNORECASE)
            qty = int(m.group(1)) if m else 1
            desc = " ".join(parts[1:]) if pos else " ".join(parts)
            extracted.append({"reference": pos, "description": desc, "qty": qty})

    if not extracted:
        extracted = [{"description": " ".join(normalize_cell(p.text) for p in doc.paragraphs), "qty": 1}]
    return pd.DataFrame(extracted)


def normalize_cell(s: Any) -> str:
    return (str(s or "").strip())


def classify_row(ref: Optional[str], description: Optional[str], value: Optional[str], partname: Optional[str], strict: bool, source_file: Optional[str] = None) -> str:
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

    # Create text blob early for use in reference-based checks
    text_blob = " ".join([desc, val, part])

    # Refdes first where reliable
    ref_prefix = ref.split(" ")[0].upper() if ref else ""
    ref_prefix = re.sub(r"\d.*$", "", ref_prefix)  # take letters before digits

    # PRIORITY 1: Check context-specific categories FIRST (before generic prefixes)
    # Check if this is a board/PCB file (self-reference: description is just the filename)
    if src_file and desc:
        # Extract filename without extension
        file_base = src_file.split('/')[-1].split('\\')[-1].rsplit('.', 1)[0].lower()
        desc_lower = desc.lower()
        
        # If description is ONLY the filename (board referencing itself), it's our development
        # AND doesn't contain component keywords
        component_keywords = ['резистор', 'конденсатор', 'микросхема', 'разъем', 'диод', 'индуктор', 'дроссель',
                             'транзистор', 'стабилитрон', 'генератор', 'вилка', 'розетка', 'кабель']
        is_component = any(kw in desc_lower for kw in component_keywords)
        
        if not is_component and file_base in desc_lower.replace('.xlsx', '').replace('.xls', ''):
            # Check if it's just the filename without other text (with tolerance for spaces/extensions)
            desc_clean = desc_lower.replace('.xlsx', '').replace('.xls', '').replace(' ', '').replace('_', '')
            file_clean = file_base.replace(' ', '').replace('_', '')
            if desc_clean == file_clean or desc_clean.startswith(file_clean) or file_clean in desc_clean:
                return "our_developments"
    
    # Our developments - check before "A" prefix
    if has_any(text_blob, ["мвок", "наша разработ", "собственной разработ", "шск-м", "плата контроллера шск"]):
        return "our_developments"
    
    # Optical modules with U prefix - check before "U" prefix for ICs
    if ref and ref_prefix.startswith("U"):
        if has_any(text_blob, ["оптический модуль", "optical module", "передающий оптический", "приемный оптический", "mp2320"]):
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
        # Russian prefix "А" for attenuators (optics)
        if ref_prefix.startswith(("А", "A")) and len(ref_prefix) <= 2:
            # Check if it's really an attenuator, not just "A" prefix IC
            if has_any(text_blob, ["аттенюат", "ослабител", "attenuator", "fc/apc", "fc/upc", "оптич"]):
                return "optics"
        # Prefix "W" often used for RF modules, waveguides, delay lines
        if ref_prefix.startswith("W"):
            if has_any(text_blob, ["свч", "rf", "линия задержек", "delay line", "усилитель", "делитель", "сумматор", "splitter", "combiner", "amplifier"]):
                return "rf_modules"
        # Prefix "WS" for splitters/dividers
        if ref_prefix.startswith("WS"):
            return "rf_modules"
        # Prefix "WU" for RF components
        if ref_prefix.startswith("WU"):
            return "rf_modules"
        # Prefix "H" for indicators/LEDs
        if ref_prefix.startswith("H"):
            return "diods"
        # Prefix "S" for switches/buttons (when not connectors)
        if ref_prefix.startswith("S"):
            if has_any(text_blob, ["переключ", "тумблер", "кнопка", "switch", "button", "toggle"]):
                return "others"

    # Russian and English keywords
    if RESISTOR_VALUE_RE.search(text_blob) or has_any(text_blob, ["резист", "resistor"]):
        return "resistors"

    if CAP_VALUE_RE.search(text_blob) or has_any(text_blob, ["конденс", "capacitor", "tantalum", "ceramic"]):
        return "capacitors"

    if IND_VALUE_RE.search(text_blob) or has_any(text_blob, ["дросс", "индукт", "inductor", "ferrite", "феррит", "катушка", "choke"]):
        return "inductors"
    
    # Diodes - check BEFORE ICs (because "стабил" in ICs catches "стабилитрон")
    if has_any(text_blob, [
        "диод", "стабилитрон", "индикатор", "led ", "svetodiod", "indicator"
    ]):
        return "diods"

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
        "zynq", "som ", "system on module", "voyager", "tinypilot"
    ]):
        return "dev_boards"

    # New categories
    if has_any(text_blob, [
        "оптичес", "лазер", "оптопара", "led ", "светодиод", "fiber", "оптоволок", "sfp", "qsfp", "transceiver module",
        "аттенюат", "ослабител", "fc/apc", "fc/upc", "sc/apc", "lc/apc", "pigtail", "патч-корд оптич"
    ]):
        return "optics"

    if has_any(text_blob, [
        "свч", "вч ", "rf ", "microwave", "mini-circuits", "planar monolithics", "pmi", "qualwave", "ghz", "lna", "rf amp",
        "линия задержек", "delay line", "делитель", "сумматор", "splitter", "combiner", "аттенюатор свч", "усилител",
        "polaris", "gigabaudics", "etl systems", "vat-", "zx60", "pne-l"
    ]):
        return "rf_modules"

    if has_any(text_blob, [
        "кабель", "cable", "шлейф", "провод", "wire", "patch cord", "jumper"
    ]):
        return "cables"

    if has_any(text_blob, [
        "модуль питания", "power module", "dc-dc", "ac-dc", "buck", "boost", "источник питания", "блок питания", "psu",
        "converter"
    ]):
        return "power_modules"

    # Our developments
    if has_any(text_blob, [
        "мвок", "наша разработ", "собственной разработ", "шск-м", "плата контроллера шск"
    ]):
        return "our_developments"

    # OTHER general hardware to bucket into 'others' (cabinets, bolts, shelves, keyboards etc.)
    if has_any(text_blob, [
        "rittal", "шкаф", "станция", "полка", "кронштейн", "ролик", "болт", "гайка", "шайба", "клавиатура", "моноблок",
        "кабель", "клеммная", "корпус", "шасси", "стеллаж", "стойка", "провод", "розетка", "вентилятор", "генератор"
    ]):
        return "others"

    # In strict mode, avoid loose matches
    return "unclassified"


def main():
    parser = argparse.ArgumentParser(description="Split BOM Excel into category CSVs or a single XLSX with sheets")
    parser.add_argument("--input", help="Path to input XLSX file (deprecated if --inputs used)")
    parser.add_argument("--inputs", nargs="+", help="Paths to input XLSX files")
    parser.add_argument("--sheet", default=None, help="Sheet name or index (default: first if not using --sheets)")
    parser.add_argument("--sheets", default=None, help="Comma-separated sheet names or indices to process")
    parser.add_argument("--out", default=None, help="Output directory for CSVs (optional)")
    parser.add_argument("--xlsx", default="categorized.xlsx", help="Path to output XLSX with category sheets")
    parser.add_argument("--merge-into", dest="merge_into", default=None, help="Existing categorized XLSX to merge into (append)")
    parser.add_argument("--combine", action="store_true", help="Create a SUMMARY sheet with aggregated quantities")
    parser.add_argument("--interactive", action="store_true", help="Interactive classification for unclassified rows")
    parser.add_argument("--loose", action="store_true", help="Use looser heuristics (may misclassify non-electronics)")
    parser.add_argument("--assign-json", dest="assign_json", default="rules.json", help="Path to JSON rules for assigning categories to unclassified rows. Format: [{'contains': 'text', 'category': 'ics'}]")
    parser.add_argument("--txt-dir", dest="txt_dir", default=None, help="Output directory for TXT files per category (in addition to XLSX)")
    args = parser.parse_args()

    if not args.inputs and not args.input:
        raise SystemExit("Provide --inputs <files...> or --input <file>")

    inputs: List[str] = args.inputs or ([args.input] if args.input else [])
    selected_sheets: Optional[List[Any]] = None
    if args.sheets:
        selected_sheets = []
        for token in args.sheets.split(','):
            token = token.strip()
            if not token:
                continue
            try:
                selected_sheets.append(int(token))
            except ValueError:
                selected_sheets.append(token)

    if args.out:
        os.makedirs(args.out, exist_ok=True)

    # Load workbook
    read_kwargs = {"engine": "openpyxl"}
    all_rows: List[pd.DataFrame] = []
    for input_path in inputs:
        try:
            ext = os.path.splitext(input_path)[1].lower()
            if ext in [".txt"]:
                df_local = parse_txt_like(input_path)
                df_local["source_file"] = os.path.basename(input_path)
                df_local["source_sheet"] = "txt"
                all_rows.append(df_local)
                continue
            if ext in [".docx"]:
                df_local = parse_docx(input_path)
                df_local["source_file"] = os.path.basename(input_path)
                df_local["source_sheet"] = "docx"
                all_rows.append(df_local)
                continue
            if ext in [".doc"]:
                # Try to convert .doc -> .docx via Word COM (if available), else fallback to text
                try:
                    from win32com.client import Dispatch  # type: ignore
                    word = Dispatch("Word.Application")
                    word.Visible = False
                    doc = word.Documents.Open(os.path.abspath(input_path))
                    tmp_docx = os.path.splitext(os.path.abspath(input_path))[0] + "_conv.docx"
                    wdFormatXMLDocument = 12
                    doc.SaveAs(tmp_docx, FileFormat=wdFormatXMLDocument)
                    doc.Close(False)
                    word.Quit()
                    df_local = parse_docx(tmp_docx)
                except Exception:
                    df_local = parse_txt_like(input_path)
                df_local["source_file"] = os.path.basename(input_path)
                df_local["source_sheet"] = "doc"
                all_rows.append(df_local)
                continue

            if selected_sheets is not None:
                # read all selected sheets explicitly
                for sh in selected_sheets:
                    df_local = pd.read_excel(input_path, sheet_name=sh, **{k: v for k, v in read_kwargs.items() if k != 'sheet_name'})
                    if isinstance(df_local, dict):
                        # unlikely when specifying a single sheet, but guard anyway
                        for _, dfi in df_local.items():
                            dfi["source_file"] = os.path.basename(input_path)
                            dfi["source_sheet"] = str(sh)
                            all_rows.append(dfi)
                    else:
                        df_local["source_file"] = os.path.basename(input_path)
                        df_local["source_sheet"] = str(sh)
                        all_rows.append(df_local)
            else:
                # single sheet or first sheet
                sheet = args.sheet
                if sheet is not None:
                    try:
                        sheet = int(sheet)
                    except ValueError:
                        pass
                    read_kwargs["sheet_name"] = sheet

                df = pd.read_excel(input_path, **read_kwargs)
                if isinstance(df, dict):
                    # take first sheet
                    first_key = next(iter(df))
                    df = df[first_key]
                    src_sheet = first_key
                else:
                    src_sheet = sheet if sheet is not None else 0
                df["source_file"] = os.path.basename(input_path)
                df["source_sheet"] = str(src_sheet)
                all_rows.append(df)
        except Exception as exc:
            raise SystemExit(f"Failed to read Excel '{input_path}': {exc}")

    if not all_rows:
        raise SystemExit("No data loaded from inputs")

    df = pd.concat(all_rows, ignore_index=True)

    # Normalize columns
    original_cols = list(df.columns)
    lower_cols = normalize_column_names(original_cols)
    rename_map = {orig: norm for orig, norm in zip(original_cols, lower_cols)}
    df = df.rename(columns=rename_map)

    # Common column guesses
    ref_col = find_column(["ref", "reference", "designator", "refdes", "reference designator", "обозначение", "позиционное обозначение"], list(df.columns))
    desc_col = find_column(["description", "desc", "наименование", "имя", "item", "part", "part name", "наим."], list(df.columns))
    value_col = find_column(["value", "значение", "номинал"], list(df.columns))
    part_col = find_column(["partnumber", "mfr part", "mpn", "pn", "art", "артикул", "part", "part name"], list(df.columns))
    qty_col = find_column([
        "qty", "quantity", "количество", "кол.", "кол-во", "кол. в ктд", "кол в ктд", "кол. в спецификации", "кол. в кдт",
        "кол. в ктд", "кол. в ктд, шт", "кол. в ктд (шт)", "кол. в ктд, шт."
    ], list(df.columns))
    mr_col = find_column([
        "код мр", "код ивп", "код мр/ивп", "код позиции", "код изделия", "код мр позиции", "код мр ивп"
    ], list(df.columns))

    # Ensure we have at least some text to classify against
    if not any([ref_col, desc_col, value_col, part_col]):
        # create a synthetic description column as a fallback using all columns joined
        df["_row_text_"] = df.apply(lambda r: " ".join(str(x) for x in r.values if pd.notna(x)), axis=1)
        desc_col = "_row_text_"

    def run_classification(input_df: pd.DataFrame) -> pd.DataFrame:
        categories_local: List[str] = []
        for _, row in input_df.iterrows():
            ref = row.get(ref_col) if ref_col else None
            desc = row.get(desc_col) if desc_col else None
            val = row.get(value_col) if value_col else None
            part = row.get(part_col) if part_col else None
            src_file = row.get('source_file') if 'source_file' in input_df.columns else None
            categories_local.append(classify_row(ref, desc, val, part, strict=not args.loose, source_file=src_file))
        input_df = input_df.copy()
        input_df["category"] = categories_local
        return input_df

    df = run_classification(df)

    # Interactive reassignment for unclassified
    if args.interactive:
        cat_names = [
            ("resistors", "Резисторы"),
            ("capacitors", "Конденсаторы"),
            ("inductors", "Дроссели"),
            ("ics", "Микросхемы"),
            ("connectors", "Разъемы"),
            ("dev_boards", "Отладочные платы"),
            ("diods", "Диоды"),
            ("our_developments", "Наши разработки"),
            ("others", "Другие"),
            ("unclassified", "Не распределено"),
        ]
        uncls = df[df["category"] == "unclassified"].copy()
        max_preview = min(len(uncls), 50)
        print(f"Нераспределено: {len(uncls)}. Покажу первые {max_preview} для разметки.")
        # Load existing rules (append new choices)
        existing_rules: List[Dict[str, Any]] = []
        if args.assign_json and os.path.exists(args.assign_json):
            try:
                with open(args.assign_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing_rules = data
            except Exception:
                pass
        for idx, (_, row) in enumerate(uncls.head(max_preview).iterrows(), start=1):
            text_blob = " ".join(str(x) for x in [row.get(desc_col), row.get(value_col), row.get(part_col)] if pd.notna(x))
            print(f"[{idx}] {text_blob}")
            for i, (_, ru) in enumerate(cat_names, start=1):
                print(f"  {i}. {ru}")
            choice = input("Выберите номер категории (Enter чтобы пропустить): ").strip()
            if choice.isdigit():
                ci = int(choice)
                if 1 <= ci <= len(cat_names):
                    selected_key = cat_names[ci - 1][0]
                    df.loc[uncls.index[idx - 1], "category"] = selected_key
                    # Persist rule by 'contains' text blob
                    rule = {"contains": text_blob[:160], "category": selected_key}
                    existing_rules.append(rule)
        # Save updated rules if any
        try:
            if args.assign_json:
                with open(args.assign_json, "w", encoding="utf-8") as f:
                    json.dump(existing_rules, f, ensure_ascii=False, indent=2)
                print(f"Сохранил правила: {args.assign_json}")
        except Exception as exc:
            print(f"Не удалось сохранить правила: {exc}")
        # Optionally redo classification for remaining items if needed (skipped for simplicity)

    outputs = {
        "resistors": df[df["category"] == "resistors"],
        "capacitors": df[df["category"] == "capacitors"],
        "inductors": df[df["category"] == "inductors"],
        "ics": df[df["category"] == "ics"],
        "connectors": df[df["category"] == "connectors"],
        "dev_boards": df[df["category"] == "dev_boards"],
        "optics": df[df["category"] == "optics"],
        "rf_modules": df[df["category"] == "rf_modules"],
        "cables": df[df["category"] == "cables"],
        "power_modules": df[df["category"] == "power_modules"],
        "diods": df[df["category"] == "diods"],
        "our_developments": df[df["category"] == "our_developments"],
        "others": df[df["category"] == "others"],
        "unclassified": df[df["category"] == "unclassified"],
    }

    # Apply assignment rules if provided
    if args.assign_json and os.path.exists(args.assign_json):
        try:
            with open(args.assign_json, "r", encoding="utf-8") as f:
                rules = json.load(f)
        except Exception as exc:
            print(f"Failed to read assign rules: {exc}")
            rules = []
        if isinstance(rules, list):
            df = df.copy()
            lower_cols = set(df.columns)
            for i, rule in enumerate(rules, start=1):
                cat = str(rule.get("category", "")).strip()
                contains = str(rule.get("contains", "")).strip().lower()
                regex = rule.get("regex")
                if not cat or (not contains and not regex):
                    continue
                mask = df["category"] == "unclassified"
                if contains:
                    blob = (
                        df.get("description", pd.Series([""] * len(df))).astype(str).str.lower().fillna("") + " " +
                        df.get("value", pd.Series([""] * len(df))).astype(str).str.lower().fillna("") + " " +
                        df.get("part", pd.Series([""] * len(df))).astype(str).str.lower().fillna("") + " " +
                        df.get("reference", pd.Series([""] * len(df))).astype(str).str.lower().fillna("")
                    )
                    mask = mask & blob.str.contains(re.escape(contains), na=False)
                if regex:
                    try:
                        r = re.compile(regex, re.IGNORECASE)
                        text_series = (
                            df.get("description", "").astype(str).fillna("") + " " +
                            df.get("value", "").astype(str).fillna("") + " " +
                            df.get("part", "").astype(str).fillna("") + " " +
                            df.get("reference", "").astype(str).fillna("")
                        )
                        mask = mask & text_series.apply(lambda t: bool(r.search(t)))
                    except Exception:
                        pass
                df.loc[mask, "category"] = cat
            # refresh outputs
            outputs = {k: df[df["category"] == k] for k in outputs.keys()}

    # Enrich each output with MR code and total quantity per item
    def enrich_with_mr_and_total(frame: pd.DataFrame) -> pd.DataFrame:
        enriched = frame.copy()
        # MR code column
        if mr_col and mr_col in enriched.columns:
            mr_series = enriched[mr_col].fillna("-")
        else:
            mr_series = pd.Series(["-"] * len(enriched), index=enriched.index)
        enriched["Код МР"] = mr_series.astype(str)

        # quantity per row
        if qty_col and qty_col in enriched.columns and pd.api.types.is_numeric_dtype(enriched[qty_col]):
            qty_series = enriched[qty_col]
        else:
            qty_series = pd.Series([1] * len(enriched), index=enriched.index)

        # grouping keys to compute total quantity per item
        group_keys: List[str] = []
        if mr_col and mr_col in enriched.columns and (enriched[mr_col].notna().any()):
            group_keys = [mr_col]
        else:
            for cand in [part_col, value_col, desc_col]:
                if cand and cand in enriched.columns:
                    group_keys.append(cand)
        if not group_keys:
            group_keys = ["category"]

        tmp = enriched.copy()
        tmp["__qty__"] = qty_series
        totals = tmp.groupby(group_keys, dropna=False)["__qty__"].sum().reset_index().rename(columns={"__qty__": "Общее количество"})
        enriched = enriched.merge(totals, on=group_keys, how="left")
        # fill missing
        if "Общее количество" not in enriched.columns:
            enriched["Общее количество"] = 0
        return enriched

    outputs = {name: enrich_with_mr_and_total(df_part) for name, df_part in outputs.items()}

    # Russian category names for output
    rus_sheet_names = {
        "resistors": "Резисторы",
        "capacitors": "Конденсаторы",
        "inductors": "Дроссели",
        "ics": "Микросхемы",
        "connectors": "Разъемы",
        "dev_boards": "Отладочные платы",
        "optics": "Оптические компоненты",
        "rf_modules": "СВЧ модули",
        "cables": "Кабели",
        "power_modules": "Модули питания",
        "diods": "Диоды",
        "our_developments": "Наши разработки",
        "others": "Другие",
        "unclassified": "Не распределено",
    }

    # Optional CSVs
    if args.out:
        for name, part_df in outputs.items():
            out_path = os.path.join(args.out, f"{name}.csv")
            save_df = part_df.copy()
            inverse_rename = {v: k for k, v in rename_map.items()}
            save_df = save_df.rename(columns=inverse_rename)
            save_df.to_csv(out_path, index=False, encoding="utf-8-sig")

    # Optional TXT files per category
    if args.txt_dir:
        os.makedirs(args.txt_dir, exist_ok=True)
        for name, part_df in outputs.items():
            if part_df.empty:
                continue
            rus_name = rus_sheet_names.get(name, name)
            txt_path = os.path.join(args.txt_dir, f"{rus_name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"=== {rus_name.upper()} ===\n")
                f.write(f"Всего элементов: {len(part_df)}\n")
                f.write("=" * 80 + "\n\n")
                
                for idx, row in part_df.iterrows():
                    # Collect available columns
                    ref = row.get(ref_col) if ref_col and ref_col in part_df.columns else None
                    desc = row.get(desc_col) if desc_col and desc_col in part_df.columns else None
                    val = row.get(value_col) if value_col and value_col in part_df.columns else None
                    part = row.get(part_col) if part_col and part_col in part_df.columns else None
                    qty = row.get(qty_col) if qty_col and qty_col in part_df.columns else None
                    mr = row.get("Код МР") if "Код МР" in part_df.columns else None
                    
                    # Format output
                    if pd.notna(ref) and str(ref).strip():
                        f.write(f"[{ref}] ")
                    
                    if pd.notna(desc) and str(desc).strip():
                        f.write(f"{desc}")
                    
                    if pd.notna(val) and str(val).strip():
                        f.write(f" | Значение: {val}")
                    
                    if pd.notna(part) and str(part).strip():
                        f.write(f" | Part: {part}")
                    
                    if pd.notna(qty):
                        try:
                            qty_int = int(float(qty))
                            f.write(f" | Кол-во: {qty_int} шт")
                        except (ValueError, TypeError):
                            pass
                    
                    if pd.notna(mr) and str(mr).strip() and str(mr) != "-":
                        f.write(f" | Код МР: {mr}")
                    
                    f.write("\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Всего записей: {len(part_df)}\n")
        
        print(f"TXT files written to: {args.txt_dir}")

    # XLSX with sheets
    def merge_existing_if_needed(writer, new_outputs: Dict[str, pd.DataFrame], existing_path: Optional[str]):
        if not existing_path or not os.path.exists(existing_path):
            # just write new_outputs as-is
            for key, part_df in new_outputs.items():
                save_df = part_df.copy()
                inverse_rename = {v: k for k, v in rename_map.items()}
                save_df = save_df.rename(columns=inverse_rename)
                sheet_name = rus_sheet_names.get(key, key)[:31]
                if save_df.empty:
                    save_df = pd.DataFrame(columns=list(inverse_rename.values()) + ["category", "source_file", "source_sheet", "Код МР", "Общее количество"])  # type: ignore
                save_df.to_excel(writer, sheet_name=sheet_name, index=False)
            return

        # merge with existing workbook
        try:
            xls = pd.ExcelFile(existing_path, engine="openpyxl")
        except Exception:
            # if cannot read, fallback to new write
            for key, part_df in new_outputs.items():
                save_df = part_df.copy()
                inverse_rename = {v: k for k, v in rename_map.items()}
                save_df = save_df.rename(columns=inverse_rename)
                sheet_name = rus_sheet_names.get(key, key)[:31]
                if save_df.empty:
                    save_df = pd.DataFrame(columns=list(inverse_rename.values()) + ["category", "source_file", "source_sheet", "Код МР", "Общее количество"])  # type: ignore
                save_df.to_excel(writer, sheet_name=sheet_name, index=False)
            return

        for key, part_df in new_outputs.items():
            inverse_rename = {v: k for k, v in rename_map.items()}
            new_df = part_df.rename(columns=inverse_rename).copy()
            sheet_name = rus_sheet_names.get(key, key)[:31]
            if sheet_name in xls.sheet_names:
                try:
                    old_df = pd.read_excel(existing_path, sheet_name=sheet_name, engine="openpyxl")
                    combined = pd.concat([old_df, new_df], ignore_index=True, sort=False)
                except Exception:
                    combined = new_df
            else:
                combined = new_df
            if combined.empty:
                combined = pd.DataFrame(columns=list(inverse_rename.values()) + ["category", "source_file", "source_sheet", "Код МР", "Общее количество"])  # type: ignore
            combined.to_excel(writer, sheet_name=sheet_name, index=False)

    def clean_component_name(row, desc_col_name):
        """Очистить наименование компонента и извлечь ТУ и тип компонента"""
        import re
        
        if desc_col_name not in row or pd.isna(row[desc_col_name]):
            return '', '', ''
        
        text = str(row[desc_col_name])
        original_text = text
        
        # Извлечь ТУ (различные форматы)
        tu_code = ''
        
        # Вариант 1: ТУ с точками и дефисами (например, "АЕНВ.431320.515-01ТУ", "АЛЯР.434110.005ТУ")
        tu_pattern1 = r'([А-ЯЁ]{2,}\.\d+[\d\.\-]*ТУ)'
        tu_match1 = re.search(tu_pattern1, text)
        if tu_match1:
            tu_code = tu_match1.group(1)
            text = text.replace(tu_code, '').strip()
        else:
            # Вариант 2: ТУ в начале (например, "ТУ 6329-019-07614320-99")
            tu_pattern2 = r'ТУ\s+([\d\-]+)'
            tu_match2 = re.search(tu_pattern2, text)
            if tu_match2:
                tu_code = 'ТУ ' + tu_match2.group(1)
                text = text.replace(tu_code, '').strip()
            else:
                # Вариант 3: Без дефиса но с точками (например, "СМ3.362.805ТУ")
                tu_pattern3 = r'([А-ЯЁ]{2,}[\d\.]+ТУ)'
                tu_match3 = re.search(tu_pattern3, text)
                if tu_match3:
                    tu_code = tu_match3.group(1)
                    text = text.replace(tu_code, '').strip()
                else:
                    # Вариант 4: Общий паттерн (на случай других форматов)
                    tu_pattern4 = r'([А-ЯЁ]{2,}[\d\.]+[А-ЯЁ]{0,3})'
                    tu_match4 = re.search(tu_pattern4, text)
                    if tu_match4:
                        tu_code = tu_match4.group(1)
                        text = text.replace(tu_code, '').strip()
        
        # Извлечь и удалить типы компонентов в начале
        component_types = ['Резистор', 'Конденсатор', 'Микросхема', 'Разъем', 'Диод', 
                          'Транзистор', 'Индуктивность', 'Дроссель', 'Кабель', 'Модуль',
                          'Стабилитрон', 'Вилка', 'Розетка', 'Генератор']
        component_type = ''
        for comp_type in component_types:
            if original_text.startswith(comp_type):
                component_type = comp_type
                text = text[len(comp_type):].strip() if text.startswith(comp_type) else text
                break
        
        # Очистить от лишних пробелов
        text = ' '.join(text.split())
        
        return text, tu_code, component_type
    
    def extract_nominal_value(text):
        """
        Извлечь номинал из текста и преобразовать в число для сортировки.
        Примеры: "180 Ом" -> 180, "1 кОм" -> 1000, "100 пФ" -> 100e-12
        """
        import re
        
        if not isinstance(text, str):
            return 0
        
        # Множители для разных единиц
        multipliers = {
            # Сопротивление
            'мом': 1e6, 'мегаом': 1e6,
            'ком': 1e3, 'килоом': 1e3,
            'ом': 1,
            # Емкость
            'ф': 1, 'фарад': 1,
            'мф': 1e-3, 'миллифарад': 1e-3,
            'мкф': 1e-6, 'микрофарад': 1e-6, 'µф': 1e-6,
            'нф': 1e-9, 'нанофарад': 1e-9,
            'пф': 1e-12, 'пикофарад': 1e-12,
            # Индуктивность
            'гн': 1, 'генри': 1,
            'мгн': 1e-3, 'миллигенри': 1e-3,
            'мкгн': 1e-6, 'микрогенри': 1e-6, 'µгн': 1e-6,
        }
        
        # Попытаться найти число с единицей измерения
        # Паттерн: число (с возможной точкой/запятой) + пробелы + единица
        pattern = r'([\d.,]+)\s*([а-яА-Яa-zA-Z]+)'
        matches = re.findall(pattern, text.lower())
        
        for num_str, unit in matches:
            # Преобразовать число
            try:
                num = float(num_str.replace(',', '.'))
            except ValueError:
                continue
            
            # Найти множитель для единицы
            for unit_key, mult in multipliers.items():
                if unit_key in unit:
                    return num * mult
        
        return 0

    with pd.ExcelWriter(args.xlsx, engine="openpyxl") as writer:
        # Записать каждую категорию с № п/п
        for key, part_df in outputs.items():
            sheet_name = rus_sheet_names.get(key, key)[:31]
            result_df = part_df.copy()
            
            # Удалить ВСЕ старые колонки с номерами (могут быть варианты написания)
            cols_to_remove = [col for col in result_df.columns 
                            if col in ['№ п/п', '№ п\п', 'п/п', 'номер', '№']]
            if cols_to_remove:
                result_df = result_df.drop(columns=cols_to_remove)
            
            # Удалить ненужные столбцы (количество, цена, стоимость, source_sheet, _row_text_, category)
            cols_to_remove = [col for col in result_df.columns 
                            if col in ['количество', 'первоначальная цена, тыс.руб.', 
                                      'первоначальная стоимость, тыс.руб.', 
                                      'source_sheet', '_row_text_', 'category']]
            if cols_to_remove:
                result_df = result_df.drop(columns=cols_to_remove)
            
            # Переименовать столбцы
            if 'Общее количество' in result_df.columns:
                result_df = result_df.rename(columns={'Общее количество': 'Кол-во'})
            if 'наименование ивп' in result_df.columns:
                result_df = result_df.rename(columns={'наименование ивп': 'Наименование ИВП'})
            
            # Обработать наименование - очистить и извлечь ТУ
            # Найти столбец с наименованием (ВАЖНО: сначала ищем переименованный столбец!)
            desc_col_name = None
            for possible_name in ['Наименование ИВП', 'наименование ивп', 'описание', 'наименование', desc_col]:
                if possible_name and possible_name in result_df.columns:
                    desc_col_name = possible_name
                    break
            
            if desc_col_name:
                # Применить функцию очистки к каждой строке
                cleaned_data = result_df.apply(lambda row: clean_component_name(row, desc_col_name), axis=1)
                result_df[desc_col_name] = [item[0] for item in cleaned_data]
                
                # Вставить ТУ сразу после наименования (а не в конец)
                tu_data = [item[1] for item in cleaned_data]
                desc_idx = list(result_df.columns).index(desc_col_name)
                result_df.insert(desc_idx + 1, 'ТУ', tu_data)
                
                # Вставить Примечание после ТУ
                component_types = [item[2] for item in cleaned_data]
                
                # Определить стандартный тип для категории
                category_standard_types = {
                    'Резисторы': 'Резистор',
                    'Конденсаторы': 'Конденсатор',
                    'Дроссели': 'Дроссель',
                    'Микросхемы': 'Микросхема',
                    'Разъемы': 'Разъем',
                    'Диоды': 'Диод',
                }
                
                standard_type = category_standard_types.get(sheet_name, '')
                
                # Если тип компонента совпадает со стандартным для категории - ставим "-"
                primechanie = []
                for comp_type in component_types:
                    if not comp_type or comp_type == standard_type:
                        primechanie.append('-')
                    else:
                        primechanie.append(comp_type)
                
                result_df.insert(desc_idx + 2, 'Примечание', primechanie)
                
                # Сортировка: сначала импортные, потом отечественные
                # Создаем вспомогательные столбцы для сортировки
                result_df['_is_domestic'] = result_df['ТУ'].apply(
                    lambda x: 1 if (x and x != '-' and str(x).strip() != '') else 0
                )
                
                # Для отечественных: извлечь первые цифры из названия
                def get_domestic_number(row):
                    if row['_is_domestic'] == 1:
                        import re
                        name = str(row[desc_col_name])
                        match = re.match(r'(\d+)', name)
                        if match:
                            return int(match.group(1))
                        else:
                            return 999999
                    else:
                        return 0
                
                result_df['_domestic_num'] = result_df.apply(get_domestic_number, axis=1)
                
                # Для импортных: сортировка по номиналу
                result_df['_nominal'] = result_df[desc_col_name].apply(extract_nominal_value)
                
                # Сортируем: сначала по типу (импортные/отечественные), потом по номиналу/номеру, потом по имени
                result_df = result_df.sort_values(
                    by=['_is_domestic', '_domestic_num', '_nominal', desc_col_name],
                    ascending=[True, True, True, True]
                )
                
                result_df = result_df.drop(columns=['_is_domestic', '_domestic_num', '_nominal'])
                result_df = result_df.reset_index(drop=True)
            
            # Добавить новую колонку № п/п в начало (ПОСЛЕ сортировки!)
            result_df.insert(0, '№ п/п', range(1, len(result_df) + 1))
            result_df.to_excel(writer, sheet_name=sheet_name, index=False)

        if args.combine:
            # Не создаем SUMMARY - он не нужен или создаем простую сводку
            summary_rows = []
            for key, part_df in outputs.items():
                if len(part_df) == 0:
                    continue
                category_name = rus_sheet_names.get(key, key)
                # Суммировать количество по категории
                total_qty = part_df['Общее количество'].sum() if 'Общее количество' in part_df.columns else len(part_df)
                summary_rows.append({
                    '№ п/п': len(summary_rows) + 1,
                    'Категория': category_name,
                    'Кол-во позиций': len(part_df),
                    'Общее количество': int(total_qty)
                })
            
            summary = pd.DataFrame(summary_rows)
            summary.to_excel(writer, sheet_name="SUMMARY", index=False)
        # SOURCES sheet
        sources = pd.DataFrame(sorted({(r.get("source_file", ""), r.get("source_sheet", "")) for _, r in df.iterrows()}), columns=["source_file", "source_sheet"])
        sources.to_excel(writer, sheet_name="SOURCES", index=False)
        
        # Применить форматирование к каждому листу
        from openpyxl.styles import Alignment
        
        for sheet_name in writer.book.sheetnames:
            ws = writer.book[sheet_name]
            
            # Найти индексы столбцов "Наименование ИВП" и "ТУ"
            desc_col_idx = None
            tu_col_idx = None
            for idx, cell in enumerate(ws[1], start=1):
                cell_val = str(cell.value).lower() if cell.value else ''
                if 'наименование ивп' in cell_val or 'наименование' in cell_val:
                    desc_col_idx = idx
                elif cell_val == 'ту':
                    tu_col_idx = idx
            
            # Центрировать все ячейки, кроме "наименование ивп" и "ТУ"
            for row_idx, row in enumerate(ws.iter_rows(), start=1):
                for col_idx, cell in enumerate(row, start=1):
                    if col_idx == desc_col_idx or col_idx == tu_col_idx:
                        # Наименование ИВП и ТУ - выравнивание по левому краю
                        cell.alignment = Alignment(horizontal='left', vertical='center')
                    else:
                        # Все остальные - по центру
                        cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Автоматически установить ширину столбцов по содержимому
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        cell_value = str(cell.value) if cell.value is not None else ""
                        if len(cell_value) > max_length:
                            max_length = len(cell_value)
                    except:
                        pass
                
                # Установить ширину с небольшим запасом
                adjusted_width = min(max_length + 2, 50)  # максимум 50 символов
                ws.column_dimensions[column_letter].width = adjusted_width

    # Print counts
    print("Split complete:")
    for name, part_df in outputs.items():
        print(f"  {name}: {len(part_df)}")
    print(f"XLSX written: {args.xlsx}")


def build_summary(df: pd.DataFrame, ref_col: Optional[str], desc_col: Optional[str], value_col: Optional[str], part_col: Optional[str], qty_col: Optional[str], mr_col: Optional[str]) -> pd.DataFrame:
    work = df.copy()
    if qty_col and qty_col in work.columns and pd.api.types.is_numeric_dtype(work[qty_col]):
        work["_qty_"] = work[qty_col]
    else:
        work["_qty_"] = 1

    group_keys: List[str] = []
    if mr_col and mr_col in work.columns and (work[mr_col].notna().any()):
        group_keys = [mr_col]
    else:
        for cand in [part_col, value_col, desc_col]:
            if cand and cand in work.columns:
                group_keys.append(cand)
    if not group_keys:
        group_keys = ["category"]

    summary = work.groupby(group_keys, dropna=False, as_index=False)["_qty_"].sum()
    summary = summary.rename(columns={"_qty_": "Общее количество"})

    # Add MR code column
    if mr_col and mr_col in work.columns:
        mr_map = work.groupby(group_keys)[mr_col].agg(lambda s: next((x for x in s if pd.notna(x)), None)).reset_index()
        summary = summary.merge(mr_map, on=group_keys, how="left")
        summary = summary.rename(columns={mr_col: "Код МР"})
    else:
        summary["Код МР"] = "-"

    cols = list(summary.columns)
    if "category" in cols:
        cols = ["category"] + [c for c in cols if c != "category"]
        summary = summary[cols]
    return summary


if __name__ == "__main__":
    main()


