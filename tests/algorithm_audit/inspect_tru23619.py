"""Read-only inventory of the supplied procurement export."""
from pathlib import Path
import hashlib
import json
import xlrd

source = Path(r'C:\Users\z6364\OneDrive\Рабочий стол\тру 23619.xls')
out = Path('docs/tru23619_analysis')
out.mkdir(exist_ok=True)
book = xlrd.open_workbook(str(source), encoding_override='cp1251')
manifest = {'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sheets':[]}
for sheet in book.sheets():
    rows = [sheet.row_values(i) for i in range(sheet.nrows)]
    manifest['sheets'].append({'name':sheet.name,'rows':sheet.nrows,'cols':sheet.ncols})
    (out/'raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SHEET',sheet.name,sheet.nrows,sheet.ncols)
    for i,row in enumerate(rows[:3]):
        print('ROW',i+1,[(j+1,v) for j,v in enumerate(row) if v!=''])
    for col in range(sheet.ncols):
        vals = [row[col] for row in rows[2:] if row[col]!='']
        uniq = list(dict.fromkeys(str(v) for v in vals))
        print('COLUMN',col+1,'HEADER',rows[1][col],'filled',len(vals),'unique',len(uniq),'examples',uniq[:5])
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
