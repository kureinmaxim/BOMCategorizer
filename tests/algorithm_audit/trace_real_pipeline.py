"""Exercise production entry point and merger locally; capture intermediate totals."""
import hashlib
import json
from pathlib import Path
import re
import sys
import pandas as pd
import xlrd
from bom_categorizer.main import main
from bom_categorizer.tru_rkm_processor import process_tru_files_batch, _read_tru_file
from bom_categorizer.tru_merger import merge_tru_into_bom, generate_unmatched_report, build_ostatki_and_zapas_reports

OUT = Path('docs/algorithm_audit_evidence')
BU = Path(r'C:\Project\!SHSK-M\BU')
TPY = Path(r'C:\Project\!SHSK-M\TPY\ТРУ_17043_2025')
summary = {}

# Read BIFF with its actual source encoding, independent of the project parser.
for name in ['ТРУ.953033.17043.xls', 'ТРУ.953033.17043_002.xls']:
    source = TPY / name
    sh = xlrd.open_workbook(str(source), encoding_override='cp1251').sheet_by_index(0)
    raw = pd.DataFrame([sh.row_values(i) for i in range(sh.nrows)])
    raw.to_csv(OUT / (source.stem + '_decoded.csv'), index=False, header=False, encoding='utf-8-sig')
    print('TRU source', name, 'shape', raw.shape, 'units', raw.iloc[2:, 6].value_counts().to_dict())
    print('TRU relevant columns', {i: raw.iloc[1, i] for i in [4, 6, 8, 9, 22, 23, 24] if i < raw.shape[1]})
    output = OUT / (source.stem + '_tpy.xlsx')
    print('TRU process', process_tru_files_batch([str(source)], str(output)))
    df = _read_tru_file(str(output))
    df.to_csv(OUT / (source.stem + '_processed.csv'), index=False, encoding='utf-8-sig')
    summary[name] = {'raw_rows': sh.nrows, 'processed_rows': len(df), 'quantity': pd.to_numeric(df['Количество'], errors='coerce').sum()}

# Run the real CLI entry point with interaction off and a non-existent rules path.
for name in ['Nashi4BU.docx', 'Plata_control.docx', 'plata_MKVH-02_audit.docx']:
    output = OUT / (Path(name).stem + '_bom.xlsx')
    source = OUT / name if name.endswith('_audit.docx') else BU / name
    sys.argv = ['audit', '--inputs', str(source), '--xlsx', str(output), '--combine', '--no-interactive', '--assign-json', str(OUT / 'no_rules.json')]
    main()
    sheets = pd.read_excel(output, sheet_name=None)
    summary[name] = {sheet: {'rows': len(df), 'qty': pd.to_numeric(df.get('шт.', pd.Series(dtype=float)), errors='coerce').sum()} for sheet, df in sheets.items() if sheet not in ['SUMMARY', 'SOURCES', 'INFO']}
    tru_paths = [OUT / (Path(n).stem + '_tpy.xlsx') for n in ['ТРУ.953033.17043.xls', 'ТРУ.953033.17043_002.xls']]
    trus = [_read_tru_file(str(p)) for p in tru_paths]
    used = set()
    matches = []
    for sheet, df in sheets.items():
        if 'Наименование ИВП' not in df:
            continue
        merged, indices, u = merge_tru_into_bom(df, trus, [p.name for p in tru_paths])
        used.update(u)
        merged['audit_sheet'] = sheet
        merged['audit_matched'] = [i in indices for i in merged.index]
        matches.append(merged)
    combined = pd.concat(matches, ignore_index=True)
    combined.to_csv(OUT / (Path(name).stem + '_merged.csv'), index=False, encoding='utf-8-sig')
    unmatched = generate_unmatched_report(trus, used)
    unmatched.to_csv(OUT / (Path(name).stem + '_unmatched.csv'), index=False, encoding='utf-8-sig')
    summary[name]['merge'] = {'matched_bom': int(combined.audit_matched.sum()), 'used_tru': len(used), 'unmatched_tru': len(unmatched), 'missing_erp_unmatched': int(unmatched['КОД ERP(МР)'].isna().sum())}

# Independent RKM source row accounting (no project cleanup/group key copied).
raw = pd.read_excel(TPY / 'PKM_2026.xlsx', header=None)
data = raw[raw[0].astype(str).str.fullmatch(r'\d+\.\d+\.\d+(?:\.\d+)*', na=False)]
print('RKM leaf rows', len(data), 'units', data[5].value_counts().to_dict())
print('RKM named rows with quantities', raw.loc[raw[1].notna() & raw[17].notna(), [0,1,6,7,8,9,10,11,17,18,19]].tail(4).to_string(index=True))
result = pd.read_excel(OUT / 'PKM_audit_result.xlsx')
actual = result[result['Наименование'].notna()]
summary['PKM'] = {'source_leaf_rows': len(data), 'source_plan_qty': pd.to_numeric(data[17], errors='coerce').sum(), 'source_plan_cost': pd.to_numeric(data[19], errors='coerce').sum(), 'result_rows': len(actual), 'result_qty': actual['шт.'].sum(), 'result_cost': actual['Стоимость'].sum()}
print('RKM duplicate names', data[1].value_counts().loc[lambda s: s>1].to_dict())
print('RKM rows missing future plan with historical plan/fact', data.loc[data[17].isna() & (data[6].notna() | data[7].notna()), [0,1,6,7,8,9,10,11,17,18,19]].head(8).to_string(index=True))

# Verify all user-supplied files remain byte-identical.
manifest = json.loads((OUT / 'input_manifest.json').read_text(encoding='utf-8'))
summary['inputs_unchanged'] = all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest() == x['sha256'] for x in manifest)
(OUT / 'real_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
print('SUMMARY', json.dumps(summary, ensure_ascii=False, default=str))
