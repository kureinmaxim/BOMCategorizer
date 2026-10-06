"""Standalone, offline review of the supplied export; no application integration."""
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import hashlib
import html
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/tru23619_analysis'


def dec(value):
    if value == '' or value is None:
        return None
    return Decimal(str(value))


def money(value):
    if value is None:
        return 'нет данных'
    return f'{value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):,.2f}'.replace(',', ' ').replace('.', ',')


def funding_scenario(required, available, inclusion, comparable=False):
    """No claim of deficit without compatible scope and a known reservation basis."""
    if not comparable or required is None or available is None:
        return {'kind': 'needs_data', 'gap': None}
    if inclusion == 'included':
        return {'kind': 'already_reserved', 'gap': None}
    if inclusion != 'excluded':
        return {'kind': 'unknown_reservation', 'gap': None}
    return {'kind': 'additional_funding', 'gap': max(Decimal(0), dec(required)-dec(available))}


def summarize(rows):
    """Keep lifecycle states independent; a rejection note is not a final status."""
    records = []
    for line, r in enumerate(rows, 3):
        amount, qty, price = dec(r[9]), dec(r[4]), dec(r[8])
        net, net_price = dec(r[23]), dec(r[22])
        reasons = []
        if r[21]:
            reasons.append(str(r[21]))
        if qty is None or price is None or amount is None:
            reasons.append('Не хватает числовых данных')
        elif abs(amount - qty * price) > Decimal('0.01'):
            reasons.append('Сумма не равна количеству × цене')
        if net is not None and net_price is not None and qty is not None:
            delta = abs(net - qty * net_price)
            # A two-decimal displayed unit price can accumulate rounding per unit.
            tolerance = abs(qty) * Decimal('0.005') + Decimal('0.005')
            if delta > tolerance:
                reasons.append('Расхождение суммы без НДС сверх округления')
        packaging = 'PCS' in str(r[1]).upper()
        if packaging:
            reasons.append('Проверить: штука или упаковка; в названии указано PCS')
        records.append(dict(row=line, erp=str(r[0]), name=str(r[1]), qty=r[4], unit=str(r[5]),
                            price=str(price) if price is not None else None,
                            amount=str(amount) if amount is not None else None,
                            net=str(net) if net is not None else None,
                            status=str(r[64]), reason=str(r[21]), comment=str(r[3]),
                            owner=str(r[12]), problems=reasons,
                            approved=r[71], received=r[74]))
    groups = defaultdict(lambda: {'count': 0, 'amount': Decimal(0)})
    for r in records:
        groups[r['status']]['count'] += 1
        if r['amount'] is not None:
            groups[r['status']]['amount'] += dec(r['amount'])
    # Reject inconsistent repetitions rather than selecting an arbitrary budget value.
    budgets = {}
    for r in rows:
        key = str(r[37])
        value = tuple(dec(r[c]) for c in (39, 40, 41))
        if key in budgets and budgets[key] != value:
            raise ValueError(f'Противоречивый лимит {key}')
        budgets[key] = value
    return records, groups, budgets


