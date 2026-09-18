"""Summarize checked CTF expansion and refresh derived catalog visualizations."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store, summary_and_figures


def main():
    store = Store(ROOT, ROOT.parent/'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name+'_viz_'+uuid.uuid4().hex[:8])
    index = store.read('data/benchmarks/index.json')
    benchmarks = {t['id']:store.read(t['benchmark_path']) for t in index['olympiads']}
    assert sum(map(len,benchmarks.values())) == index['total_records']
    # Ensure the catalog snapshot has not changed while loading it.
    for path, content in store.raw.items():
        assert path.read_bytes() == content, f'Concurrent catalog edit: {path}'
    summary = summary_and_figures(store,index,benchmarks)
    store.finish({'operation':'refresh_derived_catalog_visualizations_after_ctf_expansion','records':summary['n_primary_records']})
    report = {'paid_model_calls':0,'scope':'Main CTF runtime readiness, not end-to-end solving; no single-agent context or WRO changes.',
              'visualization_backup':str(store.backup),'competitions':{}}
    for cid, stem in [('cybench','cybench'),('nyu_ctf_bench','nyu')]:
        runtime = json.loads((ROOT/f'output/ctf_docker/{stem}_expansion_20260917.json').read_text())
        preflight = json.loads((ROOT/f'output/ctf_docker/{stem}_expansion_preflight_20260917.json').read_text())
        assert preflight['passed']
        report['competitions'][cid] = {'runtime':dict(Counter(r['status'] for r in runtime['records'])),
            'preflight':preflight['counts'],'blocked':[r for r in runtime['records'] if r['status']!='passed']}
    # The original Store used second-resolution backup directories. Preserve a
    # separate promotion log for the two NYU operations that shared one directory.
    archive = ROOT.parent/'dataset_backups/integrity_repair_20260917T200647Z'
    promotion = {'operation':'nyu_ctf_promotion_reconstructed_from_retained_originals', 'files':[]}
    for relative in ['data/benchmarks/nyu_ctf_bench/benchmark.json','data/rules/nyu_ctf_bench/evaluation.json','data/mini_data/rules/nyu_ctf_bench/evaluation.json']:
        old = archive/relative
        assert old.is_file()
        promotion['files'].append({'path':relative,'before_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
                                  'after_sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()})
    with (archive/'ctf_promotion_manifest.json').open('x',encoding='utf-8') as f:
        json.dump(promotion,f,indent=2)
    destination = ROOT/'output/ctf_docker/full_data_expansion_20260917.json'
    with destination.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2)
    print(json.dumps({'records':summary['n_primary_records'],'status_counts':summary['evaluation_status_counts'],'report':str(destination)}))


if __name__ == '__main__':
    main()
