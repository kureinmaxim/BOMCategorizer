"""Independent oracles: identity, conservation, explicit quantities, source provenance.

Known defects deliberately FAIL, rather than asserting current defective behavior.
No equivalence of distinct part numbers is assumed without an explicit rule.
"""
import pandas as pd
import pytest
from docx import Document
from bom_categorizer.parsers import parse_txt_like, parse_docx, count_from_reference
from bom_categorizer.main import aggregate_duplicate_items, multiply_quantities, create_outputs_dict
from bom_categorizer.classifiers import classify_row
from bom_categorizer.formatters import clean_component_name
from bom_categorizer.tru_merger import (
    find_matching_tru_row, extract_nominal, merge_tru_into_bom,
    generate_unmatched_report, build_ostatki_and_zapas_reports,
)
from bom_categorizer.tru_rkm_processor import process_tru_files_batch, process_rkm_file

def tru(names, quantities=None):
    return pd.DataFrame({'Наименование': names, 'Количество': quantities or [1]*len(names),
                         'Артикул': [str(101+i) for i in range(len(names))], 'Цена': [10]*len(names)})

def match(a, b):
    return find_matching_tru_row(a, extract_nominal(a), tru([b]))

@pytest.mark.parametrize('a,b', [
    ('МДМ30-1В12ТУП', 'МДМ30-1В15ТУП'),
    ('ABC123456-A', 'ABC123456-B'),
    ('Резистор С2-33 100 Ом 1%', 'Резистор С2-33 100 Ом 5%'),
    ('Конденсатор К10-17 100 нФ 16В', 'Конденсатор К10-17 100 нФ 50В'),
    ('Микросхема ABC123', 'Микросхема ABC1234'),
])
def test_distinct_complete_part_identity_is_not_auto_matched(a, b):
    assert match(a, b) is None, 'Different complete identity needs rejection/manual review'

def test_blank_name_is_not_identity():
    assert find_matching_tru_row('', '', tru(['Микросхема ABC123'])) is None

def test_ambiguous_short_code_is_not_resolved_by_row_order():
    candidates = tru(['Микросхема ABC123-A', 'Микросхема ABC123-B'])
    assert find_matching_tru_row('ABC123', '', candidates) is None

def test_unmatched_erp_stays_with_its_row():
    result = generate_unmatched_report([tru(['AAA123', 'BBB456'])], {0})
    assert result.iloc[0]['КОД ERP(МР)'] == '102'

def test_tru_quantity_and_cost_are_not_spent_twice():
    bom = pd.DataFrame({'Наименование ИВП': ['ABC123', 'ABC123'], 'шт.': [2, 3]})
    merged, indices, _ = merge_tru_into_bom(bom, [tru(['ABC123'], [5])])
    # Supply 5 and demand 2+3: there can be no excess; cost 5*10 may be allocated once.
    _, excess = build_ostatki_and_zapas_reports(merged, indices)
    assert excess.empty and pd.to_numeric(merged['Стоимость']).sum() == 50

def test_explicit_zero_supply_produces_full_shortage():
    bom = pd.DataFrame({'Наименование ИВП': ['ABC123'], 'шт.': [5]})
    merged, indices, _ = merge_tru_into_bom(bom, [tru(['ABC123'], [0])])
    shortage, _ = build_ostatki_and_zapas_reports(merged, indices)
    assert not shortage.empty and shortage['шт.'].sum() == 5

def test_grouped_thousands_are_numeric_not_prefix():
    bom = pd.DataFrame({'Наименование ИВП': ['ABC123'], 'шт.': [1000]})
    merged, indices, _ = merge_tru_into_bom(bom, [tru(['ABC123'], ['1 000'])])
    shortage, excess = build_ostatki_and_zapas_reports(merged, indices)
    assert shortage.empty and excess.empty and merged.iloc[0]['Стоимость'] == 10000

def test_quantity_strings_are_added_arithmetically():
    data = pd.DataFrame({'description': ['ABC123', 'ABC123'], 'qty': ['2', '3']})
    result = aggregate_duplicate_items(data, 'description')
    assert float(result.iloc[0]['qty']) == 5

def test_different_mpns_are_not_duplicates():
    data = pd.DataFrame({'description': ['Резистор', 'Резистор'], 'partnumber': ['ABC123-A', 'ABC123-B'], 'qty': [2, 3]})
    assert len(aggregate_duplicate_items(data, 'description')) == 2

def test_output_quantity_column_accepts_multiplier():
    assert multiply_quantities(pd.DataFrame({'шт.': [3]}), 2).iloc[0]['шт.'] == 6

def test_fractional_quantity_is_not_truncated():
    assert multiply_quantities(pd.DataFrame({'qty': [1.5], 'unit': ['м']}), 2).iloc[0]['qty'] == 3

def test_txt_without_qty_keeps_description(tmp_path):
    p = tmp_path / 'bom.txt'
    p.write_text('R1;Резистор 100 Ом', encoding='utf-8')
    assert parse_txt_like(str(p)).iloc[0]['description'] == 'Резистор 100 Ом'

def docx_input(tmp_path, qty, note=''):
    doc = Document()
    table = doc.add_table(rows=2, cols=4)
    for cell, text in zip(table.rows[0].cells, ['Поз.', 'Наименование', 'Количество', 'Примечание']):
        cell.text = text
    for cell, text in zip(table.rows[1].cells, ['R1', 'Резистор ABC123', qty, note]):
        cell.text = text
    p = tmp_path / 'bom.docx'
    doc.save(p)
    return p

