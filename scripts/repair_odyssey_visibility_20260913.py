"""Separate public practice-page instructions by the publisher's release boundary.

No stage controller or performance evaluator is added. Original source is retained.
"""
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import scorecard
from scripts.repair_data_catalog import Store,provenance
from scripts.repair_iol_sources_20260913 import read,sha,require

CID='odyssey_of_the_mind'
PID='odyssey_of_the_mind_spontaneous_examples_page'
TASK=CID+'/'+PID
RAW='data/raw/odyssey_of_the_mind/spontaneous/'
CACHE='data/.cache/odyssey_visibility_20260913/'
REPORT='data/excluded/benchmark_audit_reports/odyssey_visibility_repair_20260913.json'
TITLES=(
 'Verbal Spontaneous Problem: To Have Fun or Not to Have Fun?',
 'Verbal/Hands-On Spontaneous Problem: Creation Station',
 'Hands-On Spontaneous Problem:The Last Straw')


def clean(text):
    text=html.unescape(text).replace('\x01','')
    text=re.sub(r'\((\d+)\)',r'\1.',text)
    text=re.sub(r'\((1-10 poin\s*ts)\)',lambda m:'[printed scoring note: '+m[1].replace('poin ts','points')+']',text)
    text=re.sub(r'\([^()]*\)','',text)
    require('(' not in text and ')' not in text,'Nested/unknown parenthetical stage directions')
    text=re.sub(r'[^\S\n]+',' ',text)
    for old,new in {'t he':'the','th e':'the','w ill':'will','mig ht':'might','allow ed':'allowed',
                    'seco nds':'seconds','a llowed':'allowed','tabl e':'table','cr eate':'create',
                    'bri dge':'bridge','end s':'ends','s core':'score','yo u':'you','b ooks':'books',
                    't hat':'that','solut ion':'solution','toget her':'together'}.items():
        text=text.replace(old,new)
    text=re.sub(r' +([.,])',r'\1',text)
    return re.sub(r'\n\s*\n+', '\n\n',text).strip()


def split_source(text):
    """Known exact source; do not generalize these boundaries to other examples."""
    positions=[text.index(t) for t in TITLES]
    positions.append(text.index('Explore Problem 5: Performance',positions[-1]))
    parts=[]; hidden=[]
    for i,title in enumerate(TITLES):
        block=text[positions[i]+len(title):positions[i+1]]
        before,judge=block.split('C. FOR JUDGES ONLY:',1)
        _,readaloud=before.split('B. JUDGE READS TO TEAMS:',1)
        marker=('Part II: (Do not read to team until it completes Part I)',
                '(After reading Part I aloud, repeat items in boldface.',None)[i]
        if marker:
            initial,deferred=readaloud.split(marker,1)
            deferred=marker+deferred
            if i==0:
                require(initial.rstrip().endswith('In'),'Unexpected Part II transition')
                initial=initial.rstrip()[:-2].rstrip()
        else:
            initial=readaloud; deferred=None
        parts.append(dict(title=title,initial_read_aloud=clean(initial)))
        hidden.append(dict(title=title,deferred_read_aloud=deferred,judge_only='C. FOR JUDGES ONLY:'+judge.strip(),
                           release_rule='After Part I is complete' if marker else 'All section B instructions are read initially'))
    return parts,hidden


