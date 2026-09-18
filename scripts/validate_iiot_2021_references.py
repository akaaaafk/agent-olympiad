"""Compile archived publisher references and verify printed scalar/vector samples."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/iiot_2021_recovery/reference_validation.json'


def main():
    rows = json.loads((ROOT / 'data/benchmarks/iiot/benchmark.json').read_text())
    image = subprocess.run(['docker', 'image', 'inspect', 'gcc:14', '--format', '{{.Id}}'],
        capture_output=True, text=True, check=True).stdout.strip()
    results = []
    for row in rows:
        if row.get('year') != 2021:
            continue
        manifest = json.loads((ROOT / row['evaluation']['source_archive_manifest']).read_text())
        source = ROOT / manifest['reference']['path']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['reference']['sha256']
        matches = re.findall(r'Sample \d+ input:\s*```text\s*\n(.*?)```\s*Sample \d+ output:\s*(?:```text\s*\n(.*?)```|`([^`]+)`)',
            row['problem_description'], re.S)
        samples = [(stdin, block or inline) for stdin, block, inline in matches]
        assert len(samples) == 2, row['problem_id']
        item = {'problem_id': row['problem_id'], 'source_sha256': manifest['reference']['sha256'],
            'image_id': image, 'samples': [], 'official_limits': False,
            'validation_limits': {'seconds_per_sample': 15, 'memory_mb': 512}}
        name = 'ao-iiot-reference-' + uuid.uuid4().hex[:12]
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as tmp:
            folder = Path(tmp)
            shutil.copy2(source, folder / 'source.cpp')
            for i, (stdin, expected) in enumerate(samples):
                (folder / f'{i}.in').write_text(stdin, encoding='utf-8')
            script = 'cd /work && g++ -std=c++17 -O2 /input/source.cpp -o ref && '
            script += ' && '.join(f'printf "SAMPLE_{i}_BEGIN\\n" && timeout -k 1 15 ./ref < /input/{i}.in && printf "\\nSAMPLE_{i}_END\\n"' for i in range(len(samples)))
            try:
                run = subprocess.run(['docker', 'run', '--name', name, '--pull=never', '--network=none',
                    '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64', '--memory=512m', '--cpus=1',
                    '--read-only', '--tmpfs', '/work:rw,exec,size=128m', '--tmpfs', '/tmp:rw,size=64m',
                    '--mount', f'type=bind,source={folder},target=/input,readonly', image,
                    'sh', '-c', script], capture_output=True, text=True, timeout=100)
                item['exit_code'] = run.returncode
                item['stderr'] = run.stderr[-2000:]
                if run.returncode == 0:
                    for i, (stdin, expected) in enumerate(samples):
                        output = re.search(f'SAMPLE_{i}_BEGIN\\n(.*?)\\nSAMPLE_{i}_END', run.stdout, re.S)[1]
                        if manifest['task_code'] == 'chimneys':
                            parts = [list(map(int, line.split())) for line in stdin.splitlines()]
                            count, segments = parts[0][0], parts[1:]
                            tokens = iter(map(int, output.split()))
                            chains = [[next(tokens) for _ in range(next(tokens))] for _ in range(next(tokens))]
                            assert next(tokens, None) is None
                            indices = [j for chain in chains for j in chain]
                            valid = sorted(indices) == list(range(count)) and all(chain and all(
                                segments[a][1] == segments[b][0] for a, b in zip(chain, chain[1:])) for chain in chains)
                            item['samples'].append({'valid_construction': valid, 'score_validated': False})
                        else:
                            item['samples'].append({'matches_printed_output': output.split() == expected.split()})
                    item['status'] = 'samples_validated' if all(s.get('matches_printed_output', s.get('valid_construction')) for s in item['samples']) else 'sample_mismatch'
                else:
                    item['status'] = 'failed'
            except subprocess.TimeoutExpired:
                item['status'] = 'timeout'
            finally:
                subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
        results.append(item)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
        print(row['problem_id'], item['status'], flush=True)


if __name__ == '__main__':
    main()
