import json
from pathlib import Path
import pandas as pd
from bom_categorizer.tru_merger import extract_pure_code
OUT = Path('docs/algorithm_audit_evidence')
raw = pd.read_excel(r'C:\Project\!SHSK-M\TPY\ТРУ_17043_2025\PKM_2026.xlsx', header=None)
print('RKM metre source rows (Excel row, name, unit, qty, price, cost):')
for i, row in raw.loc[raw[5].eq('м')].iterrows():
    print(i+1, [row[c] for c in [1,5,17,18,19]])
result = pd.read_excel(OUT/'PKM_audit_result.xlsx')
print('RKM output for metre sources:')
print(result.loc[result['Наименование'].isin(raw.loc[raw[5].eq('м'),1])].to_string(index=False))
print('RKM duplicates source:')
dupes = raw[raw[1].notna() & raw[1].duplicated(keep=False) & raw[17].notna()]
print(dupes[[0,1,5,17,18,19,22]].to_string(index=True))

trus = pd.concat([pd.read_csv(p, dtype={'Артикул':str}) for p in OUT.glob('ТРУ*_parsed.csv')], ignore_index=True)
by_erp = {str(r['Артикул']):r['Наименование'] for _,r in trus.iterrows()}
for filename in ['Nashi4BU_merged.csv', 'Plata_control_merged.csv']:
    df = pd.read_csv(OUT/filename, dtype={'КОД ERP(МР)':str})
    print('MATCHES differing normalized identity:', filename)
    for _,r in df.loc[df.audit_matched].iterrows():
        original = by_erp.get(r['КОД ERP(МР)'], '')
        if extract_pure_code(r['Наименование ИВП']) != extract_pure_code(original):
            print(r['Наименование ИВП'], '=>', original, '; qty', r['шт.'])
    u = pd.read_csv(OUT/filename.replace('_merged','_unmatched'),dtype={'КОД ERP(МР)':str})
    wrong = [(r['Наименование ИВП'], r['КОД ERP(МР)'], by_erp.get(r['КОД ERP(МР)'])) for _,r in u.iterrows() if pd.notna(r['КОД ERP(МР)']) and extract_pure_code(r['Наименование ИВП']) != extract_pure_code(by_erp.get(r['КОД ERP(МР)'],''))]
    print('unmatched suspicious code/name pair count',len(wrong),'examples',wrong[:4])

# Direct source-reference reconciliation, separate from project parser.
for filename in ['Nashi4BU', 'Plata_control']:
    records = json.loads((OUT/(filename+'_raw.json')).read_text(encoding='utf-8'))
    positions = [r for r in records if r['table']==1 and len(r['cells'])>=4 and any(ch.isdigit() for ch in r['cells'][1])]
    print(filename, 'source rows with numeric reference', len(positions))
    print('notes', [(r['row'], r['cells'][1], r['cells'][-1]) for r in positions if r['cells'][-1].strip()][:20])
