"""Opt-in integration check for the real legacy DOC conversion path.

Run on Windows with Microsoft Word installed:
    $env:RUN_WORD_DOC_TESTS = '1'
    pytest -q tests/algorithm_audit/test_word_doc_conversion.py -s
"""
from pathlib import Path
import os

import pytest

from bom_categorizer.formatters import clean_component_name, extract_tu_code
from bom_categorizer.parsers import parse_docx
from bom_categorizer.utils import contains_our_development_code


SOURCE = Path(r"C:\Project\!SHSK-M\BU\TEST\MKBH-02.doc")


@pytest.mark.skipif(
    os.environ.get("RUN_WORD_DOC_TESTS") != "1",
    reason="requires explicit RUN_WORD_DOC_TESTS=1 and local Microsoft Word",
)
def test_real_mkbh_doc_conversion_restores_de_code(tmp_path):
    if not SOURCE.exists():
        pytest.skip(f"test source is unavailable: {SOURCE}")
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        pytest.skip("pywin32 is not installed")

    target = tmp_path / "MKBH-02.docx"
    pythoncom.CoInitialize()
    app = document = None
    try:
        app = win32com.client.DispatchEx("Word.Application")
        app.Visible = False
        app.DisplayAlerts = 0
        app.AutomationSecurity = 3
        document = app.Documents.Open(
            str(SOURCE), ConfirmConversions=False, ReadOnly=True,
            AddToRecentFiles=False,
        )
        document.SaveAs2(str(target), FileFormat=16, AddToRecentFiles=False)
        document.Close(False)
        document = None

        parsed = parse_docx(str(target))
        candidates = []
        for _, row in parsed.iterrows():
            values = [str(value) for value in row.tolist()]
            joined = " | ".join(values)
            if "5.067.066" in joined or "5,067,066" in joined:
                candidates.append(joined)
        assert candidates, "Word conversion did not expose the expected 5.067.066 code"

        normalized = [clean_component_name(value) for value in candidates]
        assert any(contains_our_development_code(value) for value in normalized)
        assert any("5.067.066" in extract_tu_code(value)[1] for value in normalized)
    finally:
        if document is not None:
            document.Close(False)
        if app is not None:
            app.Quit()
        pythoncom.CoUninitialize()
