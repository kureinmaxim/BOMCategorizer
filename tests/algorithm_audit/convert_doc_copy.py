"""Convert supplied legacy DOC read-only into audit directory using local Word."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import json
import hashlib
import pandas as pd
from bom_categorizer.parsers import parse_docx
source = Path(sys.argv[1] if len(sys.argv) > 1 else
              r'C:\Project\!SHSK-M\BU\TEST\MKBH-02.doc')
out = Path(sys.argv[2] if len(sys.argv) > 2 else
           'docs/algorithm_audit_evidence/MKBH-02_audit.docx').resolve()
before = hashlib.sha256(source.read_bytes()).hexdigest()
app = doc = None
try:
    import win32com.client
    app = win32com.client.DispatchEx('Word.Application')
    app.Visible = False
    app.DisplayAlerts = 0
    app.AutomationSecurity = 3
    doc = app.Documents.Open(str(source), ConfirmConversions=False, ReadOnly=True, AddToRecentFiles=False)
    doc.SaveAs2(str(out), FileFormat=16, AddToRecentFiles=False)
    doc.Close(False)
    doc = None
    app.Quit()
    app = None
    parsed = parse_docx(str(out))
    parsed.to_csv(out.with_suffix('.csv'), index=False, encoding='utf-8-sig')
    print('Converted in isolated Word instance; parsed rows', len(parsed), 'qty', parsed['qty'].sum())
    # Keep an explicit audit trail for the problematic DE code.  The JSON/text
    # representation shows whether Word dropped the first glyph during DOC→DOCX
    # and whether the parser restored it before classification.
    marker = parsed.apply(
        lambda row: ' | '.join(str(v) for v in row.tolist()), axis=1
    )
    matches = marker[marker.str.contains(r'5[.,]067[.,]066', case=False, na=False)]
    for value in matches.tolist():
        print('DE conversion candidate:', value.encode('unicode_escape').decode('ascii'))
except Exception as exc:
    print(type(exc).__name__, str(exc))
finally:
    if doc is not None:
        doc.Close(False)
    if app is not None:
        app.Quit()
    print('Source unchanged:', before == hashlib.sha256(source.read_bytes()).hexdigest())
