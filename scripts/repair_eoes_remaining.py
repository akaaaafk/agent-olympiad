"""Source-backed written EOES adaptations; exclude incomplete source packets."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import uuid
import pymupdf
from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures
from src.dataset_catalog import update_track_index

PACKETS = {
    'eoes_EUSO 2013 _ TEST 1_TASK': ['2013/EUSO 2013 _ TEST 1_TASK.pdf', '2013/EUSO 2013 _ TEST 1_ANSWER SHEET.pdf'],
    'eoes_EUSO 2013 TEST 2 TASK 2': ['2013/EUSO 2013 TEST 2 TASK 2.pdf', '2013/EUSO 2013 TEST 2 ANSWER SHEET.pdf'],
    'eoes_tasksheet2': ['2015/tasksheet2.pdf', '2015/answersheet2.pdf', '2015/template_diagrampaper.pdf'],
    'eoes_Task_1_ICE': ['2017/Task_1_ICE.pdf', '2017/Task_1_ICE_Answer_Sheet.pdf',
                        '2017/Task_1_ICE_Appendix_A1.pdf', '2017/Task_1_ICE_Appendix_A2.pdf', '2017/Task_1_ICE_Appendix_C.pdf'],
}
EXCLUDE = {
    'eoes_P1Tasks': 'Referenced 2011 answer sheet is not archived.',
    'eoes_P2Tasks': 'Referenced 2011 answer sheet and optical-bench manual are not archived.',
    'eoes_cepelinai_articleEUSO': 'Recipe article, not a complete competition task packet.',
    'eoes_worshippers-of_scientific_method': 'Recipe article, not a complete competition task packet.',
    'eoes_euso2014_Task_A': 'Referenced 2014 task-specific answer sheet is not archived.',
    'eoes_euso2014_Task_B': 'Referenced 2014 task-specific answer sheet is not archived.',
    'eoes_Task_2_OCEAN': 'Required desktop copepod videos and Appendix C are not archived.',
}


def main():
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_eoes_' + uuid.uuid4().hex[:8])
    path = 'data/benchmarks/eoes/benchmark.json'
    rows = deepcopy(store.read(path))
    blocked = {r['problem_id'] for r in rows if r['evaluation']['status'] == 'not_ready'}
    assert blocked == set(PACKETS) | set(EXCLUDE), 'Source membership changed'
    mini = store.read('data/mini_data/benchmarks/eoes/benchmark.json')
    assert not set(EXCLUDE) & {r['problem_id'] for r in mini}
    source_root = ROOT / 'data/raw/eoes/euso'
    template = store.read('data/rubrics/eoes_mini_written_20260917_v1.json')
    report = {'competition': 'eoes', 'promoted': [], 'removed': [], 'packets': [],
              'paid_model_calls': 0, 'score_scope': 'Written scientific analysis only; benchmark 100-point rubric.'}
    output = ROOT / 'data/raw/eoes_repair_20260917'
    if output.exists():
        assert not (ROOT/'output/eoes_remaining_repair_20260917.json').exists(), 'Already published'
        store.archive(output)  # Recoverable failed-build residue only.
    output.mkdir(parents=True)
    for row in rows:
        pid = row['problem_id']
        if pid not in PACKETS:
            continue
        sources = [source_root / relative for relative in PACKETS[pid]]
        assert sources[0] == ROOT / row['source_file']
        for asset in row['assets']:
            assert hashlib.sha256((ROOT/asset['path']).read_bytes()).hexdigest() == asset['sha256']
        key = str(row['year']) + '_' + hashlib.sha256(pid.encode()).hexdigest()[:10]
        final = output / (key+'.pdf')
        bundle = PdfWriter()
        page_count = 0
        provenance = []
        for source in sources:
            original = pymupdf.open(source)
            assert len(original)
            start = page_count
            bundle.append(source)
            page_count += len(original)
            provenance.append({'path': source.relative_to(ROOT).as_posix(),
                               'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                               'pages': len(original), 'bundle_start_page': start+1})
        bundle.write(final)
        bundle.close()
        merged = pymupdf.open(final)
        # Verify every copied page's visual pixels, not just extracted text.
        index = 0
        for source in sources:
            original = pymupdf.open(source)
            for page in original:
                expected = page.get_pixmap(matrix=pymupdf.Matrix(.5,.5), alpha=False)
                actual = merged[index].get_pixmap(matrix=pymupdf.Matrix(.5,.5), alpha=False)
                assert (expected.width, expected.height) == (actual.width, actual.height)
                assert page.rect == merged[index].rect and page.get_text() == merged[index].get_text()
                assert expected.samples == actual.samples, (source.name, index+1)
                index += 1
        assert index == len(merged)
        merged[0].get_pixmap().save(str(output / (key+'-preview.png')))
        rubric_path = f'data/rubrics/eoes_{key}_written_analysis_v1.json'
        rubric = deepcopy(template)
        rubric.update(rubric_id='eoes_'+key+'_written_analysis_v1', title=pid+' written analysis',
                      provenance={'sources': provenance, 'official_score_equivalent': False,
                                  'weight_basis': 'Same-competition written benchmark operationalization: 30/25/30/15. Not official task weights.'})
        rubric['not_observable_from_deck'] = ['Physical experiments and measured performance are not scored.',
                                              'Missing measurements must be identified; no invented data.',
                                              '100-point written benchmark; not official historical scoring.']
        store.save(rubric_path, rubric)
        row.setdefault('provenance', {})['written_packet_review'] = provenance
        if row.get('total_points') is not None:
            row['provenance']['source_declared_total_points'] = row['total_points']
        row['total_points'] = 100
        row['problem_description'] += '\n\nWritten benchmark adaptation: use the supplied task, blank answer sheets and appendices. Submit scientific reasoning, feasible methods, calculations from supplied data and uncertainty analysis. Identify missing physical measurements and derive symbolically where possible. Never fabricate experimental results. Scored out of 100 using benchmark weights; not official experimental performance.\n'
        row['assets'] = [a for a in row['assets'] if a['role'] == 'judge_only'] + [{
            'path': final.relative_to(ROOT).as_posix(), 'role': 'agent_visible', 'mime_type': 'application/pdf',
            'sha256': hashlib.sha256(final.read_bytes()).hexdigest()}]
        row['evaluation'].update(status='ready_with_limitations', evaluator_id='rubric_llm_v1',
            rubric_path=rubric_path, deliverable='written_scientific_analysis',
            reason='Complete archived written packet assembled; executable same-competition benchmark rubric integrated.',
            limitations=rubric['not_observable_from_deck'],
            score_basis='100-point written scientific analysis benchmark; not official historical score.')
        report['promoted'].append(pid)
        report['packets'].append({'problem_id': pid, 'sources': provenance,
                                  'bundle': final.relative_to(ROOT).as_posix(), 'pages': index,
                                  'page_geometry_and_text_identical': True, 'all_page_pixels_identical': True})
    for row in rows:
        if row['problem_id'] in EXCLUDE:
            report['removed'].append({'record': row, 'reason': EXCLUDE[row['problem_id']]})
    rows = [r for r in rows if r['problem_id'] not in EXCLUDE]
    store.save(path, rows)
    rule_path = 'data/rules/eoes/evaluation.json'
    rule = store.read(rule_path)
    sync_rules('eoes', rule, rows)
    store.save(rule_path, rule)
    index = store.read('data/benchmarks/index.json')
    update_track_index(index, 'eoes', rows)
    store.save('data/benchmarks/index.json', index)
    summary_and_figures(store, index, {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']})
    store.save('output/eoes_remaining_repair_20260917.json', report)
    store.finish(report)
    print({'repaired': len(PACKETS), 'excluded': len(EXCLUDE), 'remaining': len(rows), 'backup': str(store.backup)})


if __name__ == '__main__':
    main()
