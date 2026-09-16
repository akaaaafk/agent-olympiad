"""Preflight PDF-to-text artifacts and prioritize MCM/ICM in the shared ten-lane queue."""
import collections
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/tinker_requested_current_20260916'
sys.path.insert(0,str(ROOT/'src'))
from artifacts.assets import load_assets
from otc_artifact_pipeline import prepare_artifact_run
from pypdf import PdfReader, PdfWriter

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,r):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

registry=read(OUT/'registry.json')
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
shutil.copy2(OUT/'registry.json',OUT/f'registry.before_pdftext_{stamp}.json')
tracks=('mcm','icm','arml_national_power','arml_power','pumac_power','iol_team','ioaa_group','ijso_practical')
model=registry['model']
existing_mcm=ROOT/'results/tinker_mcm_pdftext_20260916'
prior={}
if (existing_mcm/'registry.json').exists():
 prior={(j['problem_id'],j['variant']):j for j in read(existing_mcm/'registry.json')['jobs']}
jobs=[];blocked=[];bundles=[]
for priority,c in enumerate(tracks):
 path=ROOT/'data/benchmarks'/c/'benchmark.json'
 rows=read(path);changed=False
 for row in rows:
  problem=row['problem_id']
  if row['evaluation']['status'] not in {'ready','ready_with_limitations'}:
   blocked.append(dict(competition=c,problem_id=problem,reason='Current record is not evaluation-ready'))
   continue
  try:
   pdfs=[a for a in load_assets(row,ROOT) if a.role=='agent_visible' and a.mime_type=='application/pdf']
   if not pdfs:raise ValueError('No approved contestant PDF')
   if len(pdfs)>1:
    # Only declared contestant PDFs, with their declared page ranges, in asset order.
    destination=ROOT/'data/raw/pdftext_task_bundles_20260916'/(problem+'.pdf')
    destination.parent.mkdir(parents=True,exist_ok=True)
    writer=PdfWriter();parts=[]
    for a in pdfs:
     reader=PdfReader(a.path);start=a.page_start or 1;end=a.page_end or len(reader.pages)
     for i in range(start-1,end):writer.add_page(reader.pages[i])
     parts.append(dict(path=a.path.relative_to(ROOT).as_posix(),sha256=a.sha256,pages=[start,end]))
    with destination.open('wb') as f:writer.write(f)
    digest=hashlib.sha256(destination.read_bytes()).hexdigest()
    bundle=dict(path=destination.relative_to(ROOT).as_posix(),mime_type='application/pdf',role='agent_visible',sha256=digest)
    row.setdefault('assets',[]).append(bundle)
    row.setdefault('provenance',{})['pdftext_bundle']=dict(path=bundle['path'],sha256=digest,original_contestant_pdfs=parts)
    changed=True
    # Register the bundle before artifact PDF hash -> benchmark lookup.
    write(path,rows)
    pdf=destination;start=1;end=len(PdfReader(pdf).pages)
    bundles.append(dict(competition=c,problem_id=problem,**row['provenance']['pdftext_bundle']))
   else:
    asset=pdfs[0];pdf=asset.path;start=asset.page_start or 1;end=asset.page_end or len(PdfReader(pdf).pages)
   for variant in ('single_agent','otc'):
    previous=prior.get((problem,variant)) if c=='mcm' else None
    jid=f'{problem.lower()}_{variant}_qwen_pdftext'
    output=(existing_mcm/'runs'/previous['id']) if previous else OUT/'runs'/jid
    options=dict(competition=c,task_pdf=str(pdf),task_pages=f'{start}-{end}',output=str(output),
     provider='tinker',model=model,judge_provider='tinker',judge_model=model,
     max_output_tokens=8192,max_tokens=220000,system_variant=variant)
    try:
     # Preserve completed paid MCM runs without re-execution.
     if previous and (output/'result.json').exists() and read(output/'result.json').get('status') in {'complete','unsubmitted'}:
      identity=previous['run_identity']
     else:
      prepared=prepare_artifact_run(**options)
      if (prepared['benchmark'] or {}).get('problem_id')!=problem:raise ValueError('Task PDF does not map to its expected benchmark')
      identity=prepared['identity']
      if previous and identity!=previous['run_identity']:raise ValueError('Existing paid MCM identity differs; checkpoint preserved, not rerun')
     jobs.append(dict(id=jid,competition=c,problem_ids=[problem],problem_id=problem,variant=variant,
      kind='artifact',snapshot=str(ROOT),output=str(output),artifact_options=options,
      run_identity=identity,priority=priority,task_pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
      task_pages=[start,end],input_mode='pdf_extracted_text_artifact'))
    except Exception as exc:blocked.append(dict(competition=c,problem_id=problem,variant=variant,reason=f'{type(exc).__name__}: {exc}'))
  except Exception as exc:blocked.append(dict(competition=c,problem_id=problem,reason=f'{type(exc).__name__}: {exc}'))
 print(c,'artifact_jobs',sum(j['competition']==c for j in jobs),flush=True)
 if changed:write(path,rows)

# Original referenced jobs stay registered for provenance; QANTA is deferred.
registry['jobs']=[j for j in registry['jobs'] if j['kind']!='artifact']+jobs
registry['skip_competitions']=['qanta']
registry['phase_order']=['work','evaluation']
registry['policy']='MCM/ICM first, then remaining requested PDF-text/native tracks. QANTA deferred. Only single_agent/otc solving; paid outputs retained.'
registry['pdftext_blocked']=blocked
registry['pdftext_bundles']=bundles
# Supersede the previous provider-capability blockers, retain historical cohort exclusions.
registry['blocked']=[x for x in registry['blocked'] if not (x.get('competition') in tracks and x.get('reason')=='Tinker does not support required PDF/image artifact input')]+blocked
write(OUT/'registry.json',registry)
write(OUT/'pdftext_preflight.json',dict(timestamp_utc=stamp,by_track=dict(collections.Counter(j['competition'] for j in jobs)),blocked=blocked,bundles=bundles))
print(json.dumps(dict(artifact_jobs=len(jobs),by_track=dict(collections.Counter(j['competition'] for j in jobs)),blocked=len(blocked),bundles=len(bundles),deferred=['qanta']),indent=2),flush=True)