def prepare():
    store=Store(ROOT); path=f'data/benchmarks/{CID}/benchmark.json'
    rows=deepcopy(store.read(path)); before=next(r for r in rows if r['problem_id']==PID)
    original=ROOT/before['source_file']
    require(sha(original)=='413060b1417388d43b60edd29aa8122fea161ebbc47a49cfb1d6220a713f23ae','Unexpected publisher snapshot')
    parts,hidden=split_source(original.read_text(encoding='utf-8'))
    public='# Odyssey of the Mind — initial instructions from three public practice examples\n\n'
    public+='Source: https://odysseyofthemind.com/spontaneous/\n\n'
    public+='Archive note: These are three separate practice examples, not a combined tournament packet. '
    public+='Only initial instructions and their printed scoring notes are included below. Parenthetical judge directions, '
    public+='judge-only guidance, and later instructions explicitly withheld until Part I ends are excluded. '
    public+='Physical setup and staged delivery are not implemented by this text archive.\n\n'
    for p in parts: public+='## '+p['title']+'\n\n'+p['initial_read_aloud']+'\n\n'
    public=public.rstrip()+'\n'
    judge=dict(visibility='judge_only',source_file=before['source_file'],source_sha256=sha(original),
               examples=hidden,notes=['Original full source is retained byte-for-byte as judge-only.',
               'Page-wide seven-member statement and the older 35-card example are not silently reconciled.',
               'Judge setup directions describe physical materials; a complete environment is not synthesized.',
               'No runtime release gate or official scoring is implemented by this repair.'])
    source=RAW+'initial_examples.md'; judge_path=RAW+'staged_judge_instructions.json'
    texts={source:public,judge_path:json.dumps(judge,ensure_ascii=False,indent=2)+'\n'}
    row=deepcopy(before)
    row.update(source_file=source,problem_description=public.rstrip(),solution_file=None)
    row['assets']=[dict(path=source,mime_type='text/markdown',role='agent_visible',sha256=hashlib.sha256(public.encode()).hexdigest()),
        dict(before['assets'][0],role='judge_only'),
        dict(path=judge_path,mime_type='application/json',role='judge_only',sha256=hashlib.sha256(texts[judge_path].encode()).hexdigest())]
    row['evaluation'].update(source_repair_status='initial_and_deferred_judge_material_separated',
        initial_instruction_examples=3,staged_judge_instructions=judge_path,
        limitations=['Three public practice examples only; not a historical tournament packet.',
            'Physical setup, timed phase delivery and live creative-performance assessment are not implemented.',
            'Original example roster/card-count inconsistency remains documented rather than guessed.'])
    provenance(row)
    plan=dict(benchmark_path=path,before_row=before,after_row=row,texts=texts,source_hash=sha(original),
              original_source=before['source_file'],expected_benchmark_sha256=sha(ROOT/path))
    store.save(CACHE+'plan.json',plan)
    print(json.dumps(dict(examples=len(parts),initial_characters=len(public),retained_original=True)))


