"""Validate CTF records individually in fresh containers, without model calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ctf_environment_runtime import controller as c, available
from contest_adapters import _grade_non_programming
from contest_manifest import ManifestTask


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--competition', required=True, choices=['cybench', 'nyu_ctf_bench'])
    parser.add_argument('--problem', action='append')
    parser.add_argument('--report', required=True)
    parser.add_argument('--retry-blocked', action='store_true')
    args = parser.parse_args()
    dest = (ROOT / args.report).resolve()
    if not dest.is_relative_to(ROOT / 'output/ctf_docker'):
        raise ValueError('Report must be under output/ctf_docker')
    if dest.exists() and not args.retry_blocked:
        raise FileExistsError(dest)
    benchmark = ROOT / 'data/benchmarks' / args.competition / 'benchmark.json'
    rows = json.loads(benchmark.read_text())
    report = {'competition': args.competition, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'benchmark_sha256': hashlib.sha256(benchmark.read_bytes()).hexdigest(),
              'contestant_image': c.docker('image','inspect',c.IMAGE,'--format','{{.Id}}').strip(),
              'paid_model_calls': 0, 'records': []}
    if args.retry_blocked:
        previous = json.loads(dest.read_text())
        assert previous['benchmark_sha256'] == report['benchmark_sha256']
        assert previous['contestant_image'] == report['contestant_image']
        report = previous
    for row in rows:
        tid = row['problem_id']
        if args.problem and tid not in args.problem:
            continue
        prior = next((r for r in report['records'] if r['problem_id']==tid), None)
        if prior and prior['status'] == 'passed':
            continue
        item = {'problem_id': tid, 'status': 'blocked'}
        stage = project = None
        try:
            if not available(row):
                if row.get('source_review', {}).get('environment_kind') in {'service','service_declared'}:
                    c.normalized_services(row)  # Preserve the concrete mapping error in the report.
                raise ValueError('No supported reviewed runtime mapping')
            expected = str(row.get('gold_label', {}).get('expected_answer') or '')
            if not expected:
                raise ValueError('No registered final flag')
            for asset in row.get('assets', []):
                if asset.get('role') == 'agent_visible':
                    content = (ROOT / asset['path']).read_bytes()
                    if expected.encode() in content:
                        # Reviewed exception: the original LootStash reversing binary
                        # intentionally embeds the flag; it is not a copied answer file.
                        if tid != 'cybench_hackthebox_cyber-apocalypse-2024_reversing_Very_Easy_LootStash' or not content.startswith(b'\x7fELF'):
                            raise ValueError('Plaintext final flag found in contestant asset; needs review')
                        manifest = json.loads((ROOT/row['source_review']['input_manifest_path']).read_text())
                        entry = next(e for e in manifest['files'] if e['destination']==asset['path'])
                        archive = ROOT/entry['source']
                        assert '/release/' in entry['source'] and hashlib.sha256(archive.read_bytes()).hexdigest()==entry['source_sha256']
                        with zipfile.ZipFile(archive) as z:
                            assert z.read(entry['archive_member']) == content
                        item['embedded_flag_review'] = {'source':entry['source'], 'source_sha256':entry['source_sha256'], 'member':entry['archive_member'], 'basis':'Unmodified original public ELF from release ZIP; upstream init_script.sh delivers this binary.'}
            run_id = 'expand-' + uuid.uuid4().hex
            stage, project, _ = c.prepare(tid, run_id)
            c.docker('compose','-p',project,'-f',stage/'compose.yaml','up','-d','--build',timeout=90)
            cid = c.compose(stage,project,'ps','-q','contestant').strip()
            c.docker('cp',str(stage/'inputs')+'/.',cid+':/workspace')
            output = c.docker('exec',cid,'python','/opt/ctf/check_dependencies.py',timeout=30)
            assert 'check passed' in output
            for source in (stage/'inputs').rglob('*'):
                if source.is_file():
                    remote = '/workspace/' + source.relative_to(stage/'inputs').as_posix()
                    actual = c.docker('exec',cid,'sha256sum',remote).split()[0]
                    assert actual == hashlib.sha256(source.read_bytes()).hexdigest(), 'Input delivery hash mismatch'
            c.docker('exec',cid,'sh','-lc','test ! -e /var/run/docker.sock')
            info = json.loads(c.docker('inspect',cid))[0]
            assert not info['Mounts'], 'Unexpected host mounts'
            kind = row['source_review']['environment_kind']
            endpoints = c.endpoints(row) if kind in {'service','service_declared'} else []
            if kind in {'service','service_declared'}:
                assert endpoints, 'No target endpoint'
                code = 'import socket; endpoints=' + repr(endpoints) + '; [socket.create_connection(e,3).close() for e in endpoints]'
                deadline = time.monotonic() + 25
                while True:
                    try:
                        c.docker('exec',cid,'python','-c',code,timeout=10)
                        break
                    except Exception:
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(1)
                network = next(iter(info['NetworkSettings']['Networks']))
                assert json.loads(c.docker('network','inspect',network))[0]['Internal']
            else:
                assert info['HostConfig']['NetworkMode'] == 'none'
            task = ManifestTask(tid,tid,None,row['problem_description'],'ctf',1,False,row)
            assert _grade_non_programming(task, expected, args.competition) == (1,1)
            assert _grade_non_programming(task, '', args.competition) == (0,1)
            assert _grade_non_programming(task, 'wrong flag', args.competition) == (0,1)
            item.update(status='passed', kind=kind, endpoints=endpoints,
                        startup=True, dependency_check=True, input_hashes=True,
                        isolated=True, plaintext_flag_absent='embedded_flag_review' not in item, exact_grading=True)
        except Exception as exc:
            item['reason'] = str(exc)[-1800:]
        finally:
            if stage and project and (stage/'compose.yaml').exists():
                try:
                    c.compose(stage,project,'down','--remove-orphans')
                except Exception as exc:
                    item.update(status='blocked', cleanup_error=str(exc)[-500:])
        if prior:
            item['previous_attempts'] = [prior]
            report['records'][report['records'].index(prior)] = item
        else:
            report['records'].append(item)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(tid + ': ' + item['status'] + (' ' + item.get('reason','')[:150] if item['status'] != 'passed' else ''),flush=True)
    print('RESULT', sum(r['status']=='passed' for r in report['records']), '/', len(report['records']),flush=True)


if __name__ == '__main__':
    main()
