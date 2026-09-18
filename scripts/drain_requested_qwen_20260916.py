"""Adopt existing children; finish these jobs without scheduling the queue."""
import concurrent.futures
import ctypes
import json
import os
import sys
import time
from pathlib import Path
import run_requested_qwen_10lane_20260916 as batch


def alive(pid):
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def drain(item, job, key):
    dest = Path(job['output'])
    result = dest / 'result.json'
    log = batch.OUT / 'logs' / (job['id'] + '.log')
    paths = [log, dest / 'contest_checkpoint.json', dest / 'calls.jsonl', result]
    last = max([time.time()] + [p.stat().st_mtime for p in paths if p.exists()])
    while alive(item['pid']):
        last = max([last] + [p.stat().st_mtime for p in paths if p.exists()])
        if time.time() - last > 480:
            import subprocess
            subprocess.run(['taskkill', '/PID', str(item['pid']), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            while alive(item['pid']):
                time.sleep(1)
            print('watchdog resume current job', job['id'], flush=True)
            return batch.worker(job, key)
        time.sleep(5)
    status = batch.read(result).get('status', 'failed') if result.exists() else 'failed'
    state_path = batch.OUT / 'states' / (job['id'] + '.json')
    state = batch.read(state_path)
    state.update(status=status, finished_at=time.time(), drained=True)
    batch.write(state_path, state)
    print(job['id'], status, flush=True)


if __name__ == '__main__':
    sys.path.insert(0, str(batch.ROOT / 'src'))
    from dotenv import dotenv_values
    values = dotenv_values(batch.ROOT / '.env')
    keys = [values['TINKER_API_KEY'], values['TINKER_API_KEY2']]
    active = json.loads((batch.OUT / 'drain_active_jobs.json').read_text(encoding='utf-8-sig'))
    jobs = {j['id']: j for j in batch.read(batch.OUT / 'registry.json')['jobs']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(drain, item, jobs[item['id']], keys[i % 2])
                   for i, item in enumerate(active)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    batch.write(batch.OUT / 'drain_finished.json', dict(status='paused_after_current', time=time.time()))
    (batch.OUT / 'supervisor.lock').unlink(missing_ok=True)
