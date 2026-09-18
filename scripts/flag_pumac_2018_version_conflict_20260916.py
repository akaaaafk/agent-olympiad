"""Do not offer a directly runnable task whose reference solves altered questions."""
from copy import deepcopy
from pathlib import Path
import sys
import pymupdf
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    report_path = 'data/judge_references/pumac_2018_version_conflict_20260916.json'
    if (ROOT/report_path).exists():
        raise RuntimeError('Frozen batch exists; do not replay')
    store = Store(ROOT, ROOT.parent/'dataset_backups')
    path = 'data/benchmarks/pumac_power/benchmark.json'
    rows = deepcopy(store.read(path))
    row = next(r for r in rows if r['year'] == 2018)
    texts = []
    for key in ['source_file', 'solution_file']:
        with pymupdf.open(ROOT/row[key]) as pdf:
            texts.append(''.join(p.get_text() for p in pdf))
    ids = ['1.1.5', '2.3.3', '3.3.2', '4.2.3', '4.2.4', '4.3.5']
    excerpts = {}
    for tid in ids:
        excerpts[tid] = []
        for text in texts:
            start = text.index('Problem '+tid)
            end = text.find('\nProblem ', start+1)
            excerpts[tid].append(text[start:end if end >= 0 else len(text)][:2500])
    note = ('Official archive problem and solution PDFs have matching IDs but changed question statements '
            '(including 1.1.5, 4.2.3, 4.2.4) and inconsistent weights. Current archived remote bytes '
            'match the local files; this is not a local download error. Correct version correspondence '
            'is unresolved; do not grade the original task against the altered reference.')
    row['evaluation'].update(status='not_ready', readiness_reason=note)
    row.setdefault('source_review', {})['version_conflict'] = dict(report_path=report_path, changed_statement_ids=ids)
    report = dict(role='judge_only', archive_url='https://pumac.princeton.edu/archives',
        source_sha256=store.sha(row['source_file']), solution_sha256=store.sha(row['solution_file']),
        remote_hashes_verified_equal=True, statement_excerpts=excerpts, conclusion=note)
    store.save(path, rows)
    store.save(report_path, report)
    store.finish(report)
    print('Backup:', store.backup)


if __name__ == '__main__':
    main()
