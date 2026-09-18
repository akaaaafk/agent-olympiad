"""Package EOES 2024 contestant inputs for scoped written experimental analysis."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import os
import tempfile
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import update_track_index
from enable_remaining_mini_judges import criterion

CASES = {
    'eoes_TASK1': (1, 45, 27,
        'Fe2+ quantification, chemical identification, ionizing radiation, UV effects on cell growth and genetic material. '
        'Treat microscopy, radiation counts, absorbance and actual PCR outcomes as NOT MEASURED unless supplied; '
        'distinguish expected PCR results requested by the task from observed results.'),
    'eoes_T2': (2, 50, 39,
        'Lemonade and mustard analysis, looping mechanics, LEDs and diffraction, osmosis and fish-scale analysis. '
        'Do not invent specimen observations, measured voltages, microscopy drawings or fish ages. '
        'Distinguish supplied example diagrams from the unobserved assigned specimens.'),
}


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    data = ROOT / 'data'
    bp = data / 'benchmarks/eoes/benchmark.json'
    rows = read(bp)
    before, staged, promoted = {}, {}, []
    backup = ROOT / 'tmp' / ('before_eoes_2024_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    def put(p, v):
        before[p] = p.read_bytes() if p.exists() else None
        staged[p] = v if isinstance(v, bytes) else (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    registry_path = data / 'problem_pdf_allowlist.json'
    registry = read(registry_path)
    rubrics = {}
    for row in rows:
        if row['problem_id'] not in CASES or row['evaluation']['status'] != 'not_ready':
            continue
        day, task_pages, answer_pages, focus = CASES[row['problem_id']]
        visible = [a for a in row['assets'] if a['role'] == 'agent_visible']
        assert len(visible) == 2
        for a in row['assets']:
            assert hashlib.sha256((ROOT / a['path']).read_bytes()).hexdigest() == a['sha256']
        packet = pymupdf.open()
        sources = []
        for asset, count in zip(visible, [task_pages, answer_pages]):
            with pymupdf.open(ROOT / asset['path']) as source:
                assert len(source) == count
                packet.insert_pdf(source)
            sources.append(dict(path=asset['path'], sha256=asset['sha256'], pages=count,
                role='task_sheet' if not sources else 'blank_answer_sheet'))
        dest = data / f'raw/eoes/eoes/2024/task_{day}_with_blank_answers.pdf'
        raw = packet.tobytes()
        packet.close()
        put(dest, raw)
        merged = dict(path=dest.relative_to(ROOT).as_posix(), mime_type='application/pdf', role='agent_visible',
            sha256=hashlib.sha256(raw).hexdigest())
        instructions = (
            'Written experimental-analysis benchmark: address the task and paired blank answer sheet by section and question. '
            'Solve questions using supplied constants, tables and figures. For missing experimental measurements, '
            'give a reproducible protocol, formulas, required inputs, expected relationships and uncertainty analysis; label the result NOT MEASURED. '
            'Never invent readings, laboratory actions, assessor observations or signatures. '
            'Supplied specimen photos, spectra, tables and biological diagrams are evidence; inspect original PDF pages when text extraction omits them. '
            'Do not replace unavailable measurements with sample values or marking-scheme example measurements. '
            'The report is worth 100 benchmark points: scientific reasoning 30, methods 25, supplied-data analysis 30, uncertainty/evidence integrity 15. '
            'These are written-analysis weights, not the official practical examination score. '
            f'Focus: {focus} Packet pages 1-{task_pages} are task sheets; '
            f'pages {task_pages + 1}-{task_pages + answer_pages} are blank answer sheets.')
        limitations = ['Written scientific analysis only; laboratory execution, measurements and observer signatures are not scored.',
            '100-point written-analysis benchmark, not official 2024 practical marks.',
            'Official marking files remain judge_only; this rubric-only route does not use example measurements as contestant evidence.',
            'Some supplied figures are visual; text-only providers cannot recover image-only evidence.']
        rubric = dict(rubric_id=f'eoes_2024_task{day}_written_analysis_v1', title=f'EOES 2024 Task {day} written analysis',
            total_points=100, criteria=[
                criterion('reasoning', 'Scientific reasoning', 30, 'Assess correct scientific reasoning across the actual task sections. ' + focus),
                criterion('methods', 'Experimental methods', 25, 'Assess task-specific protocols, controls, calibration and feasible procedures. Describe methods only; do not assume laboratory work was executed. ' + focus),
                criterion('analysis', 'Supplied-data analysis', 30, 'Check calculations, units, spectra, graphs and conclusions against supplied data. For missing measurements assess correct symbolic derivation and required inputs. Never reward invented readings or substitute marking examples.'),
                criterion('uncertainty', 'Uncertainty and evidence integrity', 15, 'Assess error propagation and distinction between supplied, derived and NOT MEASURED quantities. No credit for fabricated readings, observations or signatures.')],
            not_observable_from_deck=limitations,
            provenance=dict(sources=sources, weight_basis='Explicit written-analysis benchmark weights 30/25/30/15, reused from the scoped EOES 2021 approach.', official_score_equivalent=False))
        rp = data / 'rubrics' / (rubric['rubric_id'] + '.json')
        put(rp, rubric)
        rubrics[row['problem_id']] = (rp, rubric)
        ev = row['evaluation']
        ev['before_eoes_2024_analysis'] = deepcopy(ev)
        ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations', rubric_path=rp.relative_to(ROOT).as_posix(),
            reference_policy='rubric_only', grading_scope='written_artifact_benchmark', official_score_equivalent=False,
            benchmark_instructions=instructions, limitations=limitations, score_basis=rubric['provenance']['weight_basis'],
            reason='Paired original task and blank answer sheets packaged for explicitly scoped written analysis.')
        row['problem_description'] += '\n\n' + instructions
        row['assets'] = [merged] + [a for a in row['assets'] if a['role'] == 'judge_only']
        row['total_points'] = 100
        row['gold_label']['grading_rubric'] = ev['rubric_path']
        row.setdefault('source_review', {})['eoes_2024_packet'] = dict(sources=sources, merged_asset=merged,
            task_pages=task_pages, blank_answer_pages=answer_pages)
        row['provenance']['files'] = deepcopy(row['assets'])
        registry['assets'] = [a for a in registry['assets'] if a.get('problem_id') != row['problem_id']]
        registry['assets'].append(dict(problem_id=row['problem_id'], path=merged['path'], sha256=merged['sha256'],
            pages=list(range(1, task_pages + answer_pages + 1)), review_status='approved_problem_only',
            review_evidence='2026-09-17: original task sheets followed by blank participant answer sheets; original marking files excluded. Reviewed representative task/data/blank-form pages in tmp/eoes_2024_review.'))
        promoted.append(row['problem_id'])
    if not promoted:
        print('EOES 2024 already prepared; no changes.')
        return
    put(bp, rows)
    put(registry_path, registry)
    for base in [data, data / 'mini_data']:
        p = base / 'rules/eoes/evaluation.json'
        rules = read(p)
        for key, (rp, rubric) in rubrics.items():
            dest = base / 'rubrics' / rp.name
            if base != data:
                put(dest, json.loads(json.dumps(rubric).replace('data/', 'data/mini_data/')))
            rules['scoring']['record_evaluator_overrides'][key] = 'rubric_llm_v1'
            rules['scoring']['record_rubric_overrides'][key] = dest.relative_to(ROOT).as_posix()
        selected = rows if base == data else read(base / 'benchmarks/eoes/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = dict(Counter(r['evaluation']['status'] for r in selected))
        put(p, rules)
    p = data / 'benchmarks/index.json'
    index = read(p)
    update_track_index(index, 'eoes', rows)
    put(p, index)
    put(ROOT / 'tmp/main_eoes_2024_expansion.json', dict(promoted=promoted, scope='Written experimental analysis only', paid_calls=0))
    for p, v in before.items():
        assert (p.read_bytes() if p.exists() else None) == v, f'Concurrent edit: {p}'
    for p, v in staged.items():
        if before[p] is not None:
            dest = backup / p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(before[p])
        p.parent.mkdir(parents=True, exist_ok=True)
        assert (p.read_bytes() if p.exists() else None) == before[p], f'Concurrent edit before write: {p}'
        # Replace atomically so readers never see a truncated catalog; Windows
        # can reject truncation of an existing file retained by another reader.
        with tempfile.NamedTemporaryFile(dir=p.parent, prefix=p.name + '.', suffix='.tmp', delete=False) as out:
            out.write(v)
            temporary = out.name
        os.replace(temporary, p)
    print(json.dumps(dict(promoted=len(promoted), backup=str(backup))))


if __name__ == '__main__':
    main()
