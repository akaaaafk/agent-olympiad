"""Render curated, hash-verified IYPT HTML and its declared images offline."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import pymupdf
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def main():
    path=ROOT/'data/benchmarks/iypt/benchmark.json'
    rows=json.loads(path.read_text(encoding='utf-8'))
    output=ROOT/'output/remaining_routes_20260915'
    backup=output/'before/data/benchmarks/iypt/benchmark.json'
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copy2(path,backup)
    audit=[]
    for row in rows:
        assets=[a for a in row['assets'] if a['role']=='agent_visible']
        if any(a['mime_type']=='application/pdf' for a in assets):continue
        declared={}
        for asset in assets:
            source=(ROOT/asset['path']).resolve()
            assert source.is_relative_to(ROOT) and hashlib.sha256(source.read_bytes()).hexdigest()==asset['sha256']
            declared[source]=asset
        html_asset=next(a for a in assets if a['mime_type']=='text/html')
        html_path=ROOT/html_asset['path']
        soup=BeautifulSoup(html_path.read_text(encoding='utf-8'),'html.parser')
        for tag in soup(['script','style','iframe','object','embed','link','base']):tag.decompose()
        for tag in soup.find_all('a'):tag.unwrap()
        images=[]
        with tempfile.TemporaryDirectory(prefix='iypt-packet-') as directory:
            for i,tag in enumerate(soup.find_all('img')):
                source=(html_path.parent/str(tag.get('src',''))).resolve()
                assert source in declared and declared[source]['mime_type'].startswith('image/'),str(source)
                name=f'image_{i}.png'
                with Image.open(source) as image:image.convert('RGB').save(Path(directory)/name)
                tag.attrs={'src':name,'style':'max-width:100%; max-height:400px;'}
                images.append(declared[source]['path'])
            for tag in soup.find_all(True):
                if tag.name!='img':tag.attrs={}
            target=html_path.with_suffix('.packet.pdf')
            story=pymupdf.Story(html=str(soup),user_css='body {font-family:serif;font-size:11pt;} p {margin-bottom:10pt;} h1 {font-size:17pt;}',archive=pymupdf.Archive(directory))
            writer=pymupdf.DocumentWriter(str(target))
            media=pymupdf.paper_rect('a4'); area=media+(36,36,-36,-36)
            story.write(writer,lambda *args:(media,area,None))
            writer.close()
        with pymupdf.open(target) as pdf:
            assert len(pdf)>0
            page_count=len(pdf)
        asset=dict(path=target.relative_to(ROOT).as_posix(),mime_type='application/pdf',role='agent_visible',sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        row['assets'].append(asset)
        row['input_pdf_derivation']=dict(source=html_asset['path'],source_sha256=html_asset['sha256'],images=images,method='offline HTML layout with only declared local image assets; no network, scripts or external references')
        audit.append(dict(problem_id=row['problem_id'],pages=page_count,images=len(images),output=asset))
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'iypt_pdf_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print('IYPT HTML packets converted:',len(audit))


if __name__=='__main__':main()
