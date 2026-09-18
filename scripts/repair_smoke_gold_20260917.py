"""Two source-verified gold encodings exposed by live mini smoke; no LLM calls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts

CASES = {
    'qanta': 'qanta_train_119982',
    'science_bowl': 'science_bowl_sample_set_10_10a_hs_reg_2016_toss_up_17',
}
SCIENCE_PDF_SHA = 'baf671508a6599c078eb6f08ae00ce4bcf0b31a2ca232643e6d7774691376212'


def main():
    smoke = ROOT / 'results/mini_live_smoke_20260917_1q_v2'
    backup = ROOT / 'tmp' / ('gold_encoding_repair_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    def read(p):
        return json.loads(p.read_text(encoding='utf-8'))
    for base in (ROOT / 'data', ROOT / 'data/mini_data'):
        for competition, problem_id in CASES.items():
            path = base / 'benchmarks' / competition / 'benchmark.json'
            rows = read(path)
            row = next(r for r in rows if r['problem_id'] == problem_id)
            source = ROOT / row['source_file']
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            part = row['gold_label']['parts'][0]
            if competition == 'qanta':
                source_row = next(r for r in read(source)['questions'] if r['qanta_id'] == 119982)
                assert source_row['answer'] == 'zero (accept equivalents like nothing)'
                expected, aliases = 'zero', ['nothing', '0']
                note = 'Upstream answer annotation explicitly accepts equivalents such as nothing; annotation is not part of the required answer.'
                assert part['expected'] in (source_row['answer'], expected)
            else:
                assert digest == SCIENCE_PDF_SHA
                expected, aliases = '30/x^7', []
                note = 'Visually reviewed original PDF page 9: derivative of -5/x^6; answer 30/x^7. Printed DO NOT ACCEPT: 30x^-7 remains excluded.'
                assert part['expected'] in ('30/x7', expected)
                row['problem_description'] = row['problem_description'].replace('x6?', 'x^6?')
            row['gold_label']['expected_answer'] = expected
            part.update(expected=expected, aliases=aliases, reference=note)
            row.setdefault('provenance', {})['gold_encoding_review'] = {
                'reviewed_at': '2026-09-17', 'source_sha256': digest,
                'source_file': row['source_file'], 'note': note}
            content = (json.dumps(rows, ensure_ascii=False, indent=2) + '\n').encode()
            if content != path.read_bytes():
                destination = backup / path.relative_to(ROOT)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
                path.write_bytes(content)

    selection = read(smoke / 'smoke_selection.json')
    audit = {}
    for competition, problem_id in CASES.items():
        choice = next(c for c in selection if c['competition'] == competition)
        path = smoke / 'runs' / choice['job_id'] / 'contest_session.json'
        original_bytes = path.read_bytes()
        result = read(path)
        row = next(r for r in read(ROOT / 'data/mini_data/benchmarks' / competition / 'benchmark.json')
                   if r['problem_id'] == problem_id)
        answer = result['submissions'][problem_id]
        score = GoldAnswerEvaluator(load_gold_parts(row['gold_label']), answer).evaluate()
        assert score.total_score == 1
        if competition == 'science_bowl':
            assert GoldAnswerEvaluator(load_gold_parts(row['gold_label']), '30x^-7').evaluate().total_score == 0
        audit[competition] = {'problem_id': problem_id, 'submission': answer,
            'raw_score': result['grade']['score'], 'raw_max_score': result['grade']['max_score'],
            'audited_score': score.total_score, 'audited_max_score': score.max_score,
            'method': 'deterministic reevaluation after source-verified gold encoding repair',
            'model_calls': 0, 'original_result_sha256': hashlib.sha256(original_bytes).hexdigest(),
            'review': row['provenance']['gold_encoding_review']}
        assert path.read_bytes() == original_bytes
    destination = smoke / 'score_audit/verified_corrections.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'backup': str(backup), 'audited_scores': {k: v['audited_score'] for k, v in audit.items()}, 'model_calls': 0}))


if __name__ == '__main__':
    main()
