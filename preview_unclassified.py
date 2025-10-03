import sys
from typing import Any, List, Optional

import pandas as pd

from split_bom import (
    parse_docx,
    parse_txt_like,
    normalize_column_names,
    find_column,
    classify_row,
)


def load_df(path: str) -> pd.DataFrame:
    p = path.lower()
    if p.endswith(".docx"):
        df = parse_docx(path)
    elif p.endswith(".doc"):
        # Convert via Word COM if available
        try:
            from win32com.client import Dispatch  # type: ignore
            import os
            word = Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(os.path.abspath(path))
            tmp_docx = os.path.splitext(os.path.abspath(path))[0] + "_conv_prev.docx"
            wdFormatXMLDocument = 12
            doc.SaveAs(tmp_docx, FileFormat=wdFormatXMLDocument)
            doc.Close(False)
            word.Quit()
            df = parse_docx(tmp_docx)
        except Exception:
            df = parse_txt_like(path)
    elif p.endswith(".txt"):
        df = parse_txt_like(path)
    else:
        # Excel
        df = pd.read_excel(path, engine="openpyxl")
        if isinstance(df, dict):
            df = next(iter(df.values()))
    return df


def main():
    if len(sys.argv) < 2:
        print("Usage: preview_unclassified.py <input_path>")
        sys.exit(1)
    path = sys.argv[1]
    df = load_df(path)

    original_cols = list(df.columns)
    lower_cols = normalize_column_names(original_cols)
    rename_map = {orig: norm for orig, norm in zip(original_cols, lower_cols)}
    df = df.rename(columns=rename_map)

    ref_col = find_column(["ref", "reference", "designator", "refdes", "обозначение", "позиционное обозначение", "reference"], list(df.columns))
    desc_col = find_column(["description", "desc", "наименование", "item", "part", "part name", "наим."], list(df.columns))
    value_col = find_column(["value", "значение", "номинал"], list(df.columns))
    part_col = find_column(["partnumber", "mfr part", "mpn", "pn", "art", "артикул", "part", "part name"], list(df.columns))

    if not any([ref_col, desc_col, value_col, part_col]):
        df["_row_text_"] = df.apply(lambda r: " ".join(str(x) for x in r.values if pd.notna(x)), axis=1)
        desc_col = "_row_text_"

    cats: List[str] = []
    for _, row in df.iterrows():
        ref = row.get(ref_col) if ref_col else None
        desc = row.get(desc_col) if desc_col else None
        val = row.get(value_col) if value_col else None
        part = row.get(part_col) if part_col else None
        cats.append(classify_row(ref, desc, val, part, strict=False))
    df["category"] = cats

    uncls = df[df["category"] == "unclassified"].copy()
    uncls = uncls.head(20)
    def blob(r):
        parts = []
        for c in [ref_col, desc_col, value_col, part_col]:
            if c and c in r and pd.notna(r[c]):
                parts.append(str(r[c]))
        return " | ".join(parts)

    if uncls.empty:
        print("No unclassified items.")
        return

    print("Unclassified preview (reply with mappings like '1:ics, 2:cables'):")
    for i, (_, row) in enumerate(uncls.iterrows(), start=1):
        print(f"{i}. {blob(row)}")
    print("Categories: resistors, capacitors, inductors, ics, connectors, dev_boards, optics, rf_modules, cables, power_modules, others")


if __name__ == "__main__":
    main()