def main():
    rows = json.loads((OUT / 'raw.json').read_text(encoding='utf-8'))[2:]
    records, groups, budgets = summarize(rows)
    total = sum((dec(r['amount']) for r in records), Decimal(0))
    active = sum((dec(r['amount']) for r in records if r['status'] != 'Отклонено'), Decimal(0))
    budget, balance, draft_balance = next(iter(budgets.values()))
    scenario = funding_scenario(active, draft_balance, 'excluded', comparable=True)
    summary = {'rows': len(records), 'total': str(total), 'active': str(active),
               'budget': str(budget), 'balance': str(balance), 'with_drafts': str(draft_balance),
               'conditional_gap': str(scenario['gap']),
               'statuses': {k:{'count':v['count'],'amount':str(v['amount'])} for k,v in groups.items()}}
    (OUT / 'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT / 'items.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    data = json.dumps(records, ensure_ascii=False).replace('<', '\\u003c')
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ТРУ 23619 — инженерный разбор</title><style>
body{font:16px/1.5 system-ui,sans-serif;color:#203040;background:#f2f5f8;margin:0}main{max-width:1500px;margin:auto;padding:28px}h1{margin:0}h2{font-size:22px}p{max-width:1000px}.sub{color:#516476}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:24px 0}.card,section{background:white;padding:20px;border-radius:10px;margin-bottom:18px}.value{display:block;font-size:27px;font-weight:700}.warn{border-left:5px solid #b46b00}.bad{color:#9c3d15}.controls{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}input,select,button{font:inherit;padding:9px;border:1px solid #a3b3c1;border-radius:5px}input{min-width:290px}.scroll{overflow:auto;max-height:70vh}table{border-collapse:collapse;width:100%;font-size:14px}th{position:sticky;top:0;background:#e5edf4;text-align:left;z-index:1}th,td{padding:10px;border-bottom:1px solid #dce3e9;vertical-align:top}td:nth-child(2){min-width:290px}td:nth-child(5){white-space:nowrap}summary{cursor:pointer;color:#176197}small{color:#516476}.hidden{display:none}@media print{.controls{display:none}.scroll{max-height:none}th{position:static}body{background:white}}
</style><main><h1>ТРУ 23619: что требует решения</h1><p class="sub">106 позиций · версия №1 от 24.07.2026 · плановая дата 15.12.2026 · разбор 06.10.2026. Дата самой выгрузки неизвестна. Исходник не изменён.</p>
<div class="cards"><div class="card">Все строки заявки<span class="value">925 652,00 ₽</span><small>Включая 7 отклонённых строк</small></div><div class="card">Без отклонённых<span class="value">921 131,26 ₽</span><small>99 строк; это ещё не оплаченная закупка</small></div><div class="card">Остаток с «Формируется»<span class="value">35 112,28 ₽</span><small>Один общий лимит 17,5 млн ₽</small></div><div class="card">Есть замечание в источнике<span class="value">55 из 106</span><small>48 из них не имеют статуса «Отклонено»</small></div></div>
<section class="warn"><h2>Денег не хватает? Пока только условный расчёт</h2><p>Если 99 неотклонённых строк ещё НЕ включены в остаток, их все нужно закупать и лимит учитывает суммы на той же основе по НДС, требуется ещё <strong>886 018,98 ₽</strong>. Если заявка уже учтена, повторно вычитать её нельзя. В файле нет платежей, остатков склада и ценового эталона — фактический перерасход и экономию установить нельзя.</p></section>
<section><h2>Сначала проверить</h2><ol><li><strong>453 954,38 ₽ — две строки TAPE SEAL.</strong> Почти половина заявки. Заявлено 21 и 11 шт., но в названии 30 PCS и 20 PCS. Уточнить цену и единицу упаковки; автоматически пересчитывать нельзя.</li><li><strong>26 строк без технического задания — 166 065,28 ₽.</strong> Подготовить или привязать ТЗ, сверить актуальность замечания.</li><li><strong>4 отказа от поставки — 158 061,81 ₽.</strong> Уточнить причину и альтернативного поставщика; 124 800 ₽ приходится на фильтровальную бумагу.</li><li><strong>15 замечаний по нормативу отгрузки — 97 785,67 ₽.</strong> Нужны кратность, минимальная партия и фактическая потребность. Не увеличивать количество автоматически.</li><li><strong>2 строки «Товар выписан в подразделение» — 588,04 ₽.</strong> Проверить документы выдачи: повторная закупка может оказаться ненужной.</li></ol><p><small>Суммы проблем — объём строк с замечанием, а не оценка потери денег. Замечания могут быть историческими.</small></p></section>
<section><h2>Позиции и объяснения</h2><div class="controls"><input id="query" aria-label="Поиск" placeholder="Наименование, ERP, причина"><select id="state" aria-label="Состояние"><option value="">Все состояния</option><option>На согласование</option><option>Согласовано по номенклатуре</option><option>Отклонено</option></select><select id="problem" aria-label="Замечания"><option value="">Все строки</option><option value="yes">С замечаниями или риском упаковки</option><option value="no">Без выявленных замечаний</option></select><select id="sort" aria-label="Сортировка"><option value="money">Сначала дорогие</option><option value="row">Порядок исходного файла</option></select><button onclick="window.print()">Печать</button></div><p id="count" aria-live="polite"></p><div class="scroll"><table><thead><tr><th>Строка / ERP</th><th>Что требуется</th><th>Количество</th><th>Состояние</th><th>Сумма заявки</th><th>Проблема → действие</th></tr></thead><tbody id="rows"></tbody></table></div></section>
<section><h2>Как читать</h2><p>Количество заявлено — потребность по заявке. «Согласовано по номенклатуре» — этап согласования позиции. Утверждение, приёмка и оплата — отдельные события. В этой выгрузке все утверждённые и принятые количества/суммы равны нулю; отсутствие поставки в реальности этим не доказано.</p><p>Главный экран показывает 6 колонок вместо 79. В раскрытии строки сохранены цена, сумма без НДС, комментарий и роль ответственного. Полные исходные поля и правила анализа доступны в соседнем отчёте analysis.md. Расчёты выполнялись до округления, на экране деньги округлены до копеек.</p><p class="sub">Локальный прототип: не отправляет данные в сеть. Фильтры меняют только просмотр.</p></section></main><script>
const data=__DATA__;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rub=n=>n==null?'нет данных':Number(n).toLocaleString('ru-RU',{minimumFractionDigits:2,maximumFractionDigits:2})+' ₽';
function action(r){let a=[];for(const p of r.problems){let next='Уточнить актуальность замечания и решение у ответственного';if(p.includes('техническое задание'))next='Подготовить или привязать ТЗ';else if(p.includes('нормативу'))next='Уточнить минимальную партию и кратность';else if(p.includes('Отказ'))next='Уточнить причину отказа и нового поставщика';else if(p.includes('выписан'))next='Проверить выдачу со склада и остаточную потребность';else if(p.includes('ГОСТ'))next='Проверить нормативный документ и допустимую замену';else if(p.includes('PCS'))next='Сверить штуку/упаковку и цену с предложением поставщика';a.push(esc(p)+' → '+esc(next));}return a.join('<br>')||'Замечаний в проверенных полях нет; обеспеченность не подтверждена';}
function render(){let q=document.querySelector('#query').value.toLowerCase(),s=document.querySelector('#state').value,p=document.querySelector('#problem').value;let rr=data.filter(r=>(!s||r.status===s)&&(!p||(r.problems.length>0)===(p==='yes'))&&(!q||[r.name,r.erp,r.reason,r.comment].join(' ').toLowerCase().includes(q)));rr.sort(document.querySelector('#sort').value==='row'?(a,b)=>a.row-b.row:(a,b)=>Number(b.amount)-Number(a.amount));document.querySelector('#count').textContent='Показано '+rr.length+' из '+data.length+' строк. Суммы по фильтру не являются новым бюджетом.';document.querySelector('#rows').innerHTML=rr.map(r=>`<tr><td>${r.row}<br><small>${esc(r.erp)}</small></td><td>${esc(r.name)}<details><summary>Подробности</summary>Цена: ${rub(r.price)}<br>Сумма без НДС: ${rub(r.net)}<br>Комментарий: ${esc(r.comment)||'—'}<br>Роль: ${esc(r.owner)}<br>Утверждено: ${r.approved}; принято: ${r.received}</details></td><td>${esc(r.qty)} ${esc(r.unit)}</td><td>${esc(r.status)}</td><td>${rub(r.amount)}</td><td>${action(r)}</td></tr>`).join('');}
for(const id of ['query','state','problem','sort'])document.getElementById(id).addEventListener('input',render);render();
</script></html>'''.replace('__DATA__', data)
    (OUT / 'review.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    main()
