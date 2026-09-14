"""Frozen source-page release repair and version-specific printed maxima.

Original PDFs, experimental answers, membership and readiness are preserved.
No experimental or release controller is implemented.
"""
from copy import deepcopy
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import pymupdf
from scripts.repair_iol_sources_20260913 import ROOT, read, sha, require
from scripts.repair_data_catalog import Store, provenance
from scripts.repair_remaining_prompt_text_20260913 import Editor
sys.path.insert(0,str(ROOT/'src'))
from dataset_catalog import scorecard

CACHE='data/.cache/eoes_2015_scope_20260913/'
RAW='data/raw/eoes/separated_2015_20260913/'
PATH='data/benchmarks/eoes/benchmark.json'
REPORT='data/benchmarks/eoes_2015_scope_repair_20260913.json'
APPENDIX='eoes_additionalfileschallenge1'
PARENTS=['eoes_ExpBlowingintheWind','eoes_tasksheet1']
MAXIMA={PARENTS[0]:[92,92,92,6,24],PARENTS[1]:[90,92,92,6,24],'eoes_tasksheet2':[92,92,92,6,24]}
SELECTED={APPENDIX,*MAXIMA}
ORIGINAL='data/raw/eoes/euso/2015/additionalfileschallenge1.pdf'
PUBLIC=RAW+'challenge1_initial_handouts.pdf'


def verify_pdf(path):
    with pymupdf.open(ROOT/ORIGINAL) as source,pymupdf.open(path) as target:
        require(len(source)==4 and len(target)==2,'Wrong page membership')
        require(target.embfile_count()==0,'Embedded file in derived PDF')
        for i in range(2):
            a,b=source[i+2],target[i]
            require(a.rect==b.rect and a.rotation==b.rotation,'Page geometry changed')
            require(a.get_text()==b.get_text(),'Page text changed')
            require(a.get_pixmap(matrix=pymupdf.Matrix(2,2)).samples==b.get_pixmap(matrix=pymupdf.Matrix(2,2)).samples,'Rendered page differs')
            require(not b.get_links() and not list(b.widgets() or []),'Unexpected interactive PDF')
        require('Function' not in ''.join(p.get_text() for p in target),'Deferred table in initial PDF')