def apply():
    plan=read(ROOT/CACHE/'plan.json'); store=Store(ROOT)
    require(not (ROOT/REPORT).exists(),'Repair already applied; use verify')
    require(sha(ROOT/plan['benchmark_path'])==plan['expected_benchmark_sha256'],'Canonical data changed')
    require(sha(ROOT/plan['original_source'])==plan['source_hash'],'Original source changed')
    for p in plan['texts']: require(not (ROOT/p).exists(),'New path occupied: '+p)
    rows=deepcopy(store.read(plan['benchmark_path'])); row=plan['after_row']
    selected=next(r for r in rows if r['problem_id']==PID)
    require(selected==plan['before_row'],'Selected record changed')
    score_path=f'data/rubrics/task_scorecards/{CID}.json'
    scores=deepcopy(store.read(score_path))
    cards={layout:deepcopy(store.read(f'data/{layout}/task_cards.json')) for layout in ('base','last_exam')}
    manifests={layout:deepcopy(store.read(f'data/{layout}/input_asset_manifest.json')) for layout in cards}
    selected_cards={layout:next(c for c in cards[layout]['tasks'] if c['task_id']==TASK) for layout in cards}
    relative=selected_cards['base']['source_repo_path']
    require(relative==selected_cards['last_exam']['source_repo_path'],'Task path mismatch')
    # Prepare every old file and payload before the first mutation.
    writes={}; archives=[]
    for layout in cards:
        folder=f'data/{layout}/{relative}/base/input/'
        original_copy=folder+'spontaneous_examples.md'
        require(sha(ROOT/original_copy)==plan['source_hash'],'Staged source differs')
        archives.append(original_copy)
        writes[folder+'problem.md']=row['problem_description']+'\n'
        writes[folder+'initial_examples.md']=plan['texts'][row['source_file']]
        files=(selected_cards[layout]['input_files'] if layout=='base' else selected_cards[layout]['input']['files'])
        entry=next(f for f in files if f['name']=='spontaneous_examples.md')
        entry.update(name='initial_examples.md',path=('input/' if layout=='base' else 'base/input/')+'initial_examples.md')
        files.sort(key=lambda f:f['path'])
        entries=manifests[layout]['files']
        matching=[m for m in entries if m['task_id']==TASK]
        require(len(matching)==1 and matching[0]['sha256']==plan['source_hash'],'Unexpected input manifest')
        matching[0].update(source=row['source_file'],sha256=row['assets'][0]['sha256'],staged=relative+'/base/input/initial_examples.md')
    selected_cards['base'].update(evaluation=deepcopy(row['evaluation']))
    ref_path=f'data/last_exam/{relative}/eval/reference.json'
    ref=deepcopy(store.read(ref_path)); ref.update(evaluation=deepcopy(row['evaluation']))
    report=dict(status='applying',backup=store.backup.relative_to(ROOT).as_posix(),removed_from_initial_inputs=archives,
                original_source_retained=True,readiness_unchanged=True,scores_unchanged=True)
    store.finish(report)
    for p,t in {**plan['texts'],**writes}.items(): store.save_text(p,t)
    for p in archives: store.archive(p)
    selected.clear(); selected.update(row)
    old_card=next(c for c in scores['records'] if c['problem_id']==PID)
    old_card.clear(); old_card.update(scorecard(row,ROOT,read_json=store.read,hash_file=store.sha))
    store.save(plan['benchmark_path'],rows); store.save(score_path,scores); store.save(ref_path,ref)
    for layout in cards:
        store.save(f'data/{layout}/task_cards.json',cards[layout])
        store.save(f'data/{layout}/input_asset_manifest.json',manifests[layout])
    report.update(status='completed',verification=verify(plan))
    store.save(REPORT,report); store.finish(report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


def verify(plan=None):
    plan=plan or read(ROOT/CACHE/'plan.json'); row=plan['after_row']
    require(sha(ROOT/plan['original_source'])==plan['source_hash'],'Original changed')
    require(next(r for r in read(ROOT/plan['benchmark_path']) if r['problem_id']==PID)==row,'Record drift')
    for p,t in plan['texts'].items(): require((ROOT/p).read_text(encoding='utf-8')==t,'Source projection mismatch')
    for layout in ('base','last_exam'):
        card=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']==TASK)
        folder=ROOT/'data'/layout/card['source_repo_path']/'base/input'
        require(not (folder/'spontaneous_examples.md').exists(),'Full original still exposed')
        require((folder/'problem.md').read_text(encoding='utf-8')==row['problem_description']+'\n','Prompt differs')
        require((folder/'initial_examples.md').read_text(encoding='utf-8')==plan['texts'][row['source_file']],'Input differs')
        for f in folder.rglob('*.md'):
            text=f.read_text(encoding='utf-8')
            require('C. FOR JUDGES ONLY' not in text and 'Examples of Creative Responses' not in text,'Judge text exposed')
            require('pick any two of the creations' not in text and 'includes one item from each list' not in text,'Deferred prompt exposed')
            require(not any(ord(c)<32 and c not in '\n\r\t' for c in text),'Control character remains')
    require(row['total_points']==plan['before_row']['total_points'] and row['gold_label']==plan['before_row']['gold_label'],'Score/gold changed')
    return dict(initial_examples=3,staged_input_copies_verified=4,original_source_unchanged=True,
                judge_guidance_excluded=True,deferred_instructions_excluded=True,official_scoring_not_invented=True)


if __name__=='__main__':
    {'prepare':prepare,'apply':apply,'verify':lambda:print(json.dumps(verify(),indent=2))}[sys.argv[1]]()
