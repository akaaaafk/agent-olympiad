"""Build/start isolated source services and probe their original TCP routes."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ctf_docker as c

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--startup-timeout',type=int,default=90)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--problem',action='append',help='Validate only these original task ids')
    parser.add_argument('--report',default='service_validation.json',help='Report filename under output/ctf_docker')
    args=parser.parse_args()
    if Path(args.report).name!=args.report:parser.error('--report must be a filename')
    dest=c.ROOT/'output/ctf_docker'/args.report
    report=json.loads(dest.read_text()) if args.resume and dest.exists() else []
    done={r['problem_id'] for r in report}
    for competition,row in c.records():
        if args.problem and row['problem_id'] not in args.problem:continue
        if row['problem_id'] in done or row['source_review']['environment_kind'] not in {'service','service_declared'}:
            continue
        stage=project=None
        item={'competition':competition,'problem_id':row['problem_id']}
        try:
            stage,project,_=c.prepare(row['problem_id'],'service-validation-20260916')
            c.docker('compose','-p',project,'-f',stage/'compose.yaml','up','-d','--build',timeout=args.startup_timeout)
            cid=c.compose(stage,project,'ps','-q','contestant').strip()
            endpoints=c.endpoints(row)
            if not endpoints:raise ValueError('No original TCP port mapping to validate')
            code='import socket; endpoints='+repr(endpoints)+'; '+"[(lambda s:s.close())(socket.create_connection(e,3)) for e in endpoints]; print('connected')"
            deadline=time.monotonic()+25
            while True:
                try:
                    c.docker('exec',cid,'python','-c',code,timeout=10)
                    break
                except (RuntimeError,subprocess.TimeoutExpired):
                    if time.monotonic()>=deadline:raise
                    time.sleep(1)
            containers=[json.loads(line) for line in c.compose(stage,project,'ps','--all','--format','json').splitlines() if line.strip()]
            services=[x for x in containers if x['Service']!='contestant']
            if any(x['State']!='running' for x in services):
                raise ValueError('Original service exited after startup')
            item.update(status='tcp_runtime_validated',endpoints=endpoints,
                        containers=[{'service':x['Service'],'state':x['State'],'health':x.get('Health','')} for x in services],
                        flag_contract='not_yet_validated')
        except Exception as exc:
            item.update(status='blocked',reason=str(exc)[-2400:])
        finally:
            if stage and project and (stage/'compose.yaml').exists():
                try:c.compose(stage,project,'down','--remove-orphans')
                except Exception as exc:item['cleanup_error']=str(exc)[-500:]
        report.append(item)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(row['problem_id']+': '+item['status'],flush=True)
    from collections import Counter
    print(json.dumps(dict(Counter(x['status'] for x in report)),indent=2))

if __name__=='__main__':main()