def repair_challenge2(text):
    e=Editor(text)
    # Only the visually reviewed page-2 overprinted hidden text is excluded.
    # The original PDF (including that text) remains unchanged and authoritative.
    e.rx(r'Challenge•  Eating2 consistsand.*?durch!\n        chemicals\.',
         '    •  Eating and drinking is strictly prohibited in the laboratory.\n'
         '    •  Disposable gloves are provided and should be worn while working with chemicals.')
    e.rx(r'\(formula 1\)\s*𝑛𝑛∙𝜆𝜆\s*𝑠𝑠𝑠𝑠𝑠𝑠𝛼𝛼𝑛𝑛=\s*𝑑𝑑', 'sin(α_n) = n · λ / d  (formula 1)\n')
    e.rx(r'\(formula 2\)\s*𝜎𝜎= ඨ\(𝑥𝑥𝑚𝑚−𝑥𝑥1\)2 \+ \(𝑥𝑥𝑚𝑚−𝑥𝑥2\)2 \+ \(𝑥𝑥𝑚𝑚−𝑥𝑥3\)2\s*3',
         'σ = sqrt(((x_m − x_1)^2 + (x_m − x_2)^2 + (x_m − x_3)^2) / 3)  (formula 2)')
    e.rep('The specific rotation angle     is a characteristic','The specific rotation angle [α] is a characteristic')
    e.rx(r'dissolved\s*\[𝛼𝛼\]\nsubstances\.', 'dissolved\nsubstances.')
    e.rx(r'\(formula 3\)\s*𝛼𝛼\s*\[𝛼𝛼\] = 𝑙𝑙∙𝑐𝑐∙100', '[α] = (α / (l · c)) · 100  (formula 3)\n')
    return e


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Frozen plan already exists')
    store=Store(ROOT);rows=read(ROOT/PATH);updates=[];copies=[]
    protected={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'data/raw/eoes').rglob('*') if p.is_file()}
    target=ROOT/CACHE/'challenge1_initial_handouts.pdf'
    if not target.exists():
        with pymupdf.open(ROOT/ORIGINAL) as source,pymupdf.open() as dest:
            # Fresh document + full garbage collection: the withheld page objects are
            # not retained in an incremental revision or a hidden page tree.
            dest.insert_pdf(source,from_page=2,to_page=3,links=False,annots=False)
            dest.save(target,garbage=4,deflate=True)
    verify_pdf(target)
    copies.append(dict(source=target.relative_to(ROOT).as_posix(),destination=PUBLIC,sha256=sha(target)))
    asset=dict(path=PUBLIC,role='agent_visible',mime_type='application/pdf',sha256=sha(target))
    release=dict(parent_problem_ids=PARENTS,original_source_file=ORIGINAL,original_sha256=sha(ROOT/ORIGINAL),
        initial_source_pages=[3,4],deferred_source_pages=[1,2],initial_file=PUBLIC,
        release_condition='Complete Task A 3.1 and hand the glued crayfish handout to the laboratory assistant before receiving the Function table and identification diagram.',
        evidence=[dict(source_file=next(r['source_file'] for r in rows if r['problem_id']==pid),pages=[4,6,7]) for pid in PARENTS],
        runtime_gate_implemented=False,official_left_right_assignment_inferred=False,
        limitations=['Original outline scale, placement, scan artifacts and unreadable source header are retained.',
                    'A specimen, glued extremities, lab-assistant photograph and complete answer-sheet packet are not supplied by this two-page extraction.'])
    for before in rows:
        pid=before['problem_id']
        if pid not in SELECTED:continue
        row=deepcopy(before);rev=row.setdefault('source_review',{})
        rev['eoes_2015_review']=dict(original_source_file=before['source_file'],original_sha256=sha(ROOT/before['source_file']))
        if pid in MAXIMA:
            with pymupdf.open(ROOT/before['source_file']) as doc:
                values=[int(x) for x in re.findall(r'Task [A-E]:\s*(\d+)\s*Marks',doc[1].get_text(sort=True))]
            require(values==MAXIMA[pid],'Printed version maxima differ')
            sections=[dict(id=letter,max_score=value,source_page=2) for letter,value in zip('ABCDE',values)]
            rubric=dict(rubric_id=pid+'_2015_printed_maxima_v1',total_points=sum(values),criteria=[],official_problem_maxima=sections,
                source_file=before['source_file'],source_sha256=sha(ROOT/before['source_file']),source_page=2,
                visibility='judge_only',executable=False,score_basis='Sum of the section maxima printed in this exact archived task-sheet variant; not a normalized tournament score.',
                limitations=['No task-specific numeric marking scheme or experimental measurements are inferred.','Challenge 1 variants have different printed maxima and must not be added as independent contest challenges.'])
            rp='data/rubrics/'+rubric['rubric_id']+'.json';cp=CACHE+Path(rp).name;store.save(cp,rubric)
            copies.append(dict(source=cp,destination=rp,sha256=sha(ROOT/cp)))
            row['assets'].append(dict(path=rp,role='judge_only',mime_type='application/json',sha256=sha(ROOT/cp)))
            row['total_points']=sum(values)
            ev=row['evaluation'];reuse=ev.pop('rubric_reuse',None)
            if reuse:ev['superseded_rubric_reuse']=reuse
            ev.update(rubric_path=rp,official_max_score=sum(values),official_problem_maxima=sections,
                score_basis=rubric['score_basis'],source_repair_status='variant_specific_printed_maxima_verified',
                limitations=rubric['limitations']+['Physical experiments, complete participant worksheets and edition-specific executable grading remain unverified.'])
        if pid in PARENTS or pid==APPENDIX:
            rev['eoes_2015_review']['release_scope']=release
            row['evaluation']['staged_source_release']=release
            if pid in PARENTS:
                row['assets'] += [deepcopy(asset),dict(path=ORIGINAL,role='judge_only',mime_type='application/pdf',sha256=sha(ROOT/ORIGINAL))]
                row['problem_description']='Archive note: `challenge1_initial_handouts.pdf` contains the original two outline pages for Task A 3.1. The Function table and identification diagram are deferred until the handout is submitted, as stated on task-sheet pages 4, 6 and 7. A live specimen and release controller are not supplied.\n\n'+row['problem_description']
                rev['eoes_2015_review']['same_challenge_variants']=PARENTS
            else:
                row['assets']=[deepcopy(asset)]+[dict(a,role='judge_only') for a in before['assets']]
                row['source_file']=PUBLIC
                row['problem_description']='EOES / EUSO 2015 Challenge 1 - initial supplementary handouts\n\nThis record is an appendix to Challenge 1 Task A, not an independent experiment or an additional score. Open `challenge1_initial_handouts.pdf` for the two original outline pages used in Task A 3.1. Preserve their original size and orientation; the source header is unreadable. Follow the parent task sheet for instructions and required physical materials.\n\nThe identification diagram and Function table are released only after the completed crayfish handout is handed to the laboratory assistant. They are not initial inputs. No live specimen, laboratory-assistant interaction or stage controller is supplied by this archive.'
                row['evaluation'].update(source_repair_status='supplementary_initial_and_deferred_pages_separated',
                    limitations=['Supplementary pages of Challenge 1, not a separately scoreable experiment.','Initial source pages 3 and 4 only; pages 1 and 2 require Task A 3.1 hand-in.','Physical materials and phased release are not implemented.'])
                rev['eoes_2015_review'].update(record_kind='supplementary_handout',independently_scoreable=False,parent_problem_ids=PARENTS)
        if pid=='eoes_tasksheet2':
            e=repair_challenge2(row['problem_description']);row['problem_description']=e.text
            rev['eoes_2015_review']['text_corrections']=e.changes
            rev['eoes_2015_review']['visually_reviewed_text_pages']=[2,20,23,28]
        provenance(row);updates.append(dict(before=before,after=row))
    require(len(updates)==4,'Unexpected scope')
    plan=dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=rows,updates=updates,copies=copies,protected=protected,
              pdf_derivation=release,summary='4 EOES 2015 records: scoped appendix and two Challenge 1 variants; printed totals 306/304/306, three formulas restored; no readiness promotion.')
    store.save(CACHE+'plan.json',plan)
    print(json.dumps(dict(records=len(updates),copies=len(copies),scores={u['after']['problem_id']:u['after']['total_points'] for u in updates}),indent=2))


