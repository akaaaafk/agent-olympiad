"""Package the original 42 image cards for the existing visual PDF reader."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json,hashlib,sys,shutil
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from bs4 import BeautifulSoup
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from remove_eoes_companion_records_20260917 import DirectStore
from src.dataset_catalog import scorecard,update_track_index
from scripts.repair_data_catalog import summary_and_figures
PID='mystery_hunt_01261'
def main():
 s=DirectStore(ROOT);bp='data/benchmarks/mystery_hunt/benchmark.json';rows=deepcopy(s.read(bp));row=next(r for r in rows if r['problem_id']==PID)
 folder=(ROOT/row['source_file']).parent
 soup=BeautifulSoup((folder/'puzzle.html').read_bytes(),'html.parser')
 assert [a['href'] for a in soup.find_all('area')]==[f'{i:02}.jpg' for i in range(1,43)]
 image=soup.find('img',attrs={'usemap':True})['src']
 out=ROOT/f'data/raw/mystery_hunt/visual_packets_20260917/{PID}.pdf';out.parent.mkdir(parents=True,exist_ok=True)
 c=canvas.Canvas(str(out),pagesize=(660,1170),invariant=1)
 c.setTitle('Conquering the World - original puzzle images')
 c.setFont('Helvetica',15);c.drawString(30,1140,'Conquering the World')
 c.setFont('Helvetica',10)
 c.drawString(30,1120,"Minerva advises that if one wishes to conquer continents, one must plot one's course")
 c.drawString(30,1105,'carefully, and get as many armies as possible.')
 c.drawImage(ImageReader(str(folder/image)),30,30,width=600,height=1040,preserveAspectRatio=True,anchor='c');c.showPage()
 for group in range(7):
  c.setPageSize((900,960));c.setFont('Helvetica',12)
  c.drawString(12,944,f'Original cards {group*6+1:02}-{group*6+6:02} (original order)')
  for j in range(6):
   n=group*6+j+1;x=(j%3)*300;y=480-(j//3)*465
   c.drawImage(str(folder/f'{n:02}.jpg'),x,y,width=300,height=450)
   c.setFont('Helvetica',9);c.drawString(x+5,y-10,f'{n:02}')
  c.showPage()
 c.save()
 with pymupdf.open(out) as doc:
  assert len(doc)==8
  for page_no in range(1,8):
   images=doc[page_no].get_images();assert len(images)==6
   embedded=[doc.extract_image(x[0])['image'] for x in images]
   assert sorted(embedded)==sorted((folder/f'{i:02}.jpg').read_bytes() for i in range((page_no-1)*6+1,page_no*6+1))
  assert not doc.embfile_count() and all('SOWETO' not in p.get_text().upper() for p in doc)
  review=ROOT/'tmp/mystery_01261_review';review.mkdir(exist_ok=True)
  for i in range(8):doc[i].get_pixmap(matrix=pymupdf.Matrix(1,1)).save(review/f'page_{i+1}.png')
 asset=dict(path=out.relative_to(ROOT).as_posix(),role='agent_visible',mime_type='application/pdf',sha256=hashlib.sha256(out.read_bytes()).hexdigest())
 row['assets']=[a for a in row['assets'] if a['path']!=asset['path']]+[asset]
 row['provenance']['files']=[{k:a[k] for k in ('path','role','sha256')} for a in row['assets']]
 row['problem_description']="Conquering the World\n\nMinerva advises that if one wishes to conquer continents, one must plot one's course carefully, and get as many armies as possible.\n\nRead the supplied 8-page visual PDF with read_problem_pdf: page 1 preserves the original card arrangement; pages 2-8 show all 42 original cards in the same order, six per page. Images and wording are original. The HTML and individual card images are also preserved. Submit one final puzzle answer. Public background research is allowed under the competition rules; puzzle answer keys and solution pages are forbidden."
 row['evaluation'].update(evaluator_id='gold_answer_v1',status='ready_with_limitations',reason='Original visual cards delivered through reviewed PDF reader; official single-answer key verified.',limitations='Requires a vision-capable solver and public background research. Original isolated puzzle only; no full-hunt progression. PDF packet is a layout adaptation preserving all original images; no solution diagram or additional puzzle hint is supplied.')
 row['source_review']['visual_delivery_20260917']=dict(packet=asset['path'],pages=8,cards=42,original_jpeg_bytes_preserved=True,reference_availability='Publisher generic board/rules inspected in judge-only risk_reference.pdf. Not given as an extra contestant hint.',reference_url='https://www.hasbro.com/common/documents/DAD2886D1C4311DDBD0B0800200C9A66/F56A63AE8FA145D9B82A5FA3919CA3A5.pdf',scope='Online-background-research task; not a closed-book reconstruction.')
 s.save(bp,rows)
 allow=deepcopy(s.read('data/problem_pdf_allowlist.json'));allow['assets']=[a for a in allow['assets'] if a.get('problem_id')!=PID]
 allow['assets'].append(dict(problem_id=PID,path=asset['path'],sha256=asset['sha256'],pages=list(range(1,9)),review_status='approved_problem_only',review_evidence='2026-09-17: original overview plus all 42 original JPEGs, original order; embedded JPEG bytes verified; rendered pages reviewed; no answer or solution content.'))
 s.save('data/problem_pdf_allowlist.json',allow)
 index=deepcopy(s.read('data/benchmarks/index.json'));update_track_index(index,'mystery_hunt',rows);s.save('data/benchmarks/index.json',index)
 for base in ['data','data/mini_data']:
  path=base+'/rules/mystery_hunt/evaluation.json';rule=deepcopy(s.read(path));rule['scoring'].setdefault('record_evaluator_overrides',{})[PID]='gold_answer_v1'
  if base=='data':rule['scoring']['evaluation_status_counts']=dict(Counter(r['evaluation']['status'] for r in rows))
  s.save(path,rule)
 path='data/rubrics/task_scorecards/mystery_hunt.json';cards=deepcopy(s.read(path));cards['records']=[scorecard(r,ROOT) for r in rows];s.save(path,cards)
 path='data/base/task_cards.json';cards=deepcopy(s.read(path));card=next(c for c in cards['tasks'] if c['task_id']=='mystery_hunt/'+PID);card['evaluation']=deepcopy(row['evaluation'])
 relative=f'tasks/mystery_hunt/{PID}/base/input/{out.name}';staged=ROOT/'data/base'/relative;shutil.copyfile(out,staged)
 if not any(x['name']==out.name for x in card['input_files']):card['input_files'].append(dict(name=out.name,path='input/'+out.name,description='Original puzzle overview and 42 cards'))
 s.save(path,cards);s.save_text(f'data/base/tasks/mystery_hunt/{PID}/base/input/problem.md',row['problem_description']+'\n')
 path='data/base/input_asset_manifest.json';manifest=deepcopy(s.read(path));manifest['files']=[x for x in manifest['files'] if x['staged']!=relative];manifest['files'].append(dict(task_id='mystery_hunt/'+PID,source=asset['path'],sha256=asset['sha256'],staged=relative));s.save(path,manifest)
 summary_and_figures(s,index,{t['id']:deepcopy(s.read(t['benchmark_path'])) for t in index['olympiads']})
 print('Prepared 8-page packet and enabled',PID)
if __name__=='__main__':main()
