"""Bind Docker workspaces to controller-selected tasks and run identities."""
import importlib.util
import hashlib
from pathlib import Path
import subprocess

_path = Path(__file__).resolve().parents[1]/'scripts/ctf_docker.py'
_spec = importlib.util.spec_from_file_location('ctf_docker_controller',_path)
controller = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(controller)

def available(benchmark):
    if not benchmark.get('source_review',{}).get('upstream_source_directory'):
        return False
    kind=benchmark['source_review'].get('environment_kind')
    if kind in {'static_artifacts','static_artifacts_candidate'}:
        return any(a.get('role')=='agent_visible' for a in benchmark.get('assets',[]))
    if kind in {'service','service_declared'}:
        try:
            controller.normalized_services(benchmark)
            return True
        except (ValueError,OSError):
            return False
    return False

def execute(competition,problem,run,action,arguments):
    if competition not in {'cybench','nyu_ctf_bench'}:
        raise ValueError('Docker environment is not supported for this competition')
    if not run:
        raise ValueError('Controller run identity required for Docker isolation')
    actual,row=controller.select(problem)
    if actual!=competition or not available(row):
        raise ValueError('Task has no reviewed Docker environment mapping')
    run='session-'+hashlib.sha256(str(run).encode()).hexdigest()[:24]
    stage,project=controller.directory(problem,run)
    if action in {'start_environment','reset_environment'}:
        if action=='reset_environment' and (stage/'compose.yaml').exists():
            controller.compose(stage,project,'down','--remove-orphans')
        if not (stage/'compose.yaml').exists() or action=='reset_environment':
            stage,project,_=controller.prepare(problem,run)
        controller.docker('image','inspect',controller.IMAGE)
        controller.compose(stage,project,'up','-d','--build')
        cid=controller.compose(stage,project,'ps','-q','contestant').strip()
        # Only provision files on first start; resume preserves contestant edits.
        marker=stage/'provisioned-container.txt'
        if not marker.exists() or marker.read_text()!=cid:
            controller.docker('cp',str(stage/'inputs')+'/.',cid+':/workspace')
            marker.write_text(cid)
    if not (stage/'compose.yaml').exists():
        return {'valid':False,'error':'Start the environment first.'}
    if action=='execute_environment_command':
        command=arguments.get('command')
        timeout=arguments.get('timeout',30)
        if not isinstance(command,str) or not command.strip():
            raise ValueError('Nonempty command required')
        if type(timeout) is not int or not 1<=timeout<=120:
            raise ValueError('Timeout must be an integer in 1..120')
        cid=controller.compose(stage,project,'ps','-q','contestant').strip()
        if not cid: return {'valid':False,'error':'Contestant container is not running.'}
        try:
            output=controller.docker('exec',cid,'timeout','-k','2',str(timeout),'sh','-lc',command,timeout=timeout+10)
            return {'valid':True,'result':output[:20000]}
        except RuntimeError as exc:
            return {'valid':True,'result':str(exc)[:20000],'command_failed':True}
    import json
    containers=[json.loads(line) for line in controller.compose(stage,project,'ps','--format','json').splitlines() if line.strip()]
    routes=controller.endpoints(row) if row['source_review']['environment_kind'] in {'service','service_declared'} else []
    return {'valid':True,'result':{'containers':[{'service':c['Service'],'state':c['State'],'health':c.get('Health','')} for c in containers],
        'targets':[{'host':host,'port':port,'address':f'{host}:{port}'} for host,port in routes], 'workspace':'/workspace',
        'public_files':[a['path'].split('/')[-1] for a in row.get('assets',[]) if a.get('role')=='agent_visible']}}