def test_docx_explicit_zero_is_preserved(tmp_path):
    assert parse_docx(str(docx_input(tmp_path, '0'))).iloc[0]['qty'] == 0

def test_docx_explicit_grouped_integer_is_preserved(tmp_path):
    assert parse_docx(str(docx_input(tmp_path, '1 000'))).iloc[0]['qty'] == 1000

def test_docx_selection_note_survives_for_extractor(tmp_path):
    df = parse_docx(str(docx_input(tmp_path, '1', 'с подбором ABC456')))
    assert 'ABC456' in df.iloc[0]['original_note']

def test_short_real_component_remains_in_output(monkeypatch):
    monkeypatch.setattr('bom_categorizer.classifiers.get_component_category', lambda _: None)
    name = clean_component_name('Микросхема NE555')
    cat = classify_row('', name, None, None, strict=True)
    outputs = create_outputs_dict(pd.DataFrame({'description': [name], 'qty': [2], 'category': [cat]}))
    assert sum(len(v) for v in outputs.values()) == 1

def test_cyrillic_reference_range_is_counted():
    assert count_from_reference('С1-С3') == 3

def test_tru_nbsp_quantity_is_preserved(tmp_path):
    p, out = tmp_path / 'input.xlsx', tmp_path / 'output.xlsx'
    tru(['ABC123'], ['1\u00a0000']).to_excel(p, index=False)
    ok, message = process_tru_files_batch([str(p)], str(out))
    assert ok, message
    assert pd.read_excel(out).iloc[0]['Количество'] == 1000

def test_rkm_provider_provenance_is_not_lost(tmp_path):
    # Two purchases of one item from distinct vendors: both vendors must remain traceable.
    rows = [['№ п/п', 'Наименование'] + [None]*22]
    for provider in ['Поставщик А', 'Поставщик Б']:
        row = [None]*24
        row[0:2] = ['2.1.1', 'ABC123']
        row[17:20] = [1, 10, 10]
        row[22] = provider
        rows.append(row)
    p, out = tmp_path / 'rkm.xlsx', tmp_path / 'result.xlsx'
    pd.DataFrame(rows).to_excel(p, index=False, header=False)
    ok, message = process_rkm_file(str(p), str(out))
    assert ok, message
    vendors = ' '.join(pd.read_excel(out)['Поставщик'].dropna().astype(str))
    assert 'Поставщик А' in vendors and 'Поставщик Б' in vendors

@pytest.mark.parametrize('a,b', [
    ('Микросхема ABC123', 'Микросхема ABC123'),
    ('0603НР-47NXJ', '0603HP-47NXJ'),
    ('Резистор С2-33 6.8 Ом', 'Резистор С2-33 6,8 Ом'),
])
def test_documented_equivalent_spellings_match(a, b):
    assert match(a, b) is not None

def test_different_nominal_is_rejected():
    assert match('Резистор С2-33 100 Ом', 'Резистор С2-33 200 Ом') is None

def test_same_item_numeric_quantities_are_conserved():
    df = pd.DataFrame({'description': ['ABC123', 'ABC123'], 'qty': [2, 3]})
    assert aggregate_duplicate_items(df, 'description').iloc[0]['qty'] == 5

def test_rkm_preserves_metre_unit(tmp_path):
    row = [None]*24
    row[0:2] = ['2.1.1', 'Провод МГТФ 0,12']
    row[5] = 'м'
    row[17:20] = [300, 12.37, 3711]
    p, out = tmp_path / 'rkm.xlsx', tmp_path / 'result.xlsx'
    pd.DataFrame([['№ п/п', 'Наименование'] + [None]*22,row]).to_excel(p, index=False, header=False)
    assert process_rkm_file(str(p), str(out))[0]
    df = pd.read_excel(out)
    assert any('м' == str(v) for v in df.iloc[0]), 'Source unit must survive, metres cannot become pieces'

def test_comparison_detects_changed_standard_output_quantity(tmp_path):
    from bom_categorizer.main import compare_processed_files
    a, b, out = [tmp_path / n for n in ['a.xlsx','b.xlsx','comparison.xlsx']]
    for p,q in [(a,2),(b,3)]:
        pd.DataFrame({'Наименование ИВП':['ABC123'], 'шт.':[q]}).to_excel(p, sheet_name='Микросхемы', index=False)
    assert compare_processed_files(str(a),str(b),str(out))
    all_values = ' '.join(str(v) for df in pd.read_excel(out,sheet_name=None).values() for v in df.to_numpy().ravel())
    assert 'ABC123' in all_values, 'Changed item must be present in comparison report'

def test_summary_preserves_cost_from_standard_output(tmp_path):
    from bom_categorizer.excel_writer import write_categorized_excel
    df = pd.DataFrame({'Наименование ИВП':['ABC123'], 'шт.':[2], 'Стоимость':[20]})
    out = tmp_path / 'summary.xlsx'
    write_categorized_excel({'ics':df},df,str(out),True,'Наименование ИВП')
    summary = pd.read_excel(out,sheet_name='SUMMARY')
    assert summary.iloc[0]['Стоимость'] == 20

def test_tru_re_read_does_not_add_total_as_component(tmp_path):
    from bom_categorizer.tru_rkm_processor import _read_tru_file
    p, out = tmp_path/'source.xlsx',tmp_path/'processed.xlsx'
    tru(['ABC123'],[2]).to_excel(p,index=False)
    assert process_tru_files_batch([str(p)],str(out))[0]
    parsed = _read_tru_file(str(out))
    assert len(parsed) == 1 and parsed.iloc[0]['Наименование'] == 'ABC123'
