"""Recover printed item weights, checking reference coverage and cover sheets."""
from copy import deepcopy
from pathlib import Path
import re
import sys
import pymupdf
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store


def text(path):
    with pymupdf.open(ROOT / path) as pdf:
        return ''.join(p.get_text() for p in pdf)


def main():
    report_path = 'data/judge_references/pumac_item_weights_20260916.json'
    if (ROOT / report_path).exists():
        raise RuntimeError('Frozen batch exists; do not replay')
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    path = 'data/benchmarks/pumac_power/benchmark.json'
    rows = deepcopy(store.read(path))
    mapping_path = 'data/rubrics/pumac_power_official_rubrics.json'
    mapping = deepcopy(store.read(mapping_path))
    report = dict(role='judge_only', before_sha256=store.sha(path), records={})
    for row in rows:
        year = row['year']
        if year not in {2012, 2016, 2019}:
            continue
        statement, reference = text(row['source_file']), text(row['solution_file'])
        if year == 2012:
            pattern = r'(?m)^(\d+\.\d+)\s*\n\((\d+) points\)'
            matches = list(re.finditer(pattern, statement))
            refs = list(re.finditer(pattern, reference))
            weights = [(m[1], int(m[2])) for m in matches]
            assert weights == [(m[1], int(m[2])) for m in refs] and len(weights) == 14
        elif year == 2016:
            matches = list(re.finditer(r'(?m)^Problem (\d+\.\d+)[. (]', statement))
            # Source 4.2 prints the typo "2 poitns"; the cover sheet independently confirms 1+1.
            weights = [(m[1], int(re.search(r'\((\d+) (?:points|poitns)\)', statement[m.start():m.start()+120])[1])) for m in matches]
            refs = list(re.finditer(r'(?m)^Problem (\d+\.\d+)\.', reference))
            assert [m[1] for m in refs] == [m[1] for m in matches]
            cover = statement[statement.rfind('Team Number:'):]
            cover_weights = re.findall(r'(?m)^(\d+\.\d+)(?: \([a-z]\))?\s*\n(\d+)\s*$', cover)
            grouped = {}
            for tid, weight in cover_weights:
                grouped[tid] = grouped.get(tid, 0) + int(weight)
            assert dict(weights) == grouped and sum(grouped.values()) == 350
        else:
            cover = statement[statement.rfind('Team Number:'):]
            weights = [(m[0], int(m[1])) for m in re.findall(r'(?m)^(\d+\.\d+\.\d+)\s*\n(\d+)\s*$', cover)]
            ref_weights = dict((m[0], int(m[1])) for m in re.findall(r'(?m)^(\d+\.\d+\.\d+)\s*\n\[(\d+) points\]', reference))
            assert '2.2.4 and 2.2.5\n[30+30 points]' in reference
            ref_weights.update({'2.2.4': 30, '2.2.5': 30})
            assert dict(weights) == ref_weights and len(weights) == 36
            matches = list(re.finditer(r'(?m)^Problem (\d+\.\d+\.\d+)[. (]', statement))
            refs = []
            assert [m[1] for m in matches] == [tid for tid, _ in weights]
        assert len(dict(weights)) == len(weights)
        total = sum(w for _, w in weights)
        assert total == {2012: 110, 2016: 350, 2019: 1025}[year], (year, total)
        criteria = []
        for i, (tid, weight) in enumerate(weights):
            item_statement = statement[matches[i].start():matches[i+1].start() if i+1 < len(matches) else len(statement)]
            if refs:
                item_reference = reference[refs[i].start():refs[i+1].start() if i+1 < len(refs) else len(reference)]
            else:
                # Shared-reference sections remain together; do not invent a missing proof.
                header = '2.2.4 and 2.2.5' if tid in {'2.2.4', '2.2.5'} else tid
                found = re.search(r'(?m)^' + re.escape(header) + r'\s*\n\[', reference)
                assert found, tid
                next_header = re.search(r'(?m)^\d+\.\d+\.\d+(?: and \d+\.\d+\.\d+)?\s*\n\[', reference[found.end():])
                end = found.end()+next_header.start() if next_header else len(reference)
                item_reference = reference[found.start():end]
            criteria.append(dict(id='problem_' + tid, name='Problem ' + tid, max_score=weight, observable=True,
                description='Grade only this numbered problem, requiring justified proofs and accepting valid alternatives. '
                    'Respect printed subpart weights, counting the parent maximum once. Reference pointers to external proofs '
                    'do not supply those proofs; assess the submitted proof directly. Detailed partial-credit calibration is benchmark judgment.\nSTATEMENT:\n'
                    + item_statement + '\nOFFICIAL REFERENCE (JUDGE ONLY):\n' + item_reference))
        rp = f'data/rubrics/pumac_power_{year}_official_items_v2.json'
        store.save(rp, dict(rubric_id=f'pumac_power_{year}_official_items_v2', role='judge_only',
            title=f'PUMaC {year} printed problem maxima', total_points=total, criteria=criteria,
            official_solution_file=row['solution_file'], official_solution_sha256=store.sha(row['solution_file'])))
        row['total_points'] = total
        row['evaluation'].update(rubric_path=rp,
            score_basis='Printed numbered problem maxima with source/reference correspondence; official-reference LLM proof assessment.')
        mapping[row['problem_id']].update(official_total_points=total, official_problem_maxima=weights,
            coverage='all_numbered_item_maxima_source_and_reference_checked',
            allocation_note='2019 shared reference for 2.2.4/2.2.5 kept intact. References containing external proof pointers remain limited; no official human partial-credit equivalence claimed.')
        report['records'][row['problem_id']] = dict(weights=weights, total_points=total,
            source_sha256=store.sha(row['source_file']), solution_sha256=store.sha(row['solution_file']))
    store.save(path, rows)
    store.save(mapping_path, mapping)
    store.save(report_path, report)
    store.finish(report)
    print('Backup:', store.backup)


if __name__ == '__main__':
    main()
