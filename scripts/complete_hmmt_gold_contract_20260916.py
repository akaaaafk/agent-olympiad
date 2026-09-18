"""Publish per-packet scoring mode IDs without gold values; add notation aliases."""
from copy import deepcopy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store


def main():
    report_path='data/judge_references/hmmt_gold_contract_20260916.json'
    if (ROOT/report_path).exists():raise RuntimeError('Frozen contract exists; do not replay')
    store=Store(ROOT,ROOT.parent/'dataset_backups')
    path='data/benchmarks/hmmt_team/benchmark.json'
    rows=deepcopy(store.read(path));report=dict(role='judge_only',before_sha256=store.sha(path),packets={})
    for row in rows:
        ids=[]
        for part in row['gold_label']['parts']:
            expected=part.get('expected')
            if expected is None:continue
            ids.append(part['id'])
            if expected=='sqrt(3)/2':part['aliases']=['(sqrt(3))/(2)','\\frac{\\sqrt{3}}{2}','sqrt(3)/2']
            elif expected=='7/2':part['aliases']=['(7)/(2)','3.5','\\frac{7}{2}']
            elif expected=='2013^4025':part['aliases']=['2013^{4025}']
            elif expected=='1, 2, 3, 4':part['aliases']=['{1,2,3,4}','1;2;3;4']
        contract=('\n\nBENCHMARK SUBMISSION AND SCORING CONTRACT:\n'
            'Keep problem numbering. For final-answer gold parts '+(', '.join(ids) if ids else '(none)')+
            ', start the response with a separate line of the form "N. final answer"; optional reasoning may follow. '
            'These parts receive their printed maximum for a correct final answer and zero otherwise. '
            'All other parts require complete proofs or reasoning and are scored by an official-reference LLM judge. '
            'This is a benchmark scoring adaptation; the original HMMT requires proof even for numerical results. '
            'Do not put multiple alternative final answers on one line.')
        row['problem_description']+=contract
        report['packets'][row['problem_id']]=dict(public_gold_part_ids=ids,source_prompt_preserved_as_prefix=True)
    store.save(path,rows);store.save(report_path,report);store.finish(report)
    print('Backup:',store.backup)


if __name__=='__main__':main()
