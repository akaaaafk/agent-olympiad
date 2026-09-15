"""Prepare judge-only test assets with explicit pairing and filename-alias evidence."""
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_data_catalog import Store,provenance
from scripts.repair_iol_sources_20260913 import read,sha,require

CACHE='data/.cache/iiot_2023_test_recovery_20260913/'


def aliases(files):
    standard=[f for f in files if f['kind']=='input' and re.fullmatch(r'input\d+\.txt',f['name'])]
    extra=[f for f in files if f['kind']=='input' and not re.fullmatch(r'input\d+\.txt',f['name'])]
    found=[]; unresolved=[]
    for f in extra:
        matched=[s for s in standard if s['sha256']==f['sha256']]
        basis='identical_file_sha256'
        if not matched:
            data=(ROOT/f['cache']).read_bytes()
            matched=[s for s in standard if (ROOT/s['cache']).stat().st_size <= len(data)+4
                and (ROOT/s['cache']).read_bytes().rstrip(b'\r\n')==data.rstrip(b'\r\n')]
            basis='byte_equality_after_removing_only_trailing_CR_LF'
        if len(matched)==1:
            found.append(dict(alias=f['name'],standard_input=matched[0]['name'],evidence=basis,
                alias_sha256=f['sha256'],standard_sha256=matched[0]['sha256'],not_an_additional_case=True))
        else: unresolved.append(dict(name=f['name'],candidate_names=[m['name'] for m in matched]))
    return found,unresolved


def prepare():
    store=Store(ROOT); download=read(ROOT/CACHE/'download_plan.json'); result=read(ROOT/CACHE/'download_results.json')
    require(not result['failures'],'Downloads failed')
    files=result['files']
    require(len(files)==len(download['jobs'])==728,'Unexpected download count')
    require({(f['task'],f['kind'],f['id'],f['name']) for f in files}=={(f['task'],f['kind'],f['id'],f['name']) for f in download['jobs']},'Download membership differs')
    for f in files:
        require(sha(ROOT/f['cache'])==f['sha256'],'Cached source changed')
        require((ROOT/f['cache']).stat().st_size==f['verified_bytes'],'Cached size changed')
    path='data/benchmarks/iiot/benchmark.json'; rows=read(ROOT/path); updates=[]; new=[]; summaries=[]
    for task in download['tasks']:
        task_files=[f for f in files if f['task']==task['task']]
        before=next(r for r in rows if r.get('year')==2023 and r.get('task_code')==task['task']); row=deepcopy(before)
        base='data/raw/iiot/2023/'+task['task']+'/'; byname={}; archived=[]
        for f in task_files:
            destination=base+'tests/'+f['kind']+'/'+f['name']
            byname[(f['kind'],f['name'])]=destination
            new.append(dict(source=f['cache'],destination=destination,sha256=f['sha256']))
            row['assets'].append(dict(path=destination,mime_type='text/plain',role='judge_only',sha256=f['sha256']))
            archived.append(dict(path=destination,name=f['name'],kind=f['kind'],sha256=f['sha256'],bytes=f['verified_bytes'],
                publisher_file_id=f['id'],source_url=f['source_url'],folder_url=f['parent_folder'],listing_url=f['listing_url']))
        pairs=[dict(id=str(i),input=byname[('input',f'input{i}.txt')],output=byname[('output',f'output{i}.txt')],
                    pairing_basis='same numeric ID in publisher inputN.txt and outputN.txt filenames') for i in task['pair_ids']]
        alias,unresolved=aliases(task_files)
        manifest=dict(task_code=task['task'],year=2023,official_archive_url=row['source_url'],publisher_test_folder=task['source_url'],
            reference_manifest=row['evaluation']['source_archive_manifest'],files=archived,test_pairs=pairs,input_aliases=alias,
            unresolved_alias_files=unresolved,official_test_pair_count=len(pairs),
            listing_scope='All files visible in the publisher-linked public embedded folder views at discovery time; no claim about unpublished/private files.',
            discovered_at_utc=download['discovered_at_utc'],ordinary_view_truncation_avoided=True,
            test_subtask_mapping=None,checker_configuration=None,execution_limits=None,programs_executed=False)
        manifest_path=base+'test_source_manifest.json'; manifest_cache=CACHE+task['task']+'/test_source_manifest.json'
        store.save(manifest_cache,manifest); new.append(dict(source=manifest_cache,destination=manifest_path,sha256=sha(ROOT/manifest_cache)))
        row['assets'].append(dict(path=manifest_path,mime_type='application/json',role='judge_only',sha256=new[-1]['sha256']))
        limitations=['All publicly listed test files are archived; original test-to-subtask assignments, checker configuration and execution limits remain unavailable.',
            'Reference source has not been compiled or executed in an isolated judge; test presence does not establish runtime readiness.',
            'Contestant template files mentioned in the statement are not supplied by this test-folder archive.']
        if unresolved: limitations.append('Some additional input filenames have no uniquely verified standard-input correspondence; see manifest.')
        if task['task']=='tetris': limitations.append('The statement permits multiple valid constructions; expected-output text equality is not a valid general checker.')
        row['evaluation'].update(test_source_manifest=manifest_path,official_test_pair_count=len(pairs),
            archived_test_files=len(archived),verified_input_alias_count=len(alias),
            source_repair_status='publisher_reference_subtask_weights_and_public_test_files_archived',
            reason='Official public test files and reference sources are archived; missing original judge configuration still prevents official automatic grading.',
            limitations=limitations)
        provenance(row); updates.append(dict(before=before,after=row))
        summaries.append(dict(task=task['task'],pairs=len(pairs),files=len(archived),input_aliases=len(alias),unresolved_aliases=len(unresolved)))
    plan=dict(competition_id='iiot',benchmark_path=path,expected_benchmark_sha256=sha(ROOT/path),updates=updates,new_files=new,
        report_path='data/benchmarks/iiot_2023_test_recovery_20260913.json',
        summary=dict(tasks=summaries,official_test_pairs=sum(t['pairs'] for t in summaries),downloaded_files=len(files),
                     downloaded_bytes=sum(f['verified_bytes'] for f in files),all_test_assets_judge_only=True,
                     original_scores_unchanged=True,programs_executed=False))
    store.save(CACHE+'apply_plan.json',plan)
    print(json.dumps(plan['summary'],ensure_ascii=False,indent=2))


if __name__=='__main__': prepare()
