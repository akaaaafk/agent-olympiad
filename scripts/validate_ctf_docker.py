"""Exercise all static Docker deliveries; prepare service candidates without paid agents."""
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ctf_docker as c

def main():
    report=[]
    for competition,row in c.records():
        kind=row['source_review']['environment_kind']
        if kind not in {'static_artifacts','static_artifacts_candidate','service','service_declared'}:
            continue
        item={'competition':competition,'problem_id':row['problem_id'],'kind':kind}
        project=None
        stage=None
        try:
            stage,project,_=c.prepare(row['problem_id'],'delivery-validation-20260916')
            c.compose(stage,project,'config','--quiet')
            if kind.startswith('static_artifacts'):
                c.compose(stage,project,'up','-d')
                cid=c.compose(stage,project,'ps','-q','contestant').strip()
                c.docker('cp',str(stage/'inputs')+'/.',cid+':/workspace')
                # Prove byte identity across Docker cp, not just file presence.
                for path in (stage/'inputs').rglob('*'):
                    if path.is_file():
                        remote='/workspace/'+path.relative_to(stage/'inputs').as_posix()
                        actual=c.docker('exec',cid,'sha256sum',remote).split()[0]
                        assert actual==hashlib.sha256(path.read_bytes()).hexdigest(),remote
                info=json.loads(c.docker('inspect',cid))[0]
                assert not info['Mounts']
                assert info['HostConfig']['NetworkMode']=='none'
                item['status']='static_delivery_validated'
            else:
                item['status']='compose_prepared_not_runtime_validated'
        except Exception as exc:
            item.update(status='blocked',reason=str(exc)[-2000:])
        finally:
            if project and stage and kind.startswith('static_artifacts'):
                c.compose(stage,project,'down','--remove-orphans')
        report.append(item)
        dest=c.ROOT/'output/ctf_docker/validation.json'
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(row['problem_id']+': '+item['status'],flush=True)
    from collections import Counter
    print(json.dumps(dict(Counter(x['status'] for x in report)),indent=2))

if __name__=='__main__': main()