def apply():
    plan=read(ROOT/CACHE/'plan.json');store=Store(ROOT)
    require(not (ROOT/REPORT).exists(),'No blind replay')
    require(sha(ROOT/PATH)==plan['expected_benchmark_sha256'],'Canonical source drift')
    rows=deepcopy(plan['before_rows']);cards={l:read(ROOT/f'data/{l}/task_cards.json') for l in ('base','last_exam')}
    manifests={l:read(ROOT/f'data/{l}/input_asset_manifest.json') for l in cards}
    scores=read(ROOT/'data/rubrics/task_scorecards/eoes.json');writes={};payloads=list(plan['copies']);archives=[];protected=deepcopy(plan['protected'])
    for t in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if t['benchmark_path']!=PATH:protected[t['benchmark_path']]=sha(ROOT/t['benchmark_path'])
    for u in plan['updates']:
        row=u['after'];before=u['before'];pid=row['problem_id'];task='eoes/'+pid
        oldpublic={Path(a['path']).name:a for a in before['assets'] if a['role']=='agent_visible'}
        public={Path(a['path']).name:a for a in row['assets'] if a['role']=='agent_visible'}
        for layout in cards:
            card=next(c for c in cards[layout]['tasks'] if c['task_id']==task);relative=card['source_repo_path'];folder=f'data/{layout}/{relative}/base/input/'
            for p in (ROOT/folder).iterdir():
                if p.is_file():protected[p.relative_to(ROOT).as_posix()]=sha(p)
            for name,a in oldpublic.items():require(sha(ROOT/folder/name)==a['sha256'],'Staged old asset differs')
            for name in oldpublic.keys()-public.keys():archives.append(folder+name);protected.pop(folder+name)
            for name,a in public.items():
                if name in oldpublic:require(a==oldpublic[name],'Unexpected same-name replacement')
                else:
                    source=next(c['source'] for c in plan['copies'] if c['destination']==a['path'])
                    payloads.append(dict(source=source,destination=folder+name,sha256=a['sha256']))
                    entry=dict(name=name,path=('input/' if layout=='base' else 'base/input/')+name)
                    if layout=='base':entry['description']='Agent-visible input'
                    (card['input_files'] if layout=='base' else card['input']['files']).append(entry)
            files=card['input_files'] if layout=='base' else card['input']['files']
            files[:]=sorted([f for f in files if f['name'] not in oldpublic.keys()-public.keys()],key=lambda f:f['path'])
            manifests[layout]['files'][:]=[m for m in manifests[layout]['files'] if m['task_id']!=task]
            manifests[layout]['files'] += [dict(task_id=task,source=a['path'],sha256=a['sha256'],staged=relative+'/base/input/'+name) for name,a in public.items()]
            writes[folder+'problem.md']=row['problem_description']+'\n';protected.pop(folder+'problem.md')
            if layout=='base':card.update(evaluation=deepcopy(row['evaluation']),solution_file=row.get('solution_file'))
            else:
                rp=f'data/last_exam/{relative}/eval/reference.json';ref=read(ROOT/rp)
                ref.update(evaluation=deepcopy(row['evaluation']),rubric_path=row['evaluation'].get('rubric_path'));writes[rp]=ref
        r=next(r for r in rows if r['problem_id']==pid);r.clear();r.update(row)
    # New rubric paths do not exist until copied. Build scorecards afterwards.
    for p,h in protected.items():require(sha(ROOT/p)==h,'Protected preflight drift')
    for c in payloads:
        require(not (ROOT/c['destination']).exists(),'Destination occupied')
        require(sha(ROOT/c['source'])==c['sha256'],'Prepared bytes changed')
    expected={p:sha(ROOT/p) for p in writes}
    for p in [PATH,'data/rubrics/task_scorecards/eoes.json']+[f'data/{l}/{n}.json' for l in cards for n in ('task_cards','input_asset_manifest')]:expected[p]=sha(ROOT/p)
    for p,h in expected.items():require(sha(ROOT/p)==h,'Concurrent metadata change')
    report=dict(status='applying',backup=store.backup.relative_to(ROOT).as_posix(),records=4,removed_from_initial_inputs=archives,record_count_change=0,readiness_promotions=0)
    store.finish(report)
    for c in payloads:
        dest=store.path(c['destination']);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as out,(ROOT/c['source']).open('rb') as inp:shutil.copyfileobj(inp,out)
        store.changes.append(dict(path=c['destination'],before_sha256=None,after_sha256=c['sha256']))
    for p in archives:store.archive(p)
    for u in plan['updates']:
        s=next(s for s in scores['records'] if s['problem_id']==u['after']['problem_id']);s.clear();s.update(scorecard(u['after'],ROOT))
    writes.update({PATH:rows,'data/rubrics/task_scorecards/eoes.json':scores})
    for l in cards:writes.update({f'data/{l}/task_cards.json':cards[l],f'data/{l}/input_asset_manifest.json':manifests[l]})
    for p,v in writes.items():store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    for p,h in protected.items():require(sha(ROOT/p)==h,'Protected file changed')
    for p,v in writes.items():require(((ROOT/p).read_text(encoding='utf-8') if isinstance(v,str) else read(ROOT/p))==v,'Readback differs')
    report.update(status='completed',protected_files_unchanged=len(protected),verification=verify(),summary=plan['summary'])
    store.save(REPORT,report);store.finish(report);print(json.dumps(report,indent=2))


