"""Restore only mini_data's original Pattern Recognition static packet."""
import copy
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import shutil
from urllib.parse import urljoin, urlsplit
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / 'data/mini_data'
PID = 'mystery_hunt_01497'
URL = 'https://puzzles.mit.edu/2011/puzzles/world1/pattern_recognition/'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    catalog = MINI / 'benchmarks/mystery_hunt/benchmark.json'
    rows = read(catalog)
    row = next(r for r in rows if r['problem_id'] == PID)
    if row.get('source_review', {}).get('mini_static_repair'):
        print('Already repaired; run the validation test.')
        return
    before = copy.deepcopy(row)
    original = ROOT / row['source_file']
    soup = BeautifulSoup(original.read_bytes(), 'html.parser')
    videos = [dict(a.attrs) for a in soup.find_all('area')]
    assert len(videos) == 18
    folder = MINI / 'raw/mystery_hunt/pattern_recognition_static/input'
    folder.mkdir(parents=True, exist_ok=True)
    sources = {}
    session = requests.Session()

    def fetch(url):
        if url in sources:
            return sources[url]['name']
        url_secure = url.replace('http://yui.yahooapis.com/', 'https://yui-s.yahooapis.com/')
        response = session.get(url_secure, timeout=40)
        response.raise_for_status()
        data = response.content
        name = hashlib.sha256(url.encode()).hexdigest()[:10] + '_' + Path(urlsplit(url).path).name
        sources[url] = {'name': name, 'source_sha256': hashlib.sha256(data).hexdigest()}
        if name.endswith('.css'):
            text = data.decode('utf-8-sig')
            assert '@import' not in text.lower()
            def replace(match):
                value = match.group(1).strip(' \t\r\n\"\'')
                return 'url(' + fetch(urljoin(url, value)) + ')'
            data = re.sub(r'url\(([^)]+)\)', replace, text).encode('utf-8')
        destination = folder / name
        destination.write_bytes(data)
        if destination.suffix.lower() in ('.jpg', '.png', '.gif'):
            with Image.open(destination) as image:
                image.verify()
        sources[url]['sha256'] = hashlib.sha256(data).hexdigest()
        return name

    for tag in soup.find_all('script'):
        tag.decompose()
    soup.find(id='puzzletopbar').decompose()
    for tag in soup.find_all(['img', 'link']):
        attr = 'src' if tag.name == 'img' else 'href'
        tag[attr] = fetch(urljoin(URL, tag[attr]))
    assert [dict(a.attrs) for a in soup.find_all('area')] == videos
    packet = folder / 'puzzle.html'
    packet.write_text(str(soup), encoding='utf-8')
    assets = []
    for p in sorted(folder.iterdir()):
        assets.append({'path': p.relative_to(ROOT).as_posix(), 'role': 'agent_visible',
                       'mime_type': mimetypes.guess_type(p)[0] or 'application/octet-stream',
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    limitation = ('The seven original puzzle panels, image map and styles are archived. '
                  'All 18 original YouTube links and map coordinates are preserved, but video '
                  'availability/content and offline video delivery remain unverified. '
                  'Runtime visual delivery and grading are not validated; retain not_ready.')
    row.update(source_url=URL, source_file=packet.relative_to(ROOT).as_posix(), assets=assets,
        problem_description='# Pattern Recognition\n\nOpen `puzzle.html` for the seven original visual panels. '
            'The sixth panel has 18 original video links; these videos are not included in the offline packet.\n\n'
            + soup.find(id='puzzlecontent').find('em').get_text() + '\n',
        asset_policy='Only sanitized puzzle HTML and explicit static dependencies are agent-visible. Original video links are retained as unresolved external dependencies.',
        source_visibility='static_packet_with_unresolved_external_videos')
    row['evaluation']['limitations'] = limitation
    row['source_review'] = {'mini_static_repair': True, 'original_source_file': before['source_file'],
        'original_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
        'dependencies': sources, 'external_video_links': videos, 'scope': 'mini_data only'}
    row['provenance'].update(source_url=URL, source_file=row['source_file'],
        files=[{k: a[k] for k in ('path', 'role', 'sha256')} for a in assets])
    for key in ('gold_label', 'total_points', 'year', 'split', 'license'):
        assert row[key] == before[key]
    assert row['evaluation']['status'] == 'not_ready'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ROOT / 'tmp' / ('mini_pattern_before_' + stamp)
    backup.mkdir(parents=True)
    for relative in ('benchmarks/mystery_hunt/benchmark.json', 'rubrics/task_scorecards/mystery_hunt.json',
                     'dependency_manifest.json'):
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MINI / relative, destination)
    write(backup / 'manifest.json', {'problem_id': PID, 'scope': 'mini_data only', 'before': before})
    write(catalog, rows)
    cards_path = MINI / 'rubrics/task_scorecards/mystery_hunt.json'
    cards = read(cards_path)
    next(c for c in cards['records'] if c['problem_id'] == PID)['limitations'] = limitation
    write(cards_path, cards)
    manifest_path = MINI / 'dependency_manifest.json'
    manifest = read(manifest_path)
    for a in assets:
        p = ROOT / a['path']
        upstream = next((u for u, info in sources.items() if info['name'] == p.name), None)
        manifest['files'][p.relative_to(MINI).as_posix()] = {
            'source': upstream or before['source_file'], 'source_sha256': sources[upstream]['source_sha256'] if upstream else row['source_review']['original_sha256'],
            'sha256': a['sha256'], 'transformation': 'Static dependency localization and archive navigation removal; video map preserved.'}
    write(manifest_path, manifest)
    print(json.dumps({'problem_id': PID, 'public_assets': len(assets), 'video_links_unresolved': len(videos),
                      'status': row['evaluation']['status'], 'backup': str(backup)}))


if __name__ == '__main__':
    main()
