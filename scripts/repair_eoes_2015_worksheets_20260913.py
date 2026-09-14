"""Restore reviewed participant worksheets, not experimental answer keys.

All 54 worksheet pages, the graph-paper page, and task-sheet 2 page 13
were rendered and visually reviewed. Original PDF bytes are never rewritten.
"""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import sys
import pymupdf
from scripts.repair_iol_sources_20260913 import ROOT, read, sha, require
from scripts.repair_data_catalog import Store, provenance
from scripts.repair_remaining_prompt_text_20260913 import Editor
sys.path.insert(0, str(ROOT/'src'))
from dataset_catalog import scorecard

CACHE='data/.cache/eoes_2015_worksheets_20260913/'
REPORT='data/benchmarks/eoes_2015_worksheets_repair_20260913.json'
PATH='data/benchmarks/eoes/benchmark.json'
RAW='data/raw/eoes/euso/2015/'
SELECTED={'eoes_ExpBlowingintheWind','eoes_tasksheet1','eoes_tasksheet2'}
FORMULA='Rf-value = (distance start–middle of the spot) / (distance start–end of mobile phase)'


def repair_rf(text):
    e=Editor(text)
    e.rx(r'(?<=each compound under given chromatographic conditions\.\n) +𝑑𝑑[^\n]+𝑝𝑝ℎ𝑎𝑎𝑎𝑎𝑎𝑎(?=\n)', FORMULA)
    return e


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(), 'Frozen plan already exists')
    rows=read(ROOT/PATH); updates=[]; store=Store(ROOT)
    protected={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'data/raw/eoes').rglob('*') if p.is_file()}
    for before in rows:
        pid=before['problem_id']
        if pid not in SELECTED: continue
        row=deepcopy(before); challenge=2 if pid=='eoes_tasksheet2' else 1
        names=[f'answersheet{challenge}.pdf']+(['template_diagrampaper.pdf'] if challenge==1 else [])
        review=dict(kind='participant_worksheet_not_solution',challenge=challenge,
            full_visual_review=True,experimental_results_added=False,grading_key_recovered=False,
            edition_equivalence_certified=False,source_files=[])
        for name in names:
            path=RAW+name
            with pymupdf.open(ROOT/path) as doc:
                pages=len(doc)
                require(pages==(1 if name.startswith('template') else 27),'Unexpected source page count')
                require(not doc.is_encrypted and doc.embfile_count()==0,'Unexpected PDF payload')
                links=[(i+1,l.get('kind'),l.get('uri')) for i,p in enumerate(doc) for l in p.get_links()]
                require(links==([(27,2,'http://www.dict.cc/englisch-deutsch/branchiae.html')] if name=='answersheet1.pdf' else []),'Unexpected PDF links')
                require(not any(list(p.widgets() or []) for p in doc),'Unexpected PDF form fields')
                for xref in range(1,doc.xref_length()):
                    require(not any(s in doc.xref_object(xref) for s in ('/JavaScript','/Launch','/OpenAction','/AA ','/SubmitForm')),'Unexpected PDF action')
            row['assets'].append(dict(path=path,role='agent_visible',mime_type='application/pdf',sha256=sha(ROOT/path)))
            review['source_files'].append(dict(path=path,sha256=sha(ROOT/path),visually_reviewed_pages=list(range(1,pages+1)),original_links_retained_not_followed=links))
        if challenge==1:
            review.update(worksheet_task_a_printed_submarks=[9,12,3,5,20,10,9,2,10,10],
                worksheet_task_a_total=90,task_sheet_task_a_total=before['evaluation']['official_problem_maxima'][0]['max_score'],
                source_observations=[
                    'Pages 4 and 5 contain given oxygen and temperature charts, not completed markings.',
                    'Page 7 contains the participant identification key with empty tick cells; the separately deferred morphology diagram and Function table remain judge-only.',
                    'The printed 15 C statement on worksheet page 2 is a question to classify; the task-sheet scientific-information text says 11 C. Neither is silently corrected.',
                    'The graph-paper template carries original CHALLENGE 1 and TEAM A watermarks; no participant team assignment is inferred.',
                    'Mixed original footer dates, all blank lab-assistant fields, and page 20 resistance values are retained.'])
            note=('Archive worksheet note: `answersheet1.pdf` is the original 27-page participant worksheet, not a solution key. '
                'Its Task A submarks sum to 90; the two archived Challenge 1 task sheets print different Task A maxima (90 and 92). '
                'This same-challenge worksheet is supplied with that version limitation, not as proof of an exact marking-scheme match. '
                '`template_diagrampaper.pdf` is the original blank graph-paper template; its TEAM A watermark does not assign this task to a team. '
                'Preserve the given charts and the blank result fields. The separately deferred Function table and morphology diagram remain unavailable until the stated hand-in condition. '
                'Physical experiments, lab-assistant feedback and executable grading are not supplied.')
        else:
            review['source_observations']=[
                'Worksheet page 3 contains the originally prefilled ice-plant number 9; this is retained as a given value, not promoted to a gold answer.',
                'Worksheet pages 20 and 22 contain given dilution concentrations; measured rotations and derived results remain blank.',
                'True/false statements, empty diagrams, signatures and experimental-result fields are preserved without solving them.']
            edit=repair_rf(row['problem_description']);row['problem_description']=edit.text
            review['text_corrections']=edit.changes
            review['formula_source']=dict(path=before['source_file'],sha256=sha(ROOT/before['source_file']),page=13,transcription=FORMULA)
            note=('Archive worksheet note: `answersheet2.pdf` is the original 27-page participant worksheet, not a solution key. '
                'The prefilled ice-plant number and dilution concentrations are original givens; blank experimental results, diagrams and lab-assistant fields have not been filled. '
                'Physical evidence samples, experiments, lab-assistant feedback and executable grading are not supplied.')
        row['problem_description']=note+'\n\n'+row['problem_description']
        row.setdefault('source_review',{})['eoes_2015_worksheet_review']=review
        row['evaluation']['participant_worksheet_review']=deepcopy(review)
        row['evaluation']['limitations']=[s for s in row['evaluation']['limitations'] if s!='Physical experiments, complete participant worksheets and edition-specific executable grading remain unverified.']
        row['evaluation']['limitations'].append('Reviewed participant worksheets are available; physical experiments, lab-assistant feedback, exact edition equivalence and executable grading remain unverified.')
        provenance(row);updates.append(dict(before=before,after=row))
    require(len(updates)==3,'Unexpected record scope')
    plan=dict(benchmark_path=PATH,expected_benchmark_sha256=sha(ROOT/PATH),before_rows=rows,updates=updates,protected=protected,
        summary='3 EOES 2015 records: original participant worksheets and Challenge 1 graph-paper template restored; one source-verified Rf formula repaired. Printed scores, gold, readiness and original PDF bytes unchanged.')
    store.save(CACHE+'plan.json',plan)
    print(json.dumps(dict(records=3,original_pdfs=3,reviewed_source_pages=56)))


