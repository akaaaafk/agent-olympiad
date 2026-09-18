"""Local Docker environment delivery for reviewed Cybench/NYU attachments.

Does not execute publisher initialization shell scripts or change dataset readiness.
All command execution occurs inside the dedicated contestant container.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'agent-olympiad-ctf:v1'

def docker(*args, timeout=600):
    command=['docker',*map(str,args)]
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,encoding='utf-8',errors='replace',start_new_session=os.name!='nt',
        env={**os.environ,'COMPOSE_PROGRESS':'plain'})
    try:
        stdout,stderr=process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Docker Compose is a child plugin on Windows. Killing only docker.exe
        # leaves its inherited pipes open and defeats the startup timeout.
        if os.name=='nt':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
        else:
            import signal
            os.killpg(process.pid,signal.SIGKILL)
        stdout,stderr=process.communicate(timeout=10)
        raise subprocess.TimeoutExpired(command,timeout,output=stdout,stderr=stderr)
    if process.returncode:
        raise RuntimeError((stdout+'\n'+stderr)[-6000:])
    return stdout

def inside(path, root=ROOT):
    path = Path(path).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path outside allowed source directory')
    return path

def records():
    sys.path.insert(0, str(ROOT / 'src'))
    from dataset_paths import data_root
    for competition in ('cybench', 'nyu_ctf_bench'):
        for row in json.loads((data_root() / 'benchmarks' / competition / 'benchmark.json').read_text(encoding='utf-8')):
            yield competition, row

def select(problem):
    matches = [(c, r) for c, r in records() if r['problem_id'] == problem]
    if len(matches) != 1:
        raise ValueError('Unknown or ambiguous problem_id')
    return matches[0]

def compose_path(row):
    review = row['source_review']
    root = inside(ROOT / review['upstream_source_directory'])
    declared = review.get('compose_files') or []
    candidates = [ROOT / p for p in declared]
    # Paths checked against publisher start scripts; never search solution trees
    # for a convenient replacement service.
    reviewed_nested = {
        '05-motp':'env/docker-compose.yml',
        '21-elgamal':'env/docker-compose.yml',
        '22-back-to-the-past':'env/docker-compose.yml',
        'network-tools':'challenge/docker-compose.yml',
        'chunky':'dist/docker-compose.yml',
        'Character':'metadata/env/docker-compose.yml',
    }
    for suffix,relative in reviewed_nested.items():
        if not candidates and row['problem_id'].endswith(suffix):
            candidates=[root/relative]
    if not candidates:
        candidates = list(root.glob('docker-compose.y*ml')) + list(root.glob('compose.y*ml'))
    if len(candidates) != 1:
        raise ValueError('Exactly one original Compose file required; initializer-only services need explicit mapping')
    return inside(candidates[0], root), root

def source_compose(row):
    """Explicit Dockerfile-only publisher mappings, preserving original CMD."""
    manual={
        'diffecient':('challenge','diffecient',9999),
        'Stop_Drop_and_Roll':('.','stop_drop_roll',1337),
    }
    for suffix,(context,name,port) in manual.items():
        if row['problem_id'].endswith(suffix):
            root=inside(ROOT/row['source_review']['upstream_source_directory'])
            # Ports verified from Dockerfile EXPOSE/xinetd and publisher build script.
            return root/'publisher-compose.yaml',root,{'services':{name:{'build':context,'expose':[port]}}}
    path,root=compose_path(row)
    return path,root,yaml.safe_load(path.read_text(encoding='utf-8'))

def endpoints(row):
    _,_,source=source_compose(row)
    result=[]
    for name,service in source['services'].items():
        for mapping in service.get('ports',[]) or service.get('expose',[]):
            port=mapping.get('target') if isinstance(mapping,dict) else str(mapping).split(':')[-1].split('/')[0]
            if str(port).isdigit():result.append((name,int(port)))
    review=row['source_review']
    target=review.get('target_host') or ''
    if ':' in target and target.rsplit(':',1)[1].isdigit():
        host,port=target.rsplit(':',1);result.append((host,int(port)))
    elif target and str(review.get('internal_port','')).isdigit():
        result.append((target,int(review['internal_port'])))
    return sorted(set(result))

def normalized_services(row, stage=None):
    path, root, config = source_compose(row)
    services = config.get('services') or {}
    if not services:
        raise ValueError('Compose has no services')
    def reject_host_interpolation(value):
        if isinstance(value,str) and re.search(r'(?<!\$)\$(?:\{|[A-Za-z_])',value):
            raise ValueError('Host environment interpolation requires explicit task mapping')
        if isinstance(value,dict):
            for child in value.values():reject_host_interpolation(child)
        if isinstance(value,list):
            for child in value:reject_host_interpolation(child)
    reject_host_interpolation(services)
    result = {}
    # Explicit allowlist: unknown runtime settings cannot silently weaken isolation.
    allowed = {'image','build','command','entrypoint','environment','env_file','working_dir',
               'user','healthcheck','depends_on','expose','ports','networks','container_name',
               'restart','volumes','hostname','platform','init','labels','mem_limit','cpus','read_only','privileged','deploy','extra_hosts'}
    for name, source in services.items():
        if set(source) - allowed:
            raise ValueError(f'{name}: unsupported Compose fields: {sorted(set(source)-allowed)}')
        if source.get('privileged'):
            raise ValueError(f'{name}: privileged original runtime needs a separate VM')
        if source.get('extra_hosts') and not (row['problem_id'].endswith('web_chunky') and
                source['extra_hosts']==['chunky.chals.sekai.team:host-gateway']):
            raise ValueError('Original host gateway mapping needs explicit task routing')
        if source.get('deploy') and set(source['deploy'])-{'resources'}:
            raise ValueError('Unsupported deploy settings')
        service = {k:v for k,v in source.items() if k not in {'ports','networks','container_name','restart','labels','hostname','mem_limit','cpus','privileged','deploy','extra_hosts'}}
        if row['problem_id'] in {'nyu_ctf_2023f-cry-describeme','nyu_ctf_2021f-cry-interoperable'} and name=='game-server':
            # Reviewed programs never invoke Docker (DescribeMe: stdlib;
            # Interoperable: stdlib + gmpy2). Build source without the unused socket.
            reviewed={
                'Dockerfile':'f69dbf91eb43e2c5629cf5ce1fdcac80617c052434d7de764e9c95a5b890c1ef',
                'chall.py':'cf3536a18e0fb1d9e8ee53af9374a036bce97f1860f12b0eec7e586896199dbb',
            }
            if row['problem_id']=='nyu_ctf_2021f-cry-interoperable':
                reviewed={
                    'Dockerfile':'7db5a99a93754a729e6fcedb7207a4ba1dc76d7b52e19827c6699a48b4976789',
                    'chal.py':'7842caaf10170094d45e5cf3477d1c3e8ac5fb540b47a6cc78f9e37e5030b57c',
                    'interoperable.xinetd':'b989191744931945c2b52f9818a1d38291a507ca37de708e641685e319319247',
                }
            if service.get('volumes')!=['/var/run/docker.sock:/var/run/docker.sock']:
                raise ValueError('Reviewed original socket mapping changed; review required')
            for relative,digest in reviewed.items():
                if hashlib.sha256(inside(root/relative,root).read_bytes()).hexdigest()!=digest:
                    raise ValueError('Reviewed original source changed; review required')
            service.pop('volumes')
            service['build']='.'
        if service.get('volumes'):
            raise ValueError(f'{name}: bind/volume mapping requires explicit review')
        build = service.get('build')
        if build:
            service.pop('image',None)  # Compose project-specific build tags.
            build = {'context':build} if isinstance(build,str) else dict(build)
            if set(build) - {'context','dockerfile','args','target'}:
                raise ValueError(f'{name}: unsupported build settings')
            context = inside(path.parent / build.get('context','.'), root)
            if not context.is_dir():
                raise ValueError(f'{name}: missing original build context')
            inside(context / build.get('dockerfile','Dockerfile'), root)
            original = context / build.get('dockerfile','Dockerfile')
            # Retain historical Python/OS versions; archived Debian repositories
            # replace retired mirrors in a generated Dockerfile only.
            text = original.read_text(encoding='utf-8')
            shell_copy='.sh' in text
            retired_java='FROM openjdk:11-slim' in text
            maven_legacy='FROM maven:3.8.5-openjdk-11-slim' in text
            buster_base='buster' in text or (row['problem_id']=='nyu_ctf_2023f-cry-describeme' and text.startswith('FROM python:3.6.9-slim'))
            if stage is not None and (buster_base or 'xinetd' in text or shell_copy or retired_java or maven_legacy):
                lines = text.splitlines()
                if retired_java:
                    lines=[line.replace('FROM openjdk:11-slim','FROM eclipse-temurin:11-jdk-jammy') for line in lines]
                if maven_legacy:
                    # Use the immutable snapshot date documented in this exact
                    # base image's own sources.list; preserve its Java/Maven versions.
                    lines.insert(1,"RUN printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20220527T000000Z bullseye main\\ndeb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20220527T000000Z bullseye-security main\\n' > /etc/apt/sources.list")
                if row['problem_id']=='nyu_ctf_2021f-cry-interoperable':
                    lines.insert(1,"RUN sed -i 's|archive.ubuntu.com|old-releases.ubuntu.com|g; s|security.ubuntu.com|old-releases.ubuntu.com|g' /etc/apt/sources.list")
                if buster_base:
                    lines=[line.replace('deb.debian.org/debian-security','archive.debian.org/debian-security')
                               .replace('deb.debian.org/debian','archive.debian.org/debian') for line in lines]
                    lines=['    true && \\' if 'echo ' in line and 'buster-updates' in line else line for line in lines]
                    lines.insert(1, "RUN if [ -f /etc/apt/sources.list ]; then sed -i 's|deb.debian.org/debian|archive.debian.org/debian|g; s|security.debian.org/debian-security|archive.debian.org/debian-security|g; /buster-updates/d' /etc/apt/sources.list; fi && printf 'Acquire::Check-Valid-Until \"false\";\\n' > /etc/apt/apt.conf.d/99archive")
                if 'xinetd' in text:
                    lines.append("RUN find /etc/xinetd.d -type f -exec sed -i 's/\\r$//' {} +")
                if shell_copy:
                    users=[line.split(None,1)[1] for line in lines if line.upper().startswith('USER ')]
                    if users:lines.append('USER root')
                    lines.append("RUN find / -xdev -type f -name '*.sh' -exec sed -i 's/\\r$//' {} +")
                    if users:lines.append('USER '+users[-1])
                patched = stage / (name+'-Dockerfile')
                patched.write_text('\n'.join(lines)+'\n',encoding='utf-8')
                build['dockerfile'] = str(patched)
            build['context'] = str(context)
            service['build'] = build
            health=service.get('healthcheck',{}).get('test',[])
            if text.startswith('FROM python:') and isinstance(health,list):
                match=re.search(r'nc -z localhost (\d+)', ' '.join(health))
                if match:
                    port=int(match.group(1))
                    service['healthcheck']={**service['healthcheck'], 'test':['CMD','python','-c',
                        f'import socket; socket.create_connection(("127.0.0.1",{port}),3).close()']}
        if 'env_file' in service:
            entries = service['env_file']
            entries = [entries] if isinstance(entries,str) else entries
            if not all(isinstance(e,str) for e in entries):
                raise ValueError('Structured env_file needs review')
            service['env_file'] = [str(inside(path.parent/e,root)) for e in entries]
        aliases = {name}
        if row['problem_id'].endswith('web_chunky') and name=='cache':
            aliases.add('chunky.chals.sekai.team')
        original_networks = source.get('networks') or {}
        if isinstance(original_networks,dict):
            for network in original_networks.values():
                if isinstance(network,dict):
                    aliases.update(network.get('aliases') or [])
        if source.get('container_name'):
            aliases.add(source['container_name'])
        target=row['source_review'].get('target_host') or ''
        hostname=target.rsplit(':',1)[0] if ':' in target else target
        if len(services)==1 and hostname and hostname not in {'localhost','127.0.0.1'}:
            aliases.add(hostname)
        service.update(networks={'challenge':{'aliases':sorted(aliases)}},
                       restart='no', mem_limit='1g', cpus=1,
                       ulimits={'nofile':{'soft':1024,'hard':1024}},
                       security_opt=['no-new-privileges:true'])
        result[name] = service
    return result

def directory(problem, run):
    if not run or len(run)>80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in run):
        raise ValueError('run must be a short alphanumeric identity')
    key = hashlib.sha256((problem+'\0'+run).encode()).hexdigest()[:20]
    return ROOT/'output/ctf_docker'/key, 'aoctf-'+key

def prepare(problem, run):
    _, row = select(problem)
    stage, project = directory(problem,run)
    inside(ROOT/'output/ctf_docker')
    inside(stage,ROOT/'output/ctf_docker')
    stage.mkdir(parents=True,exist_ok=True)
    inputs = stage/'inputs'
    inside(inputs,stage)
    if inputs.exists():
        shutil.rmtree(inputs)
    inputs.mkdir()
    assets = [a for a in row.get('assets',[]) if a.get('role')=='agent_visible']
    kind = row['source_review']['environment_kind']
    service_mode = kind in {'service','service_declared'}
    if not assets and not service_mode:
        raise ValueError('No reviewed contestant assets')
    paths = [inside(ROOT/a['path']) for a in assets]
    common = Path(os.path.commonpath([str(p.parent) for p in paths])) if paths else inputs
    for asset,path in zip(assets,paths):
        if not asset.get('sha256') or hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:
            raise ValueError('Contestant asset hash mismatch')
        dest = inputs/path.relative_to(common)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest)
        with path.open('rb') as stream:
            signature=stream.read(4)
        if signature.startswith(b'\x7fELF') or signature.startswith(b'#!'):
            dest.chmod(0o755)
    if kind not in {'service','service_declared','static_artifacts','static_artifacts_candidate'}:
        raise ValueError('Original runtime unresolved; refusing standalone substitution')
    services = normalized_services(row,stage) if service_mode else {}
    services['contestant'] = {'image':IMAGE,'command':['sleep','infinity'], 'working_dir':'/workspace',
        'mem_limit':'1g','cpus':1,'pids_limit':256,'cap_drop':['ALL'],
        'security_opt':['no-new-privileges:true'],
        **({'networks':['challenge']} if service_mode else {'network_mode':'none'})}
    config = {'services':services}
    if service_mode:
        config['networks'] = {'challenge':{'internal':True}}
    (stage/'compose.yaml').write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    (stage/'identity.json').write_text(json.dumps({'problem_id':problem,'run':run,'project':project}),encoding='utf-8')
    return stage,project,row

def compose(stage,project,*args):
    return docker('compose','-p',project,'-f',stage/'compose.yaml',*args)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['build','inventory','prepare','start','inspect','exec','stop','reset'])
    parser.add_argument('--problem'); parser.add_argument('--run',default='local')
    parser.add_argument('--command'); parser.add_argument('--timeout',type=int,default=30)
    args=parser.parse_args()
    if args.action=='build':
        print(docker('build','-t',IMAGE,ROOT/'docker/ctf',timeout=1200)); return
    if args.action=='inventory':
        report=[]
        for c,row in records():
            kind=row['source_review']['environment_kind']
            status='static_candidate' if kind.startswith('static_artifacts') else 'blocked'
            reason=''
            if kind in {'service','service_declared'}:
                try:
                    normalized_services(row); status='compose_candidate'
                except (ValueError,OSError) as exc:
                    reason=str(exc)
            elif status=='blocked':
                reason='Missing original runtime mapping or reviewed contestant inputs'
            report.append({'competition':c,'problem_id':row['problem_id'],'kind':kind,'environment_status':status,'reason':reason})
        dest=ROOT/'output/ctf_docker/inventory.json'; dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
        from collections import Counter
        print(json.dumps({'records':len(report),'statuses':dict(Counter(r['environment_status'] for r in report)),'report':str(dest)},indent=2)); return
    if not args.problem: parser.error('--problem required')
    stage,project=directory(args.problem,args.run)
    if args.action in {'prepare','start','reset'}:
        if args.action=='reset' and (stage/'compose.yaml').exists():
            compose(stage,project,'down','--remove-orphans')
        if args.action=='prepare' or not (stage/'compose.yaml').exists() or args.action=='reset':
            stage,project,_=prepare(args.problem,args.run)
        if args.action=='prepare': print(str(stage/'compose.yaml')); return
        docker('image','inspect',IMAGE)
        compose(stage,project,'up','-d','--build')
        cid=compose(stage,project,'ps','-q','contestant').strip()
        marker=stage/'provisioned-container.txt'
        if not marker.exists() or marker.read_text()!=cid:
            docker('cp',str(stage/'inputs')+'/.',cid+':/workspace')
            marker.write_text(cid)
    if not (stage/'compose.yaml').exists(): raise ValueError('Environment not prepared')
    if args.action=='exec':
        if not args.command: parser.error('--command required')
        if not 1<=args.timeout<=120: parser.error('--timeout must be 1..120')
        cid=compose(stage,project,'ps','-q','contestant').strip()
        if not cid: raise ValueError('Contestant container is not running')
        # In-container timeout kills the command; no host shell fallback.
        print(docker('exec',cid,'timeout','-k','2',str(args.timeout),'sh','-lc',args.command,timeout=args.timeout+10))
    elif args.action=='stop': print(compose(stage,project,'down','--remove-orphans'))
    else: print(compose(stage,project,'ps','--format','json'))

if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired) as exc:
        print(str(exc),file=sys.stderr); sys.exit(1)
