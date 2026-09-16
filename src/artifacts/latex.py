"""Compile contestant LaTeX in a networkless container without host mounts."""
import base64
import json
from pathlib import Path
import subprocess
import uuid

IMAGE = 'agent-olympiad-latex:v1'


def renderer_identity():
    result = subprocess.run(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'],
                            capture_output=True, text=True, timeout=15)
    if result.returncode or not result.stdout.strip().startswith('sha256:'):
        raise ValueError('LaTeX renderer unavailable. Build: docker build -t agent-olympiad-latex:v1 docker/latex')
    return result.stdout.strip()


SUPERVISOR = r'''
import base64, json, os, pathlib, resource, subprocess, sys
os.chdir('/work')
resource.setrlimit(resource.RLIMIT_FSIZE, (24*1024*1024, 24*1024*1024))
source=sys.stdin.read()
pathlib.Path('submission.tex').write_text(source, encoding='utf-8')
ok=True
with open('compiler.log','wb') as log:
    for _ in range(2):
        try:
            result=subprocess.run(['pdflatex','-no-shell-escape','-halt-on-error',
                '-interaction=nonstopmode','submission.tex'],stdout=log,stderr=log,timeout=35)
            if result.returncode: ok=False; break
        except subprocess.TimeoutExpired: ok=False; break
pdf=pathlib.Path('submission.pdf')
payload={'ok':ok and pdf.is_file(),'log':pathlib.Path('compiler.log').read_text(errors='replace')[-12000:]}
if payload['ok']: payload['pdf']=base64.b64encode(pdf.read_bytes()).decode()
print(json.dumps(payload))
'''


def compile_latex(source: str, pdf: Path, *, image_id=None):
    identity = image_id or renderer_identity()
    name = 'olympiad-latex-' + uuid.uuid4().hex
    command = ['docker','run','--rm','--pull=never','--name',name,'--network=none',
               '--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',
               '--memory=512m','--cpus=1','--pids-limit=64','--user=65534:65534',
               '--tmpfs','/work:rw,noexec,nosuid,size=128m,mode=1777',
               '--tmpfs','/tmp:rw,noexec,nosuid,size=32m,mode=1777',
               '-i',identity,'python','-I','-c',SUPERVISOR]
    try:
        result = subprocess.run(command,input=source,capture_output=True,text=True,
                                encoding='utf-8',timeout=90)
        if result.returncode:
            raise ValueError('Isolated LaTeX renderer failed: '+result.stderr[-2000:])
        payload=json.loads(result.stdout)
        pdf.with_suffix('.compile.log').write_text(payload['log'],encoding='utf-8')
        if not payload['ok']:
            raise ValueError('LaTeX compilation failed: '+payload['log'][-3500:])
        content=base64.b64decode(payload['pdf'],validate=True)
        if not content.startswith(b'%PDF-'):
            raise ValueError('Compiler did not produce a PDF')
        pdf.write_bytes(content)
        return identity
    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