def apply():
    require(not (ROOT/REPORT).exists(),'No blind replay')
    plan=read(ROOT/CACHE/'plan.json');require(sha(ROOT/PATH)==plan['expected_benchmark_sha256'],'Canonical drift')
    store=Store(ROOT); rows=deepcopy(plan['before_rows']); writes={}; copies=[]; protected=deepcopy(plan['protected'])
    cards={l:read(ROOT/f'data/{l}/task_cards.json') for l in ('base','last_exam')}
    manifests={l:read(ROOT/f'data/{l}/input_asset_manifest.json') for l in cards}
    scores=read(ROOT/'data/rubrics/task_scorecards/eoes.json')
    for track in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if track['benchmark_path']!=PATH:protected[track['benchmark_path']]=sha(ROOT/track['benchmark_path'])
    for u in plan['updates']:
        before,row=u['before'],u['after'];pid=row['problem_id'];task='eoes/'+pid
        old={a['path']:a for a in before['assets']};new=[a for a in row['assets'] if a['path'] not in old]
        require(all(a['role']=='agent_visible' for a in new),'Unexpected visibility')
        for layout in cards:
            c=next(c for c in cards[layout]['tasks'] if c['task_id']==task);relative=c['source_repo_path'];folder=f'data/{layout}/{relative}/base/input/'
            for p in (ROOT/folder).iterdir():
                if p.is_file() and p.name!='problem.md':protected[p.relative_to(ROOT).as_posix()]=sha(p)
            require((ROOT/folder/'problem.md').read_text(encoding='utf-8')==before['problem_description']+'\n','Old prompt differs')
            files=c['input_files'] if layout=='base' else c['input']['files']
            for a in new:
                name=Path(a['path']).name;dst=folder+name
                require(not (ROOT/dst).exists(),'Destination occupied')
                copies.append(dict(source=a['path'],destination=dst,sha256=a['sha256']))
                entry=dict(name=name,path=('input/' if layout=='base' else 'base/input/')+name)
                if layout=='base':entry['description']='Agent-visible input'
                files.append(entry)
                manifests[layout]['files'].append(dict(task_id=task,source=a['path'],sha256=a['sha256'],staged=relative+'/base/input/'+name))
            files.sort(key=lambda f:f['path']);writes[folder+'problem.md']=row['problem_description']+'\n'
            if layout=='base':c['evaluation']=deepcopy(row['evaluation'])
            else:
                rp=f'data/last_exam/{relative}/eval/reference.json';ref=read(ROOT/rp);ref['evaluation']=deepcopy(row['evaluation']);writes[rp]=ref
        r=next(r for r in rows if r['problem_id']==pid);r.clear();r.update(row)
        s=next(s for s in scores['records'] if s['problem_id']==pid);s.clear();s.update(scorecard(row,ROOT))
    writes.update({PATH:rows,'data/rubrics/task_scorecards/eoes.json':scores})
    for l in cards:writes.update({f'data/{l}/task_cards.json':cards[l],f'data/{l}/input_asset_manifest.json':manifests[l]})
    expected={p:sha(ROOT/p) for p in writes}
    for p,h in {**expected,**protected}.items():require(sha(ROOT/p)==h,'Preflight drift: '+p)
    report=dict(status='applying',backup=store.backup.relative_to(ROOT).as_posix(),records=3,record_count_change=0,readiness_promotions=0,removed_from_initial_inputs=[],summary=plan['summary'])
    store.finish(report)
    for c in copies:
        require(sha(ROOT/c['source'])==c['sha256'],'Source drift')
        with (ROOT/c['destination']).open('xb') as out,(ROOT/c['source']).open('rb') as inp:shutil.copyfileobj(inp,out)
        store.changes.append(dict(path=c['destination'],before_sha256=None,after_sha256=c['sha256']))
    for p,v in writes.items():store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    for p,h in protected.items():require(sha(ROOT/p)==h,'Protected drift: '+p)
    report.update(status='completed',protected_files_unchanged=len(protected),verification=verify())
    store.save(REPORT,report);store.finish(report);print(json.dumps(report,indent=2))


