"""Real Docker checks through the contest task executor, without model calls."""
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ctf_environment_runtime import controller as c
from contest_adapters import EnvironmentTaskExecutor
from contest_manifest import ContestManifest,ManifestTask

def main():
    problem='nyu_ctf_2013f-cry-stfu'
    competition,row=c.select(problem)
    task=ManifestTask(problem,problem,None,row['problem_description'],'ctf',1,False,row)
    executor=EnvironmentTaskExecutor(ContestManifest('docker-smoke',competition,(task,)),benchmark_root=c.ROOT/'data/benchmarks')
    executor.submission_run_id='docker-runtime-smoke-20260916'
    stage,project=c.directory(problem,'session-'+hashlib.sha256(executor.submission_run_id.encode()).hexdigest()[:24])
    report={}
    try:
        assert executor(task,'start_environment',{})['valid']
        result=executor(task,'execute_environment_command',{'command':'file stfu; ./stfu 2>&1 | head -c 100; echo persisted > sentinel; test ! -e challenge.json; test ! -e /var/run/docker.sock'})
        assert result['valid'] and not result.get('command_failed'),result
        report['file_and_binary_command']=result['result']
        assert executor(task,'start_environment',{})['valid']
        result=executor(task,'execute_environment_command',{'command':'cat sentinel'})
        assert result['result'].strip()=='persisted',result
        report['resume_preserved_workspace']=True
        assert executor(task,'reset_environment',{})['valid']
        result=executor(task,'execute_environment_command',{'command':'test ! -e sentinel && echo reset'})
        assert result['result'].strip()=='reset',result
        report['reset_cleared_workspace']=True
        report['timeout']=executor(task,'execute_environment_command',{'command':'sleep 10','timeout':1})
        assert report['timeout'].get('command_failed'),report
        report['containers']=executor(task,'inspect_environment',{})['result']
    finally:
        if (stage/'compose.yaml').exists(): c.compose(stage,project,'down','--remove-orphans')
    # Real Windows Compose plugin timeout, including inherited pipe cleanup.
    timeout_file=stage/'startup-timeout.yaml'
    timeout_file.write_text('services:\n  wait:\n    image: python:3.11-slim\n    command: [sleep, infinity]\n    network_mode: none\n    healthcheck:\n      test: [CMD, "false"]\n      interval: 1s\n      retries: 120\n',encoding='utf-8')
    timeout_project=project+'-timeout'
    started=time.monotonic()
    try:
        try:
            c.docker('compose','-p',timeout_project,'-f',timeout_file,'up','-d','--wait','--wait-timeout','120',timeout=2)
            raise AssertionError('Expected startup timeout')
        except subprocess.TimeoutExpired:
            elapsed=time.monotonic()-started
            assert elapsed<12,elapsed
            report['host_compose_plugin_timeout_seconds']=elapsed
    finally:
        c.docker('compose','-p',timeout_project,'-f',timeout_file,'down','--remove-orphans')
    destination=c.ROOT/'output/ctf_docker/runtime_smoke.json'
    destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
