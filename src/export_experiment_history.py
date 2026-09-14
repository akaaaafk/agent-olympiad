"""Read historical result formats and export provenance-preserving paste tables."""
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'
OUT=RESULTS/'history_export_20260914'
COLS='model competition problem_id score max_score accuracy Communication Planning CS turns api_calls tokens sec variant notes'.split()

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(a):return hashlib.sha256(json.dumps(a,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
def pick(*args):return next((a for a in args if a is not None),None)

def write_table(path,rows):
    lines=['\t'.join(COLS)]
    for r in rows:
        vals=[]
        for c in COLS:
            v=r.get(c)
            text='N/A' if v is None else format(v,'.10g') if isinstance(v,float) else str(v)
            vals.append(text.replace('\t',' ').replace('\r',' ').replace('\n',' '))
        lines.append('\t'.join(vals))
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')

def main():
    OUT.mkdir(exist_ok=True)
    catalog={}
    for t in read(ROOT/'data/benchmarks/index.json')['olympiads']:
        catalog[t['id']]=[r['problem_id'] for r in read(ROOT/t['benchmark_path'])]
    all_rows=[]; exclusions=[]; seen={}; duplicates=[]
    def add(r,identity,source,mode,model):
        if model and ('mock' in str(model).lower() or 'catalog-smoke' in str(model).lower()) or mode in {'mock','smoke','offline'}:
            exclusions.append({'source':source,'reason':'explicit_mock_or_offline'});return
        if identity in seen:
            duplicates.append({'source':source,'same_as':seen[identity]});return
        seen[identity]=source
        classification='live' if mode=='live' or (model and str(model)!='unknown') else 'unverified'
        r['_classification']=classification;r['_source']=source
        score=r.get('score');maximum=r.get('max_score')
        r['accuracy']=score/maximum if isinstance(score,(int,float)) and isinstance(maximum,(int,float)) and maximum>0 else None
        r['notes']+='; verification='+classification+'; source='+source
        all_rows.append(r)
    sessions=list(RESULTS.rglob('contest_session.json'))
    for number,path in enumerate(sessions):
        if number%250==0:print('sessions',number,'/',len(sessions),flush=True)
        source=str(path.relative_to(ROOT)).replace('\\','/')
        try:
            a=read(path); run=a.get('run') or {};settings=(a.get('run_identity') or {}).get('settings') or {};ex=settings.get('execution') or {}
            mode=pick(ex.get('mode'),run.get('mode'));model=pick(ex.get('model'),run.get('model'))
            if model and 'mock' in model.lower() or mode in {'mock','smoke','offline'}:
                exclusions.append({'source':source,'reason':'explicit_mock_or_offline'});continue
            b=a.get('budget',{});g=a.get('grade') or {};m=a.get('metrics') or {};c=a.get('coordination') or {}
            cid=a.get('competition_id');tasks=a.get('manifest',{}).get('tasks',[])
            ids=list(dict.fromkeys(t.get('parent_problem_id') or t.get('task_id') for t in tasks))
            if ids==['deliverable'] or not ids:
                matched=[pid for pid in catalog.get(cid,[]) if pid in str(path)]
                if matched:ids=[max(matched,key=len)]
            pid=';'.join(str(x) for x in ids) or a.get('session_id')
            note='batch='+path.relative_to(RESULTS).parts[0]+'; protocol='+str(a.get('protocol_version','unknown'))+'; unit=session'
            if len(ids)>1:note+='; session_tasks='+str(len(ids))+'; budget_not_per_problem'
            f=path.parent/'result.json'
            if f.exists():
                result=read(f);e=result.get('evaluation') or {}
                if e and result.get('graded'):
                    g={'score':e.get('total_score'),'max_score':e.get('max_score'),'graded':True,'method':e.get('evaluator_id')}
                    note+='; artifact_rubric; proxy_not_official_score'
            raw_hash=None
            for filename in ['coordination_posthoc.json','task_rubric_posthoc.json']:
                f=path.parent/filename
                if not f.exists():continue
                side=read(f)
                raw_hash=raw_hash or hashlib.sha256(path.read_bytes()).hexdigest()
                if side.get('source_sha256')!=raw_hash:continue
                if filename.startswith('coordination') and side.get('status')=='complete':c=side['coordination']
                elif filename.startswith('task') and side.get('status')=='complete':g={'score':side['score'],'max_score':side['max_score'],'graded':True,'method':'rubric_llm_v1_posthoc'}
                elif side.get('status')=='excluded':note+='; EXCLUDED='+side.get('reason','')
            note+='; grade_method='+str(g.get('method'))+'; graded='+str(g.get('graded',False))
            if not g.get('graded'):
                reasons=list(dict.fromkeys(t.get('reason','') for t in g.get('tasks',{}).values() if t.get('reason')))
                if reasons:note+='; grade_issue='+str(reasons)[:600]
            r=dict(model=model,competition=cid,problem_id=pid,score=g.get('score'),max_score=g.get('max_score'),
                Communication=pick(c.get('communication_score'),m.get('communication_score')),
                Planning=pick(c.get('planning_score'),m.get('planning_score')),CS=pick(c.get('coordination_score'),m.get('coordination_score')),
                turns=b.get('turns_used'),api_calls=b.get('api_calls_used'),tokens=b.get('tokens_used'),
                sec=pick(b.get('wall_seconds_used'),m.get('elapsed_seconds'),run.get('elapsed_seconds')),
                variant=a.get('system_variant'),notes=note)
            add(r,'session:'+digest(a),source,mode,model)
        except Exception as e:exclusions.append({'source':source,'reason':'parse_error:'+type(e).__name__})
    # Old per-task/matrix exports: use detailed records, never totals or mean summaries.
    paths=[]
    for name in ['competition_batch.json','phase_b_matrix.json','phase_a.json','phase_a_rescored.json']:
        paths.extend(RESULTS.rglob(name))
    paths.extend(p for p in RESULTS.glob('*.json') if p.is_file())
    for path in paths:
        try:
            a=read(path)
            if not isinstance(a,dict):continue
            records=a.get('results')
            if records is None:
                if not (a.get('problem_id') and a.get('schema')):continue
                records=[a]
            if not isinstance(records,list):continue
            for i,item in enumerate(records):
                if not isinstance(item,dict) or not item.get('problem_id'):continue
                source=str(path.relative_to(ROOT)).replace('\\','/')+'#row='+str(i+1)
                model=pick(item.get('model'),item.get('agent_model'))
                if not model and item.get('agent_models'):model=' + '.join(sorted(set(item['agent_models'].values())))
                model=pick(model,a.get('model'),item.get('model_label'))
                g=item.get('grade') or {};c=item.get('coordination') or {}
                score=pick(item.get('grade_score'),g.get('score'));maximum=pick(item.get('grade_max_score'),g.get('max_score'))
                note='batch='+path.relative_to(RESULTS).parts[0]+'; unit=task; status='+str(item.get('status','legacy'))+'; schema_preserved'
                note+='; grade_method='+str(pick(item.get('grade_method'),g.get('method')))
                if item.get('judge_feedback'):note+='; separate_free_text_judge_feedback_exists; score_is_structured_grade'
                if item.get('error'):note+='; error='+str(item['error'])[:300]
                r=dict(model=model,competition=pick(item.get('competition'),item.get('competition_id')),problem_id=item['problem_id'],score=score,max_score=maximum,
                    Communication=pick(item.get('communication_score'),c.get('communication_score')),
                    Planning=pick(item.get('planning_score'),c.get('planning_score')),CS=pick(item.get('coordination_score'),c.get('coordination_score')),
                    turns=item.get('turns_used'),api_calls=item.get('api_calls'),tokens=item.get('tokens_used'),
                    sec=pick(item.get('elapsed_seconds'),item.get('wall_seconds')),variant=item.get('schema'),notes=note)
                add(r,'legacy:'+digest(item),source,a.get('mode'),model)
        except Exception as e:exclusions.append({'source':str(path),'reason':'parse_error:'+type(e).__name__})
    all_rows.sort(key=lambda r:(str(r['competition']),r['_source']))
    live=[r for r in all_rows if r['_classification']=='live']; unknown=[r for r in all_rows if r['_classification']=='unverified']
    write_table(OUT/'all_live_results_copy.txt',live)
    write_table(OUT/'unverified_results_copy.txt',unknown)
    (OUT/'all_records.json').write_text(json.dumps(all_rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'audit.json').write_text(json.dumps({'excluded':exclusions,'exact_duplicates':duplicates},ensure_ascii=False,indent=2),encoding='utf-8')
    groups=collections.defaultdict(list)
    for r in live:groups[r['competition']].append(r)
    (OUT/'by_competition').mkdir(exist_ok=True)
    lines=['# Historical experiment export','',
        'Scope: this checkout results directory. Original protocol/schema labels and scores preserved. No new API calls.',
        'One row per saved session or legacy task record; multi-problem session budgets are not duplicated per problem.',
        'Exact duplicate JSON records removed. Different rescorings/retries remain separate and must not be treated as independent replications without checking source paths.',
        'N/A = unavailable. accuracy = score/max_score. CS is only read from recorded coordination scores. Live classification uses explicit run mode or a concrete non-mock solver model; unverified records are exported separately.',
        'Legacy free-text judge feedback is not substituted for structured scores. These historical protocols, rubrics and models are not a single matched comparison.', '',
        f'Live records: {len(live)}; competitions: {len(groups)}; unverified: {len(unknown)}; excluded files/rows: {len(exclusions)}; exact duplicate records: {len(duplicates)}.', '',
        '| competition | records | task score available | CS available |', '| --- | ---: | ---: | ---: |']
    for cid,rows in sorted(groups.items()):
        write_table(OUT/'by_competition'/f'{cid}_copy.txt',rows)
        lines.append(f'| {cid} | {len(rows)} | {sum(r["score"] is not None for r in rows)} | {sum(r["CS"] is not None for r in rows)} |')
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines[-len(groups)-4:]),flush=True)

if __name__=='__main__':main()
