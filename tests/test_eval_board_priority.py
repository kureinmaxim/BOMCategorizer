"""Evaluation board identifiers take precedence over RF reference designators."""
import pytest
from docx import Document

from bom_categorizer import classifiers
from bom_categorizer.main import run_classification
from bom_categorizer.parsers import parse_docx


@pytest.mark.parametrize('name', ['EVAL-ADF4351EB1Z', 'EVAL - ADF4351EB1Z',
                                'eval–ADF4351EB1Z'])
@pytest.mark.parametrize('ref', ['W3', 'U1', ''])
def test_eval_identifier_precedes_reference(name, ref, monkeypatch):
    monkeypatch.setattr(classifiers, 'get_component_category', lambda _: None)
    assert classifiers.classify_row(ref, name, None, None, True) == 'dev_boards'


def test_docx_eval_and_adjacent_rf_components(tmp_path, monkeypatch):
    monkeypatch.setattr(classifiers, 'get_component_category', lambda _: None)
    document = Document()
    table = document.add_table(rows=1, cols=5)
    for cell, text in zip(table.rows[0].cells,
                          ['Зона', 'Поз. обозначение', 'Наименование', 'Кол.', 'Примечание']):
        cell.text = text
    for ref, name, qty in [
        ('W1-W4', 'Вентиль СВЧ ФВК3-28 ПЯ0.223.147 ТУ', '4'),
        ('W3', 'EVAL-ADF4351EB1Z Analog Devices', '1'),
        ('W4, W5', 'Усилитель ВЧ TB-TSS2-53LNBC+ MINI-CIRCUITS', '2'),
    ]:
        for cell, text in zip(table.add_row().cells, ['', ref, name, qty, '']):
            cell.text = text
    path = tmp_path / 'eval.docx'
    document.save(path)
    parsed = parse_docx(str(path))
    result = run_classification(parsed, 'reference', 'description', None, None, False)
    assert result['category'].tolist() == ['rf_modules', 'dev_boards', 'rf_modules']
    assert result['qty'].tolist() == [4, 1, 2]
