"""Register edition-specific case-deck rubrics after reviewing original PDFs."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard, update_track_index
from enable_open_artifact_judges import criterion, ANCHORS

CASES = {
    2019: ('General Motors', 'Tesla', 'acquire', 'Value 100% of Tesla equity with DCF and/or multiples; acquisition feasibility and expected ROI.', 'How Tesla fits the General Motors portfolio.'),
    2020: ('Amazon', 'Netflix', 'acquire', 'Value 100% of Netflix equity with DCF and/or multiples; acquisition feasibility and expected ROI.', 'How Netflix fits the Amazon portfolio and streaming strategy.'),
    2023: ('Siemens', 'Vestas', 'acquire', 'Value both companies, justify methodology, assess feasibility, profitability, financing and FX risk.', 'Renewable-energy capabilities and ESG implications.'),
    2024: ('IBM', 'Equinix', 'acquire', 'Value both companies, justify methodology, assess feasibility, profitability and financing.', 'Cloud/data-center capabilities and data-protection implications.'),
    2025: ('Ferrari', 'Pirelli', 'acquire', 'Value both companies, justify methodology, assess feasibility, profitability and financing.', 'Capabilities, technological innovation, branding, market position and potential risks.'),
    2026: ('Thales', 'Rheinmetall', 'merge with', 'Value both companies, justify methodology, assess merger feasibility, profitability and financing.', 'Technology, sovereignty, scale, European market positioning and potential risks.'),
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    data = ROOT / 'data'
    path = data / 'benchmarks/gcch_harvard/benchmark.json'
    rows = read(path)
    staged, originals, promoted = {}, {}, []
    backup = ROOT / 'tmp' / ('before_main_gcch_expansion_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    def put(path, value):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    for row in rows:
        if row['year'] not in CASES or row['evaluation']['status'] != 'not_ready':
            continue
        buyer, target, operation, financial, special = CASES[row['year']]
        assets = [a for a in row['assets'] if a['role'] == 'agent_visible']
        assert len(assets) == 1 and assets[0]['path'].endswith('.pdf')
        asset = assets[0]
        pdf = ROOT / asset['path']
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == asset['sha256']
        doc = pymupdf.open(pdf)
        assert len(doc) == 7
        text = '\n'.join(page.get_text() for page in doc)
        assert buyer.casefold() in text.casefold() and target.casefold() in text.casefold()
        criteria = [criterion(key, name, 20, desc + ' ' + ANCHORS) for key, name, desc in [
            ('recommendation', 'Recommendation and executive summary', f'Assess the clear, evidence-supported answer to whether {buyer} should {operation} {target}. Executive summary should communicate the core argument in at most one slide.'),
            ('context', 'Company and industry context', f'Assess relevant history, operations, market position, strategic direction and industry context for {buyer} and {target}.'),
            ('financial', 'Financial due diligence', financial + ' Require dated sources, explicit assumptions, reproducible calculations and uncertainty; do not infer later outcomes.'),
            ('strategic', 'Strategic due diligence', 'Assess synergies, integration threats, complementary capabilities and industry implications. ' + special),
            ('conclusion', 'Balanced conclusion and alternatives', 'Balance supporting and opposing evidence. If recommending the transaction, explain deal structure and next steps; otherwise give defensible alternative strategies. A different deck structure is acceptable.')]]
        limitations = [f'Five recommended analysis topics in the original {row["year"]} case operationalized as five equal 20-point benchmark criteria.',
            'These weights and anchors are benchmark choices, not published official judge weights.',
            'Evaluate only the submitted deck, not oral delivery, live Q&A or an official event ranking.']
        instructions = ('This is an offline archival AI research benchmark, not an entry to the original human competition. '
            'Produce the requested case-analysis deck. Use the original case requirements and dated evidence; identify assumptions explicitly. '
            'The five written-analysis criteria are each worth 20 benchmark points. Historical submission dates are context, not present deadlines. '
            'Do not submit to event websites, email addresses or named organizers.')
        if row['year'] >= 2024:
            instructions += (' The original event prohibits generative-AI-written decks; that rule remains in the archived PDF. '
                'This explicitly adapted offline benchmark permits AI-generated decks and does not claim compliance with that original participation restriction.')
            limitations.append('Original human-event AI prohibition is preserved; this offline AI benchmark explicitly differs from that participation rule.')
        ev = row['evaluation']
        ev['before_main_case_judge'] = deepcopy(ev)
        rp = data / 'rubrics' / (row['problem_id'] + '_deck_review_v1.json')
        rubric = dict(rubric_id=rp.stem, title=f'{row["year"]} {buyer} / {target} case-deck review',
            total_points=100, criteria=criteria, not_observable_from_deck=limitations,
            provenance=dict(source_path=asset['path'], source_sha256=asset['sha256'], source_pages=[4,5,6],
                weight_basis='Equal benchmark weights for the five recommended analysis topics in this exact case.', official_score_equivalent=False))
        put(rp, rubric)
        ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations', rubric_path=rp.relative_to(ROOT).as_posix(),
            reference_policy='rubric_only', grading_scope='written_case_deck_benchmark', official_score_equivalent=False,
            limitations=limitations, benchmark_instructions=instructions,
            score_basis=rubric['provenance']['weight_basis'], reason='Original seven-page case reviewed; edition-specific deck rubric registered.')
        row['total_points'] = 100
        row['gold_label']['grading_rubric'] = ev['rubric_path']
        promoted.append(row['problem_id'])
    put(path, rows)
    for base in [data, data / 'mini_data']:
        p = base / 'rules/gcch_harvard/evaluation.json'
        rules = read(p)
        for row in rows:
            if row['problem_id'] not in promoted:
                continue
            src = ROOT / row['evaluation']['rubric_path']
            dest = base / 'rubrics' / src.name
            if base != data:
                put(dest, json.loads(staged[src].decode().replace('data/', 'data/mini_data/')))
            rules['scoring']['record_evaluator_overrides'][row['problem_id']] = 'rubric_llm_v1'
            rules['scoring']['record_rubric_overrides'][row['problem_id']] = dest.relative_to(ROOT).as_posix()
        current = rows if base == data else read(base / 'benchmarks/gcch_harvard/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in current) for s in {r['evaluation']['status'] for r in current}}
        put(p, rules)
    ip = data / 'benchmarks/index.json'
    index = read(ip)
    update_track_index(index, 'gcch_harvard', rows)
    put(ip, index)
    sp = data / 'rubrics/task_scorecards/gcch_harvard.json'
    cards = read(sp)
    cards['records'] = [scorecard(r, ROOT,
        read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
        hash_file=lambda p: hashlib.sha256(staged[ROOT / p] if ROOT / p in staged else (ROOT / p).read_bytes()).hexdigest()) for r in rows]
    put(sp, cards)
    put(ROOT / 'tmp/main_gcch_expansion_20260917.json', dict(promoted=promoted, scope='Edition-specific written case deck', mini_membership_changed=False, paid_calls=0))
    for path, before in originals.items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] is not None:
            dest = backup / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(promoted=len(promoted), backup=str(backup))))


if __name__ == '__main__':
    main()
