"""Source-reviewed prompt repairs; never changes recorded experiment results.

Run from this checkout. ARML transcription is bound to original PDF bytes.
Mystery Hunt rows are isolated puzzles: declare benchmark rules instead of
applying the unrelated 2026 full-hunt FAQ to historical editions.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from artifacts.reviewed_pdf_text import ARML_2013_SHA256, ARML_2013_TEXT


def main():
    backup = ROOT / 'tmp' / ('prompt_integrity_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    changed = []
    def read(p):
        return json.loads(p.read_text(encoding='utf-8'))
    def write(p, obj):
        content = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode()
        if p.read_bytes() == content:
            return
        dst = backup / p.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        changed.append(str(p.relative_to(ROOT)))
        p.write_bytes(content)

    contamination = ' Chimneys receives a code-quality estimate, never an invented measured output/reference ratio.'
    old_limit = 'No claim of compilation, official test execution, official all-cases credit or measured Chimneys quality ratio.'
    clean_limit = 'No claim of compilation, official test execution or official all-cases credit.'
    for base in (ROOT / 'data', ROOT / 'data/mini_data'):
        path = base / 'benchmarks/arml_local/benchmark.json'
        rows = read(path)
        for row in rows:
            if row['problem_id'] == 'arml_local_2013':
                source = ROOT / row['source_file']
                assert hashlib.sha256(source.read_bytes()).hexdigest() == ARML_2013_SHA256
                row['problem_description'] = ARML_2013_TEXT
                row.setdefault('provenance', {})['statement_review'] = {
                    'method': 'visual transcription of original problem page; no solution used',
                    'source_sha256': ARML_2013_SHA256, 'pdf_page': 1,
                    'printed_page': 346, 'reviewed_at': '2026-09-17'}
        write(path, rows)
        path = base / 'benchmarks/iiot/benchmark.json'
        rows = read(path)
        for row in rows:
            if row['problem_id'] != 'iiot_2021_01':
                row['problem_description'] = row['problem_description'].replace(contamination, '')
                ev = row.get('evaluation', {})
                if 'limitations' in ev:
                    ev['limitations'] = [v.replace(old_limit, clean_limit) for v in ev['limitations']]
        write(path, rows)
        path = base / 'rules/iiot/competition.json'
        card = read(path)
        card['rules_text'] = card['rules_text'].replace(contamination, '')
        write(path, card)
        for path in (base / 'rubrics').glob('iiot_2021_*_source_review_v1.json'):
            if path.name.startswith('iiot_2021_01_'):
                continue
            obj = read(path)
            obj['not_observable_from_deck'] = [v.replace(old_limit, clean_limit) for v in obj['not_observable_from_deck']]
            write(path, obj)

        directory = base / 'rules/mystery_hunt'
        path = directory / 'competition.json'
        card = read(path)
        card['execution']['rules_edition'] = 'isolated_puzzle_benchmark'
        card['team']['official_roster_note'] = '8-12 active agents, default 12, is a benchmark configuration; no historical official roster rule is asserted.'
        card['human_constraints'] = [
            'This is one archived puzzle from the year recorded on the benchmark task, not the complete annual hunt.',
            'Submit the answer to the provided puzzle. Full-hunt unlocking, live interactions, runarounds, winner eligibility and coin-finding are not reproduced.',
            'The configured team and resource restrictions are benchmark adaptations, not verified historical event rules.',
            'Do not access hidden answers or solution pages or obtain answers from other teams.']
        card['rules_text'] = ('Isolated archived Mystery Hunt puzzle benchmark. Use the puzzle statement and its recorded edition. '
            'No rules from another annual hunt apply. Submit one shared puzzle answer. '
            'Benchmark roster: 8-12 active agents, default 12; the single-agent baseline uses one agent. '
            'Benchmark resources: internet and code execution allowed; calculators and assistance from other teams forbidden; paper and pencil allowed. '
            'These resource choices are experimental controls, not claims about the original hunt. '
            'Do not access answer keys or hidden solutions. Full-hunt progression, interactions, runarounds and coin-finding are unavailable.')
        # Historical provenance remains in the byte-for-byte backup, not in live
        # rule queries where an obsolete FAQ could again become instructions.
        card['provenance'] = {
            'status': 'benchmark_adaptation', 'rules_scope': 'isolated_archived_puzzle',
            'sources': [], 'official_rules_verified': False,
            'adaptations': ['Roster and resource policy retained as benchmark controls.',
                            'Task year and puzzle source are supplied by each benchmark record.'],
            'proxy_limitations': ['Historical full-hunt rules are not reproduced.'],
            'source_correction_revision': '2026-09-17-prompt-integrity'}
        write(path, card)
        path = directory / 'collaboration.json'
        obj = read(path)
        obj['rule_sections'] = {
            'competition_format': card['human_constraints'][:3],
            'timeline': ['Use the configured benchmark turn and API budgets; no official historical duration is asserted.'],
            'resource_policy': [card['rules_text']],
            'collaboration_protocol': [card['team']['collaboration'], card['team']['official_roster_note']],
            'integrity_and_compliance': [card['human_constraints'][3]],
            'deliverable_format': ['Submit one answer for the provided archived puzzle.'],
            'evaluation_criteria': ['Use the per-record evaluator; puzzle answer matching is not a full-hunt victory.'],
            'runtime_limitations': [card['human_constraints'][1]]}
        obj['simulation']['turn_budget_basis'] = 'Benchmark safety budget, not verified official wall-clock duration.'
        write(path, obj)
        path = directory / 'evaluation.json'
        obj = read(path)
        for key in ('official_performance', 'official_scoring'):
            block = obj['scoring'][key]
            block['source_refs'] = []
            block['mechanics'] = ['Per-record archived puzzle answer checking only; no full-hunt scoring claim.']
            if 'criteria' in block:
                block['criteria'] = ['Match the provided puzzle answer using its registered evaluator.']
                block['source_status'] = 'benchmark_adaptation'
                block['source_review_status'] = 'historical_full_hunt_rules_not_verified'
        write(path, obj)
    if changed:
        (backup / 'manifest.json').write_text(json.dumps(changed, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'backup': str(backup), 'changed': changed}, indent=2))


if __name__ == '__main__':
    main()
