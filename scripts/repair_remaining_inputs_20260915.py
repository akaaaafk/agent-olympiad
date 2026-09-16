"""Source-bounded task repairs; never extract gold into contestant inputs."""
import json, re, hashlib, shutil
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/remaining_routes_20260915'
OUT.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,value):
    backup=OUT/'before'/p.relative_to(ROOT)
    if p.exists() and not backup.exists():backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,backup)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fyziklani():
    catalog=ROOT/'data/benchmarks/fyziklani/benchmark.json';rows=read(catalog)
    registry=ROOT/'data/problem_pdf_allowlist.json';allowed=read(registry);audits=[]
    for row in rows:
        source=row.get('input_repair', {}).get('source') or next(a for a in row['assets'] if a['role']=='agent_visible' and a['path'].endswith('.pdf'))
        path=ROOT/source['path'];assert digest(path)==source['sha256']
        doc=pymupdf.open(path);texts=[];clips=[]
        for page in doc:
            objects=page.get_xobjects();outer=next(x for x in objects if x[2]==0 and x[1].startswith('fzFrm'))
            full=next(x for x in objects if x[2]==outer[0] and x[1]=='fullpage')
            bbox=list(map(float,doc.xref_get_key(outer[0],'BBox')[1].strip('[]').split()))
            matrix=list(map(float,doc.xref_get_key(outer[0],'Matrix')[1].strip('[]').split()))
            assert matrix[:4]==[1,0,0,1] and abs(matrix[5]+bbox[1])<0.01
            width=full[3][2]-full[3][0];height=page.rect.height
            # Preserve vertical bounds exactly. Only restore the original page width.
            doc.xref_set_key(outer[0],'BBox',f'[0 {bbox[1]} {width} {bbox[3]}]')
            doc.xref_set_key(outer[0],'Matrix',f'[1 0 0 1 0 {-bbox[1]}]')
            page.set_mediabox(pymupdf.Rect(0,0,width,height))
            text=page.get_text();texts.append(text)
            spans=[span for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for span in line['spans']]
            safe_bottom=min(page.rect.height,max(span['bbox'][3] for span in spans)+0.5)
            # Discard graphics below the last statement/credit text: floating solution figures can begin before solution prose.
            page.set_cropbox(pymupdf.Rect(0,0,width,safe_bottom))
            clips.append(dict(page=page.number+1,y_bounds=bbox[1::2],original_width=width,safe_height=safe_bottom))
            assert not re.search(r'(?im)^\s*(?:solutions?\s*[:.]?|answer key|the answer is|we obtain|we get)\b',text),row['problem_id']
        ids=re.findall(r'\bProblem\s+([A-Za-z]+\.\d+|\d+)', '\n'.join(texts))
        expected=[str(p['id']) for p in row['gold_label']['parts']]
        assert len(ids)==len(expected) and set(ids)==set(expected),(row['problem_id'],ids,expected)
        target=ROOT/'data/raw/fyziklani'/str(row['year'])/f"{row['problem_id']}_problem_pages_v2.pdf"
        rendered=pymupdf.open()
        for page in doc:
            pix=page.get_pixmap(dpi=150,annots=False)
            target_page=rendered.new_page(width=page.rect.width,height=page.rect.height)
            target_page.insert_image(target_page.rect,stream=pix.tobytes('png'))
        rendered.save(target,deflate=True);rendered.close()
        row['assets']=[a for a in row['assets'] if a['role']!='agent_visible' or a.get('mime_type')!='application/pdf']
        row['assets'].append(dict(path=target.relative_to(ROOT).as_posix(),mime_type='application/pdf',role='agent_visible',sha256=digest(target)))
        row['source_file']=target.relative_to(ROOT).as_posix()
        row['provenance']['source_file']=row['source_file']
        row['provenance']['files']=[{k:a[k] for k in ('path','role','sha256')} for a in row['assets']]
        row['problem_description']='Official contestant problem text (PDF pages retain diagrams and typesetting):\n\n'+'\n\n'.join(f'[PDF page {i+1}]\n{t}' for i,t in enumerate(texts))
        row['evaluation']['task_pdf_required']=True
        row['input_repair']=dict(source=source,method='preserve verified statement y bounds; restore horizontal width; rasterize visible pages only',question_ids=ids)
        allowed['assets']=[a for a in allowed['assets'] if a.get('problem_id')!=row['problem_id']]
        allowed['assets'].append(dict(problem_id=row['problem_id'],path=row['source_file'],sha256=digest(target),pages=list(range(1,len(doc)+1)),review_status='approved_problem_only',review_evidence='Source-bounded repair: existing contestant-only vertical clips never expanded, trailing below-text graphics removed, original width restored, all expected problem ids matched, solution-heading scan passed, pixels-only output removes hidden original PDF objects. See output/remaining_routes_20260915/fyziklani_audit.json.'))
        audits.append(dict(problem_id=row['problem_id'],source_sha256=source['sha256'],output_sha256=digest(target),questions=len(ids),pages=len(doc),clips=clips,review_method='automated source-boundary checks; visual samples are a separate check'))
        doc.close()
    save(catalog,rows);save(registry,allowed);save(OUT/'fyziklani_audit.json',audits)
if __name__=='__main__':fyziklani()
