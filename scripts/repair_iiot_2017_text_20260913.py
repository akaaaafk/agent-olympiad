"""Source-reviewed 2017 samples, scoring fractions and graph/table layout."""
from copy import deepcopy
import json
import sys
from scripts.repair_remaining_prompt_text_20260913 import ROOT,Store,Editor,read,sha,rel,require

CACHE='data/.cache/iiot_2017_text_20260913/'
REPORT='data/benchmarks/iiot_2017_text_repair_20260913.json'
PATH='data/benchmarks/iiot/benchmark.json'
SAMPLES={
 1:[('4 1\n2 20 15\n3 70 0\n0 10 10\n1 50 0','70'),('6 3\n2 40 30\n4 90 70\n0 75 10\n5 20 0\n1 80 80\n3 50 50','225')],
 2:[('2 3\n4 4\n0 1\n2 3\n2 1\n0 3','0 3 .\n1 2 .'),
    ('4 4\n11 10\n1 4\n0 1\n7 2\n8 6\n6 10\n5 7\n4 2\n3 10\n10 9\n6 0','1 0 7 5\n4 . 2 .\n8 6 10 9\n. . 3 .'),
    ('4 4\n11 10\n1 4\n0 1\n7 2\n8 6\n6 10\n5 7\n4 2\n3 10\n10 9\n6 0','1 0 7 5\n4 . 2 .\n6 . 10 .\n. . 3 9')],
 3:[('100\n5 3\n15 80 20 50','18'),('100\n10 5\n34 30 16 9 18 14 27 10 15','5415')],
 4:[('@dd10 v1cin*\n0 v@d1ci*n','6'),("caro vicino vuoi smetterla di fare casino\nIl caro vita sale ancora: se sei mancino vuoi smettere di comprare oggetti appositi, per esempio. Fare cassa e' sempre piu' difficile; parola di fiscalista.",'5')],
 5:[('10\n3\n20 19\n2 2\n17 15','1'),('10\n5\n11 13\n4 15\n12 14\n9 7\n5 8','2')],
 6:[('3 5\n-1 0 0\n0 2 1 2\n3 0\n2 2 4 3\n1 1 0\n6 5 4 2 3 1 5','10c'),('8 4\n-1 0 0 2 2 2 2 1\n2 3 5 6 7\n2 2 5 4\n8 2 6 7\n1 0','1010')],
 7:[('3\ndollars invest enlarge\n4\nscientific paper deadline professor\n3\n6\nhey giorgio send me the paper\n8\nnow is the time to invest in bitcoin\n11\ni wonder why we dont invest more for the scientific advancement','1 1'),
    ('1\nyikes\n1\nyummy\n5\n2\nyummy yummy\n2\nlikes bikes\n2\nyummy bikes\n2\nyummy yikes\n2\nbikes yikes','1 2')]
}
PAGES={1:2,2:3,3:2,4:2,5:2,6:4,7:2}


def repair(number,text):
    e=Editor(text)
    e.rep('III OOO III ((( ))) ;;; +++ TTT','[IOI in Teams logo]',PAGES[number])
    examples='\n\nExamples\n\n'+'\n\n'.join(f'Sample {i} input:\n```text\n{a}\n```\n\nSample {i} output:\n```text\n{b}\n```' for i,(a,b) in enumerate(SAMPLES[number],1))+'\n\n'
    e.rx(r'Examples input.txt output.txt .*?(?=Explanation)',examples)
    if number==1:e.rep('Fi̸= i','Fi ≠ i')
    elif number==2:
        e.rep('M−∆ out M + 10∆ out','(M − Δ_out) / (M + 10 Δ_out)')
        e.rep('10−3 10 + 10·3 = 7 40 = 0.175','(10 − 3) / (10 + 10·3) = 7/40 = 0.175')
        e.text+='\n\nSource note: the printed edge-endpoint constraint indexes i through N−1 although the input describes M edges. The original indexing is retained; no unpublished erratum or checker behavior is assumed.'
    elif number==3:
        e.rep('0 1 2 3 4 15 20 50 ⋆ 80 20 15 50 ⋆ 80 20 50 15 ⋆ 80 15 50 20 ⋆ 80 50 15 20 ⋆ 80 50 20 15 ⋆ 80',
            '\n```text\nposition: 0  1  2  3  4\n         15 20 50  ⋆ 80\n         20 15 50  ⋆ 80\n         20 50 15  ⋆ 80\n         15 50 20  ⋆ 80\n         50 15 20  ⋆ 80\n         50 20 15  ⋆ 80\n```\n')
        e.text+='\n\nSource note: the input lists N−1 capacities but labels them V_0,...,V_{N−1}; the constraint elsewhere ends at N−2. This original endpoint inconsistency is retained, not silently corrected.'
    elif number==4:
        e.rep('∆ max−∆ out ∆ max + 10∆ out','(Δ_max − Δ_out) / (Δ_max + 10 Δ_out)')
        e.text+="\n\nSample transcription note: the long newspaper string is one input line; visual line wrapping in the PDF is not an input newline. Its two printed apostrophe glyphs are represented as ASCII ' under the source's printable-ASCII constraint. The original PDF remains available."
    elif number==5:
        e.rep('Ai̸= H and Bi̸= H','Ai ≠ H and Bi ≠ H')
    elif number==6:
        e.rep('0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 8 In this case',
            '\n[Graph transcription: arrows point from a slave to its master; parent arrays list nodes in ascending ID order, with −1 for the root.]\nBefore: [-1,0,0,2,2,2,2,1]. After adding node 8: [-1,0,0,2,2,8,8,8,2].\nIn this case')
        e.rep('0 1 2 0 1 2 3 0 1 2 3 4 0 1 2 3 4 5',
            '\n[Sample 1 diagram sequence, slave-to-master parent arrays:]\nInitial: [-1,0,0]. Step 1: [-1,3,3,0]. Step 2: [-1,3,3,0,3]. Step 3: [-1,3,3,5,5,2], showing the directed cycle 2→3→5→2.\n')
        e.rep('0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 8 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 10 0 1 2 3 4 5 6 7 8 9 10 11',
            '\n[Sample 2 diagram sequence, slave-to-master parent arrays:]\nInitial: [-1,0,0,2,2,2,2,1].\nStep 1: [-1,0,0,2,2,8,8,8,2].\nStep 2: [-1,0,0,2,9,9,8,8,2,2].\nStep 3: [-1,0,0,2,9,9,10,10,2,2,8].\nStep 4: [-1,0,0,2,9,9,10,10,2,2,8,1].\n')
    return e


