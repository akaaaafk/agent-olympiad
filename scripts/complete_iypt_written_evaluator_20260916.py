"""Align IYPT evaluator metadata with its written-document delivery contract."""
from copy import deepcopy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    report_path='data/judge_references/iypt_written_evaluator_20260916.json'
    if (ROOT/report_path).exists():raise RuntimeError('Frozen batch exists; do not replay')
    store=Store(ROOT,ROOT.parent/'dataset_backups')
    path='data/benchmarks/iypt/benchmark.json';rows=deepcopy(store.read(path))
    report=dict(role='judge_only',before_sha256=store.sha(path),records=[])
    for row in rows:
        assert row['evaluation']['assessment_scope']=='written_only'
        row['evaluation']['evaluator_id']='rubric_llm_v1'
        report['records'].append(row['problem_id'])
    store.save(path,rows);store.save(report_path,report);store.finish(report)
    print('Backup:',store.backup)


if __name__=='__main__':main()
