"""Run the user's BZ/TRU/RKM set offline through production code, without editing inputs."""
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
from bom_categorizer.main import main
from bom_categorizer.parsers import parse_docx
from bom_categorizer.tru_rkm_processor import _read_tru_file, process_tru_files_batch, process_rkm_file
from bom_categorizer.tru_merger import (prepare_merge_context, merge_tru_into_bom,
                                      generate_unmatched_report, build_ostatki_and_zapas_reports)

ROOT = Path(r'C:\Project\!SHSK-M')
OUT = Path('docs/algorithm_audit_evidence/release_570').resolve()
OUT.mkdir(parents=True, exist_ok=True)
boms = [ROOT / 'BZ' / n for n in ['BZ_SHSK_M.doc', 'MBOK.doc', 'Mod_PIT_SHSK_M.doc', 'Plata_control.docx']]
trus = [ROOT / 'TPY' / 'TRY_2026' / f'ТРУ.953033.{n}.xls' for n in ['7412', '7413', '7458']]
rkm = ROOT / 'PKM_2026_rkm.xlsx'
manifest = [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in boms + trus + [rkm]]
summary = {'bom': {}, 'tru': {}, 'rkm': {}, 'errors': []}
tru_frames = []
for source in trus:
    raw = _read_tru_file(str(source))
    assert raw is not None and len(raw), source
    output = OUT / (source.stem + '_tpy.xlsx')
    ok, message = process_tru_files_batch([str(source)], str(output))
    assert ok, message
    actual = _read_tru_file(str(output))
    assert len(actual) == len(raw), 'TRU row conservation'
    assert actual['Количество'].sum() == raw['Количество'].astype(float).sum()
    summary['tru'][source.name] = {'rows': len(actual), 'quantity': float(actual['Количество'].sum())}
    tru_frames.append(actual)
    print('TRU', source.name, summary['tru'][source.name], flush=True)

for source in boms:
    print('BOM START', source.name, flush=True)
    try:
        parsed = parse_docx(str(source))
        parsed.to_csv(OUT / (source.stem + '_parsed.csv'), index=False, encoding='utf-8-sig')
        output = OUT / (source.stem + '_bom.xlsx')
        sys.argv = ['verify', '--inputs', str(source), '--xlsx', str(output), '--combine',
                    '--no-interactive', '--assign-json', str(OUT / 'no_rules.json')]
        main()
        sheets = {s: d for s, d in pd.read_excel(output, sheet_name=None).items()
                  if 'Наименование ИВП' in d}
        context = prepare_merge_context(sheets.values(), tru_frames)
        used, matches, shortages, surpluses = set(), [], [], []
        for sheet, frame in sheets.items():
            merged, indices, consumed = merge_tru_into_bom(
                frame, tru_frames, [p.name for p in trus], allocation_context=context)
            used.update(consumed)
            merged['Лист'] = sheet
            merged['Сопоставлено'] = [i in indices for i in merged.index]
            matches.append(merged)
            shortage, surplus = build_ostatki_and_zapas_reports(merged, indices)
            shortages.append(shortage)
            surpluses.append(surplus)
        combined = pd.concat(matches, ignore_index=True)
        combined.to_csv(OUT / (source.stem + '_merged.csv'), index=False, encoding='utf-8-sig')
        unmatched = generate_unmatched_report(tru_frames, used)
        unmatched.to_csv(OUT / (source.stem + '_unmatched.csv'), index=False, encoding='utf-8-sig')
        pd.concat(shortages).to_csv(OUT / (source.stem + '_shortage.csv'), index=False, encoding='utf-8-sig')
        pd.concat(surpluses).to_csv(OUT / (source.stem + '_surplus.csv'), index=False, encoding='utf-8-sig')
        assert len(used) + len(unmatched) == sum(map(len, tru_frames))
        summary['bom'][source.name] = {'parsed_rows': len(parsed), 'parsed_quantity': float(parsed['qty'].sum()),
                                      'output_rows': len(combined), 'matched_rows': int(combined['Сопоставлено'].sum()),
                                      'used_tru_rows': len(used), 'unmatched_tru_rows': len(unmatched)}
        print('BOM RESULT', source.name, summary['bom'][source.name], flush=True)
    except Exception as exc:
        summary['errors'].append({'file': source.name, 'error': str(exc)})
        print('BOM ERROR', source.name, repr(exc), flush=True)

ok, message = process_rkm_file(str(rkm), str(OUT / 'PKM_2026_checked.xlsx'))
assert ok, message
source_rkm = pd.read_excel(rkm).dropna(subset=['Наименование'])
result_rkm = pd.read_excel(OUT / 'PKM_2026_checked.xlsx').dropna(subset=['Наименование'])
assert abs(source_rkm['Стоимость'].sum() - result_rkm['Стоимость'].sum()) < 0.01
assert source_rkm['шт.'].sum() == result_rkm['Количество'].sum()
summary['rkm'] = {'input_rows': len(source_rkm), 'output_rows': len(result_rkm),
                  'cost': float(result_rkm['Стоимость'].sum()), 'message': message}
summary['inputs_unchanged'] = all(hashlib.sha256(Path(m['path']).read_bytes()).hexdigest() == m['sha256'] for m in manifest)
assert summary['inputs_unchanged']
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
if summary['errors']:
    raise SystemExit(1)
