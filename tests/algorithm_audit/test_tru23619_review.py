"""Business invariants for the standalone financial review, without network calls."""
import importlib.util
from pathlib import Path
from decimal import Decimal
import pytest

spec = importlib.util.spec_from_file_location('review', Path(__file__).with_name('build_tru23619_review.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def row():
    r = [''] * 79
    for c,v in {0:'00017',1:'Деталь',4:2,5:'кг',8:50,9:100,22:50,23:100,
                37:'limit-1',39:1000,40:50,41:40,64:'Согласовано по номенклатуре',71:0,74:0}.items():
        r[c] = v
    return r


def test_budget_repetitions_do_not_multiply_available_money():
    records, groups, budgets = review.summarize([row(), row()])
    assert len(records) == 2
    assert sum(v[0] for v in budgets.values()) == Decimal('1000')
    assert records[0]['erp'] == '00017'
    assert records[0]['approved'] == 0
    assert groups['Согласовано по номенклатуре']['amount'] == Decimal('200')


def test_conflicting_budget_cannot_produce_financial_conclusion():
    second = row()
    second[40] = 60
    with pytest.raises(ValueError, match='Противоречивый лимит'):
        review.summarize([row(), second])


def test_packaging_is_warning_not_automatic_quantity_conversion():
    r = row()
    r[1],r[4],r[8],r[9] = 'TAPE SEAL 30 PCS',21,10,210
    records,_,_ = review.summarize([r])
    assert records[0]['qty'] == 21
    assert any('упаковка' in p for p in records[0]['problems'])


def test_zero_and_missing_prices_are_different():
    zero, missing = row(),row()
    zero[8],zero[9],missing[8] = 0,0,''
    records,_,_ = review.summarize([zero,missing])
    assert 'Не хватает числовых данных' not in records[0]['problems']
    assert 'Не хватает числовых данных' in records[1]['problems']


def test_unit_price_rounding_is_not_overspending():
    r = row()
    r[4],r[22],r[23] = 150,184.43,27663.93
    records,_,_ = review.summarize([r])
    assert not any('сверх округления' in p for p in records[0]['problems'])


def test_funding_gap_only_for_confirmed_extra_reservation():
    assert review.funding_scenario(120,50,'excluded',True)['gap'] == 70
    assert review.funding_scenario(120,50,'included',True)['gap'] is None
    assert review.funding_scenario(120,50,'unknown',True)['gap'] is None
    assert review.funding_scenario(120,50,'excluded',False)['gap'] is None
    assert review.funding_scenario(20,50,'excluded',True)['gap'] == 0


def test_actual_export_reconciles_without_summing_budget_copies():
    import json
    rows = json.loads((review.OUT / 'raw.json').read_text(encoding='utf-8'))[2:]
    records,groups,budgets = review.summarize(rows)
    assert len(records) == 106
    assert len({r['erp'] for r in records}) == 106
    assert sum((g['amount'] for g in groups.values()),Decimal(0)) == Decimal('925652.0021')
    assert groups['Отклонено'] == {'count':7,'amount':Decimal('4520.7452')}
    assert len(budgets) == 1
    assert sum(bool(r['reason']) for r in records) == 55
    assert all(r['approved'] == r['received'] == 0 for r in records)
    assert not any('Сумма не равна количеству × цене' in r['problems'] for r in records)
    for r in rows:
        assert abs(review.dec(r[9])-review.dec(r[23])*(1+review.dec(r[24])/100)) <= Decimal('0.01')
    manifest = json.loads((review.OUT / 'manifest.json').read_text(encoding='utf-8'))
    source = Path(manifest['path'])
    if source.exists():
        import hashlib
        assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['sha256']
