"""Recover current publisher-linked IIOT 2021 tests; never infer judge rules."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from recover_iiot_2023_tests_20260913 import listing
CACHE = ROOT / 'tmp/iiot_2021_recovery'
URL = 'https://iio.team/competition/tasks/2021'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def fetch(url):
    response = requests.get(url, timeout=(15, 50))
    response.raise_for_status()
    return response


def discover():
    CACHE.mkdir(parents=True, exist_ok=True)
    html = fetch(URL).text
    (CACHE / 'publisher.html').write_text(html, encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    tasks = []
    for heading in soup.find_all('h2'):
        title = heading.get_text(' ', strip=True)
        match = re.search(r'\((\w+)\)', title)
        if not match:
            continue
        links = {}
        for node in heading.next_siblings:
            if getattr(node, 'name', None) in {'h1', 'h2'}:
                break
            if hasattr(node, 'find_all'):
                for anchor in node.find_all('a', href=True):
                    links[anchor.get_text(' ', strip=True)] = anchor['href']
        task = {'task': match[1], 'title': title, 'links': links, 'files': []}
        url = links.get('Test cases')
        if url:
            fid = re.search(r'/folders/([^?]+)', url)[1]
            def walk(folder, prefix=''):
                raw = fetch('https://drive.google.com/drive/folders/' + folder).text
                (CACHE / (folder + '.html')).write_text(raw, encoding='utf-8')
                children = listing(raw, folder)
                for child in children:
                    name = child['name']
                    if '/' in name or '\\' in name or name in {'.', '..'}:
                        raise ValueError('Unsafe publisher filename')
                    if child['mime'] == 'application/vnd.google-apps.folder':
                        walk(child['id'], prefix + name + '/')
                    else:
                        task['files'].append({**child, 'relative': prefix + name})
            try:
                walk(fid)
            except Exception as exc:
                task['discovery_error'] = str(exc)
        tasks.append(task)
        write(CACHE / 'discovery.json', {'publisher': URL, 'checked_at': datetime.now(timezone.utc).isoformat(), 'tasks': tasks})
        print(task['task'], len(task['files']), task.get('discovery_error', ''), flush=True)
    if len(tasks) != 8:
        raise ValueError('Expected exactly eight official final tasks')


def download():
    discovery = json.loads((CACHE / 'discovery.json').read_text())
    jobs = [(task['task'], file) for task in discovery['tasks'] if not task.get('discovery_error') for file in task['files']]
    def one(job):
        name, file = job
        target = CACHE / 'files' / name / file['relative']
        try:
            if target.exists():
                payload = target.read_bytes()
            else:
                payload = fetch('https://drive.google.com/uc?export=download&id=' + file['id']).content
                if payload.lstrip().lower().startswith((b'<!doctype', b'<html')):
                    raise ValueError('HTML returned instead of test file')
                if file.get('bytes') is not None and len(payload) != int(file['bytes']):
                    raise ValueError('Publisher size mismatch')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            return {**file, 'task': name, 'path': target.relative_to(ROOT).as_posix(),
                'sha256': hashlib.sha256(payload).hexdigest(), 'actual_bytes': len(payload)}
        except Exception as exc:
            return {**file, 'task': name, 'error': str(exc)}
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for result in executor.map(one, jobs):
            results.append(result)
            if len(results) % 20 == 0 or result.get('error'):
                write(CACHE / 'downloads.json', results)
                print(len(results), '/', len(jobs), 'errors', sum('error' in r for r in results), flush=True)
    write(CACHE / 'downloads.json', results)
    print('Finished', len(results), 'errors', sum('error' in r for r in results))


if __name__ == '__main__':
    {'discover': discover, 'download': download}[sys.argv[1]]()