def current_after(u):
    """Accept only the explicitly verified later worksheet-only transition."""
    later=ROOT/'data/benchmarks/eoes_2015_worksheets_repair_20260913.json'
    if later.exists():
        plan=read(ROOT/'data/.cache/eoes_2015_worksheets_20260913/plan.json')
        for v in plan['updates']:
            if v['before']['problem_id']==u['after']['problem_id']:
                require(v['before']==u['after'],'Broken batch 49 -> 50 transition')
                for k in ('total_points','source_file','gold_label','solution_file'):
                    require(v['before'].get(k)==v['after'].get(k),'Earlier scope overwritten')
                for k in ('staged_source_release','official_problem_maxima','rubric_path','status'):
                    require(v['before']['evaluation'].get(k)==v['after']['evaluation'].get(k),'Earlier grading/release overwritten')
                return v['after']
    return u['after']


def verify():
    plan=read(ROOT/CACHE/'plan.json');rows=read(ROOT/PATH)
    for p,h in plan['protected'].items():require(sha(ROOT/p)==h,'Original changed')
    verify_pdf(ROOT/PUBLIC)
    for u in plan['updates']:
        a,b=u['before'],current_after(u);pid=b['problem_id'];require(next(r for r in rows if r['problem_id']==pid)==b,'Canonical drift')
        for k in ['gold_label','split','license','team_size','title','year','solution_file']:require(a.get(k)==b.get(k),'Protected metadata changed')
        require(a['evaluation']['status']==b['evaluation']['status']=='not_ready','Readiness changed')
        for layout in ('base','last_exam'):
            c=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']=='eoes/'+pid);folder=ROOT/'data'/layout/c['source_repo_path']/'base/input'
            public=[a for a in b['assets'] if a['role']=='agent_visible'];names={Path(a['path']).name for a in public}|{'problem.md','task_sop.md','input_environment_spec.md','ground_rules.md','collaboration.md'}
            require({p.name for p in folder.iterdir()}==names,'Unlisted or missing input')
            require((folder/'problem.md').read_text(encoding='utf-8')==b['problem_description']+'\n','Prompt drift')
            for asset in b['assets']:
                require(sha(ROOT/asset['path'])==asset['sha256'],'Asset drift')
                if asset['role']=='agent_visible':require(sha(folder/Path(asset['path']).name)==asset['sha256'],'Public copy drift')
            require(not (folder/'additionalfileschallenge1.pdf').exists(),'Mixed-stage appendix exposed')
    require([r for r in rows if r['problem_id'] not in SELECTED]==[r for r in plan['before_rows'] if r['problem_id'] not in SELECTED],'Unrelated rows changed')
    return dict(records=4,initial_source_pages=[3,4],deferred_source_pages=[1,2],original_sources_unchanged=True,
                exact_render_and_geometry_match=True,scoring_totals={p:sum(v) for p,v in MAXIMA.items()},runtime_and_experiments_not_implemented=True)


if __name__=='__main__':{'prepare':prepare,'apply':apply,'verify':lambda:print(verify())}[sys.argv[1]]()