def verify():
    plan=read(ROOT/CACHE/'plan.json');rows=read(ROOT/PATH)
    for p,h in plan['protected'].items():require(sha(ROOT/p)==h,'Original changed')
    for u in plan['updates']:
        a,b=u['before'],u['after'];pid=b['problem_id'];require(next(r for r in rows if r['problem_id']==pid)==b,'Canonical drift')
        for k in ('gold_label','solution_file','total_points','year','title','split','license','team_size','source_file'):
            require(a.get(k)==b.get(k),'Protected record field changed: '+k)
        for k in ('status','rubric_path','official_max_score','official_problem_maxima','staged_source_release'):
            require(a['evaluation'].get(k)==b['evaluation'].get(k),'Score/readiness/stage changed')
        for asset in b['assets']:require(sha(ROOT/asset['path'])==asset['sha256'],'Asset changed')
        for layout in ('base','last_exam'):
            c=next(c for c in read(ROOT/f'data/{layout}/task_cards.json')['tasks'] if c['task_id']=='eoes/'+pid)
            folder=ROOT/'data'/layout/c['source_repo_path']/'base/input';public=[a for a in b['assets'] if a['role']=='agent_visible']
            require((folder/'problem.md').read_text(encoding='utf-8')==b['problem_description']+'\n','Prompt drift')
            names={Path(a['path']).name for a in public}|{'problem.md','task_sop.md','input_environment_spec.md','ground_rules.md','collaboration.md'}
            require({p.name for p in folder.iterdir()}==names,'Unexpected input file')
            for asset in public:require(sha(folder/Path(asset['path']).name)==asset['sha256'],'Staged source differs')
            ev=c['evaluation'] if layout=='base' else read(ROOT/'data'/layout/c['source_repo_path']/'eval/reference.json')['evaluation']
            require(ev==b['evaluation'],'Derived evaluation differs')
    require([r for r in rows if r['problem_id'] not in SELECTED]==[r for r in plan['before_rows'] if r['problem_id'] not in SELECTED],'Unrelated rows changed')
    return dict(records=3,original_pdfs=3,worksheet_pages_reviewed=54,template_pages_reviewed=1,formula_pages_reviewed=[13],scores_and_gold_unchanged=True)


if __name__=='__main__':{'prepare':prepare,'apply':apply,'verify':lambda:print(verify())}[sys.argv[1]]()