def prepare():
    require(not (ROOT/CACHE/'plan.json').exists(),'Already prepared')
    rows=read(ROOT/PATH);before=deepcopy(rows);selected={};changes=[];protected={}
    for row in rows:
        if row['year']!=2017:continue
        pid=row['problem_id'];n=int(pid[-2:]);e=repair(n,row['problem_description']);row['problem_description']=e.text
        if n==5:
            require(row['title']=='Moiving Paintings (paintings)','Unexpected old title');row['title']='Moving Paintings (paintings)'
        selected[pid]=row;protected.update({a['path']:a['sha256'] for a in row['assets']})
        changes.append(dict(task_id='iiot/'+pid,source_file=row['source_file'],source_sha256=sha(ROOT/row['source_file']),reviewed_pages=list(range(1,PAGES[n]+1)),edits=e.changes,samples=len(SAMPLES[n])))
    require(len(selected)==7,'Selection drift');writes={PATH:rows}
    for layout in ('base','last_exam'):
        cp=f'data/{layout}/task_cards.json';cards=read(ROOT/cp)
        for card in cards['tasks']:
            pid=card['task_id'].split('/',1)[1]
            if pid not in selected:continue
            folder=ROOT/f'data/{layout}'/card['source_repo_path'];prompt=rel(folder/'base/input/problem.md');old=next(r for r in before if r['problem_id']==pid)
            require((ROOT/prompt).read_text(encoding='utf-8')==old['problem_description']+'\n','Prompt drift');writes[prompt]=selected[pid]['problem_description']+'\n';card['title']=selected[pid]['title']
            protected.update({rel(p):sha(p) for p in folder.rglob('*') if p.is_file() and rel(p)!=prompt})
        writes[cp]=cards
        for name in ('input_asset_manifest.json','index.json','README.md'):protected[f'data/{layout}/{name}']=sha(ROOT/f'data/{layout}/{name}')
    for tree in ('data/rules','data/rubrics','data/viz'):
        protected.update({rel(p):sha(p) for p in (ROOT/tree).rglob('*') if p.is_file()})
    for track in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        if track['benchmark_path']!=PATH:protected[track['benchmark_path']]=sha(ROOT/track['benchmark_path'])
    protected['data/benchmarks/index.json']=sha(ROOT/'data/benchmarks/index.json')
    Store(ROOT).save(CACHE+'plan.json',dict(writes=writes,before_rows=before,changes=changes,protected=protected,expected={p:sha(ROOT/p) for p in writes}))
    print(json.dumps(dict(records=7,content_files=len(writes),samples=sum(map(len,SAMPLES.values())))))


def verify(plan):
    for p,v in plan['writes'].items():require(((ROOT/p).read_text(encoding='utf-8') if isinstance(v,str) else read(ROOT/p))==v,'Write drift: '+p)
    for p,h in plan['protected'].items():require(sha(ROOT/p)==h,'Protected drift: '+p)
    expected=deepcopy(plan['before_rows'])
    for row in expected:
        if row['year']==2017:
            row['problem_description']=repair(int(row['problem_id'][-2:]),row['problem_description']).text
            if row['problem_id']=='iiot_2017_05':row['title']='Moving Paintings (paintings)'
    require(expected==read(ROOT/PATH),'Unexpected canonical edit')
    return dict(records=7,content_files=17,sample_pairs=15,reviewed_pages=17,protected_files_unchanged=len(plan['protected']),sources_tests_scores_readiness_unchanged=True)


def apply():
    require(not (ROOT/REPORT).exists(),'Already applied');plan=read(ROOT/CACHE/'plan.json')
    for p,h in {**plan['expected'],**plan['protected']}.items():require(sha(ROOT/p)==h,'Concurrent edit: '+p)
    store=Store(ROOT);report=dict(status='applying',backup=rel(store.backup),changes=plan['changes']);store.finish(report)
    for p,v in plan['writes'].items():store.save_text(p,v) if isinstance(v,str) else store.save(p,v)
    report.update(status='completed',validation=verify(plan));store.save(REPORT,report);store.finish(report);print(json.dumps(report['validation']))


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    elif mode=='apply':apply()
    elif mode=='verify':print(json.dumps(verify(read(ROOT/CACHE/'plan.json'))))
    else:raise ValueError(mode)
