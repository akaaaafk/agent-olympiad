"""Deliver Box Sets without changing its original image or revealing its solution."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import hashlib, json, sys, shutil
import requests
import pymupdf
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from remove_eoes_companion_records_20260917 import DirectStore
from src.dataset_catalog import scorecard, update_track_index
from scripts.repair_data_catalog import summary_and_figures
PID = 'mystery_hunt_01271'

def main():
    s = DirectStore(ROOT)
    bp = 'data/benchmarks/mystery_hunt/benchmark.json'
    rows = deepcopy(s.read(bp)); row = next(r for r in rows if r['problem_id'] == PID)
    folder = (ROOT/row['source_file']).parent
    soup = BeautifulSoup((folder/'puzzle.html').read_bytes(), 'html.parser')
    flavor = [p.get_text(' ', strip=True) for p in soup.select('.flavortext p')]
    assert len(flavor) == 2 and soup.select_one('#page-content img')['src'] == 'box_sets.jpg'
    solution_url = row['source_url']+'solution.html'
    response = requests.get(solution_url, timeout=30); response.raise_for_status()
    solution_text = BeautifulSoup(response.content, 'html.parser').get_text(' ', strip=True)
    assert 'ANSWER: SMACK' in solution_text and 'REST ARE THREES A THRU E' in solution_text
    assert row['gold_label']['expected_answer'] == 'SMACK'
    solution = ROOT/f'data/judge_references/mystery_hunt/{PID}/solution.html'
    solution.parent.mkdir(parents=True, exist_ok=True); solution.write_bytes(response.content)
    out = ROOT/f'data/raw/mystery_hunt/visual_packets_20260917/{PID}.pdf'
    out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=(713, 760), invariant=1)
    c.setTitle('Box Sets - original puzzle')
    c.setFont('Helvetica-Bold', 18); c.drawString(30, 728, 'Box Sets')
    c.setFont('Helvetica', 11); c.drawString(30, 700, flavor[0])
    c.drawString(30, 677, 'The intricate and sometimes imperfect designs found on Aztec tile work were always a big hit,')
    c.drawString(30, 661, 'though the tiles themselves were typically laid out in rather mundane patterns.')
    assert flavor[1] == 'The intricate and sometimes imperfect designs found on Aztec tile work were always a big hit, though the tiles themselves were typically laid out in rather mundane patterns.'
    c.drawImage(str(folder/'box_sets.jpg'), 30, 30, width=653, height=610)
    c.showPage(); c.save()
    review = ROOT/'tmp/mystery_01271_review'; review.mkdir(exist_ok=True)
    with pymupdf.open(out) as doc:
        assert len(doc) == 1 and not doc.embfile_count()
        assert doc.extract_image(doc[0].get_images()[0][0])['image'] == (folder/'box_sets.jpg').read_bytes()
        assert 'SMACK' not in doc[0].get_text().upper()
        doc[0].get_pixmap().save(review/'page_1.png')
    asset = dict(path=out.relative_to(ROOT).as_posix(), role='agent_visible', mime_type='application/pdf', sha256=s.sha(out))
    hidden = dict(path=solution.relative_to(ROOT).as_posix(), role='judge_only', mime_type='text/html', sha256=s.sha(solution))
    row['assets'] = [a for a in row['assets'] if a['path'] not in (asset['path'],hidden['path'])]+[asset,hidden]
    row['solution_file'] = hidden['path']; row['provenance']['solution_file'] = hidden['path']
    row['provenance']['files'] = [{k:a[k] for k in ('path','role','sha256')} for a in row['assets']]
    row['problem_description'] = '# Box Sets\n\n'+'\n\n'.join(flavor)+'\n\nRead the supplied one-page visual PDF with read_problem_pdf. It preserves the original complete picture grid and wording. Submit one final puzzle answer. Public background research is allowed under the competition rules; puzzle answer keys and solutions are forbidden.'
    row['evaluation'].update(evaluator_id='gold_answer_v1', status='ready_with_limitations', reason='Complete original visual puzzle and official answer verified; reviewed PDF reader enabled.', limitations='Requires a vision-capable solver; public background research is allowed. Isolated puzzle only, not full-hunt progression. Offline delivery and grading checks do not establish model solving accuracy.')
    row['source_review']['visual_delivery_20260917'] = dict(packet=asset['path'], pages=1, original_jpeg_bytes_preserved=True, solution_url=solution_url, solution_visibility='judge_only', scope='Complete standalone visual puzzle; no physical interaction or feeder answers required.')
    s.save(bp, rows)
    p='data/problem_pdf_allowlist.json'; allow=deepcopy(s.read(p))
    allow['assets']=[a for a in allow['assets'] if a.get('problem_id') != PID]
    allow['assets'].append(dict(problem_id=PID,path=asset['path'],sha256=asset['sha256'],pages=[1],review_status='approved_problem_only',review_evidence='Original full picture grid and verbatim flavor text only; embedded JPEG bytes match source; rendered page reviewed.'))
    s.save(p, allow)
    index=deepcopy(s.read('data/benchmarks/index.json')); update_track_index(index,'mystery_hunt',rows); s.save('data/benchmarks/index.json',index)
    for base in ['data','data/mini_data']:
        p=base+'/rules/mystery_hunt/evaluation.json'; rule=deepcopy(s.read(p))
        rule['scoring'].setdefault('record_evaluator_overrides',{})[PID]='gold_answer_v1'
        if base=='data': rule['scoring']['evaluation_status_counts']=dict(Counter(r['evaluation']['status'] for r in rows))
        s.save(p,rule)
    p='data/rubrics/task_scorecards/mystery_hunt.json'; cards=deepcopy(s.read(p)); cards['records']=[scorecard(r,ROOT) for r in rows]; s.save(p,cards)
    p='data/base/task_cards.json'; cards=deepcopy(s.read(p)); card=next(c for c in cards['tasks'] if c['task_id']=='mystery_hunt/'+PID); card['evaluation']=deepcopy(row['evaluation'])
    relative=f'tasks/mystery_hunt/{PID}/base/input/{out.name}'; shutil.copyfile(out,ROOT/'data/base'/relative)
    if not any(x['name']==out.name for x in card['input_files']): card['input_files'].append(dict(name=out.name,path='input/'+out.name,description='Original complete picture grid and flavor text'))
    s.save(p,cards); s.save_text(f'data/base/tasks/mystery_hunt/{PID}/base/input/problem.md',row['problem_description']+'\n')
    p='data/base/input_asset_manifest.json'; manifest=deepcopy(s.read(p)); manifest['files']=[x for x in manifest['files'] if x['staged'] != relative]; manifest['files'].append(dict(task_id='mystery_hunt/'+PID,source=asset['path'],sha256=asset['sha256'],staged=relative)); s.save(p,manifest)
    p='data/mini_data/dependency_manifest.json'; dep=deepcopy(s.read(p)); rel='rules/mystery_hunt/evaluation.json'
    if rel in dep['files']:
        dep['files'][rel].update(source_sha256=s.sha('data/'+rel),mini_sha256=s.sha('data/mini_data/'+rel))
    s.save(p,dep)
    summary_and_figures(s,index,{t['id']:deepcopy(s.read(t['benchmark_path'])) for t in index['olympiads']})
    print('Prepared Box Sets; current Mystery Hunt records:',len(rows))

if __name__ == '__main__': main()
