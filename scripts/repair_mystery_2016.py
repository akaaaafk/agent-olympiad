"""Complete 2016 isolated-puzzle delivery; archive unsupported workflows honestly."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from PIL import Image
import pymupdf
from pypdf import PdfWriter
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures
from dataset_catalog import update_track_index
from evaluation.gold import load_gold_parts, GoldAnswerEvaluator
from problem_pdf import read_problem_pdf

KEEP = ['02133', '02146', '02166', '02174', '02185', '02186',
        '02200', '02205', '02220', '02258', '02262']
REMOVE = {
    '02144': 'Missing playable Hangman state/action adapter and bell clue delivery. Recovered publisher code is server-private puzzle logic, not a contestant input; no word/score table is exposed.',
    '02156': 'Requires identifying phrases and release ordering in 18 Cooking with Dog video episodes. Original bag/media assets exist, but the required historical episode reference package and reproducible video delivery are not provisioned.',
    '02197': 'Meta requires other puzzle answers and hunt progression; these feeder inputs are absent from the isolated starting packet.',
    '02203': 'Original ZIP/data are intact (13,853,280 records). Missing compatible agent-readable bulk-data/computation adapter; cannot certify a runnable native short-answer task. This is not a missing-source exclusion.',
    '02218': 'Printed grids extract a CONTACT HQ instruction; receiving SELF-DECLARED requires a rap-battle performance accepted by HQ. Host workflow is absent and the registered answer is only an intermediate instruction.',
    '02241': 'Physical-object collection and host verification precede an additional numbered note. This note is not an initial contestant input; missing host workflow must not be replaced with solution material.',
}
PDF_IDS = {'02133': 'ott.pdf', '02146': 'blazing_trails.pdf',
           '02185': 'losers.pdf', '02186': 'LostSkull.pdf'}
OUTPUT = ROOT / 'data/raw/mystery_hunt/reviewed_2016_20260917/puzzles.pdf'
STAGE = ROOT / 'tmp/pdfs/mystery_2016'
MANIFEST = STAGE / 'manifest.json'
YEAR = 2016
EXTRA_HTML = {}
SELECTED_ONLY = False
SOLUTION_URLS = {}


def render_html(source, key):
    soup = BeautifulSoup(source.read_bytes(), 'html.parser')
    assert not soup.find_all('script')
    if soup.head is None:
        wrapper = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
        for node in list(soup.contents):
            wrapper.body.append(node.extract())
        soup = wrapper
    for tag in soup.find_all(['img', 'link']):
        ref = tag.get('src') or tag.get('href')
        if ref:
            assert not ref.startswith(('http:', 'https:'))
            path = source.parent / ref.split('?')[0].split('#')[0]
            assert path.is_file(), ref
            if tag.name == 'img' and path.suffix.lower() == '.gif':
                assert Image.open(path).n_frames == 1, 'Animated input needs temporal delivery, not a flattened PDF.'
    base = soup.new_tag('base', href=source.parent.as_uri() + '/')
    soup.head.insert(0, base)
    style = soup.new_tag('style')
    style.string = '@page{size:1000pt 1400pt;margin:24pt} @media print{html,body,.container{width:auto!important;max-width:none!important} img{max-width:100%;height:auto} tr{break-inside:avoid} .puzzle{background:white!important}}'
    if YEAR == 2015:
        style.string += ' @media print{img{max-height:1100pt;object-fit:contain}}'
    soup.head.append(style)
    page = STAGE / f'{key}.html'
    page.write_text(str(soup), encoding='utf-8')
    packet = STAGE / f'{key}.pdf'
    result = subprocess.run([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new', '--disable-gpu', '--no-first-run', '--disable-extensions',
        '--disable-background-networking', '--allow-file-access-from-files',
        '--no-pdf-header-footer', '--virtual-time-budget=3000',
        '--user-data-dir=' + str(STAGE / f'chrome-{key}'), '--print-to-pdf=' + str(packet), page.as_uri()],
        capture_output=True, timeout=60)
    assert result.returncode == 0 and packet.is_file(), result.stderr
    return packet


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def current():
    rows = json.loads((ROOT / 'data/benchmarks/mystery_hunt/benchmark.json').read_text(encoding='utf-8'))
    selected = {r['problem_id'][-5:]: r for r in rows if r.get('year') == YEAR}
    if SELECTED_ONLY:
        selected = {key: row for key, row in selected.items() if key in set(KEEP) | set(REMOVE)}
    assert set(selected) == set(KEEP) | set(REMOVE)
    assert all(r['evaluation']['status'] == 'not_ready' for r in selected.values())
    return rows, selected


def build():
    _, selected = current()
    assert not OUTPUT.exists() and not MANIFEST.exists(), 'Preserve earlier outputs; do not overwrite.'
    STAGE.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    records = {}
    for key in KEEP:
        row = selected[key]
        for a in row['assets']:
            assert sha(ROOT / a['path']) == a['sha256'], a['path']
        source = ROOT / row['source_file']
        soup = BeautifulSoup(source.read_bytes(), 'html.parser')
        assert not soup.find_all('script')
        start = len(writer.pages) + 1
        if key in PDF_IDS:
            packet = source.parent / PDF_IDS[key]
            assert any(a['path'] == packet.relative_to(ROOT).as_posix() and a['role'] == 'agent_visible' for a in row['assets'])
            writer.append(packet)
        elif key == '02220':
            packet = STAGE / 'replication_tiles.pdf'
            original = Image.open(source.parent / 'sudoku.png').convert('RGB')
            assert original.size == (16290, 4720)
            c = canvas.Canvas(str(packet), pagesize=(1240, 440), invariant=1)
            c.setFont('Helvetica', 12)
            c.drawString(20, 418, 'Replication: full original image overview. Following pages are lossless overlapping tiles.')
            c.drawImage(ImageReader(original), 20, 40, width=1200, height=1200*original.height/original.width)
            c.showPage()
            boxes = []
            for y in range(0, original.height, 1536):
                for x in range(0, original.width, 2136):
                    box = (x, y, min(x+2200, original.width), min(y+1600, original.height))
                    tile = original.crop(box)
                    boxes.append(box)
                    c.setPageSize((tile.width+40, tile.height+70))
                    c.setFont('Helvetica', 14)
                    c.drawString(20, tile.height+44, f'Original pixel region: x={box[0]}..{box[2]-1}, y={box[1]}..{box[3]-1}; overlap=64 pixels')
                    c.drawImage(ImageReader(tile), 20, 20, width=tile.width, height=tile.height)
                    c.showPage()
            c.save()
            with pymupdf.open(packet) as doc:
                for page, box in zip(list(doc)[1:], boxes, strict=True):
                    embedded = Image.open(io.BytesIO(doc.extract_image(page.get_images()[0][0])['image'])).convert('RGB')
                    assert embedded.tobytes() == original.crop(box).tobytes()
            writer.append(packet)
        else:
            packet = render_html(source, key)
            if key in EXTRA_HTML:
                component_paths = [packet] + [render_html(source.parent / name, key + '_extra' + str(i))
                                              for i, name in enumerate(EXTRA_HTML[key])]
                complete = PdfWriter()
                for component in component_paths:
                    complete.append(component)
                packet = STAGE / f'{key}_complete.pdf'
                with packet.open('wb') as stream:
                    complete.write(stream)
            writer.append(packet)
        pages = list(range(start, len(writer.pages)+1))
        records[key] = dict(problem_id=row['problem_id'], pages=pages,
                            record_sha256=hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest(),
                            original_packet=str(packet), original_packet_sha256=sha(packet))
        print(key, 'built pages', pages, flush=True)
    with OUTPUT.open('wb') as stream:
        writer.write(stream)
    # Every source packet page must retain identical rendered pixels after assembly.
    with pymupdf.open(OUTPUT) as bundle:
        for key, record in records.items():
            with pymupdf.open(record['original_packet']) as original:
                for local, global_page in enumerate(record['pages']):
                    a = original[local].get_pixmap(matrix=pymupdf.Matrix(.5,.5), annots=False)
                    b = bundle[global_page-1].get_pixmap(matrix=pymupdf.Matrix(.5,.5), annots=False)
                    assert a.width == b.width and a.height == b.height and a.samples == b.samples
                    bundle[global_page-1].get_pixmap(matrix=pymupdf.Matrix(.7,.7), annots=False).save(STAGE / f'page-{global_page}.png')
        count = len(bundle)
    MANIFEST.write_text(json.dumps(dict(records=records, pdf_sha256=sha(OUTPUT), pages=count), indent=2), encoding='utf-8')
    print('Review required:', count, 'pages', flush=True)


def promote():
    _, selected = current()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert sha(OUTPUT) == manifest['pdf_sha256']
    assert (STAGE / 'visual_review_passed.json').is_file(), 'Require actual complete-page visual review first.'
    review = json.loads((STAGE / 'visual_review_passed.json').read_text())
    assert review['pdf_sha256'] == sha(OUTPUT) and review['pages'] == manifest['pages']
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + f'_mystery_{YEAR}_' + uuid.uuid4().hex[:8])
    path = 'data/benchmarks/mystery_hunt/benchmark.json'
    rows = deepcopy(store.read(path))
    asset_path = f'data/raw/mystery_hunt/reviewed_{YEAR}_20260917/puzzles.pdf'
    destination = ROOT / asset_path
    if destination.resolve() != OUTPUT.resolve():
        assert not destination.exists()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OUTPUT, destination)
    allowlist = deepcopy(store.read('data/problem_pdf_allowlist.json'))
    report = dict(competition='mystery_hunt', year=YEAR, promoted=[], removed=[],
                  mini_membership='unchanged', raw_sources='preserved', paid_model_calls=0, tests={})
    for row in rows:
        if row.get('year') != YEAR:
            continue
        key = row['problem_id'][-5:]
        if SELECTED_ONLY and key not in set(KEEP) | set(REMOVE):
            continue
        slug = row['title'].split('/')[-1]
        url = SOLUTION_URLS.get(key, f'https://puzzles.mit.edu/{YEAR}/puzzle/{slug}/solution/')
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        solution_path = f'data/judge_references/mystery_hunt/{row["problem_id"]}/solution_20260917.html'
        store.save_text(solution_path, response.content.decode('utf-8'))
        if key in REMOVE:
            report['removed'].append(dict(record=deepcopy(row), reason=REMOVE[key], official_solution=url,
                                           source_evidence=solution_path, sha256=store.sha(solution_path)))
            continue
        record = manifest['records'][key]
        assert hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest() == record['record_sha256']
        expected = row['gold_label']['expected_answer']
        assert f'"{expected}"' in response.text or expected in BeautifulSoup(response.content, 'html.parser').get_text(' ', strip=True), (key, expected)
        if key == '02146':
            assert 'answer BLUE INDIGO' in response.text
            row['gold_label']['parts'][0].setdefault('aliases', []).append('BLUE INDIGO')
        row['assets'] += [dict(path=asset_path, role='agent_visible', mime_type='application/pdf', sha256=sha(OUTPUT)),
                          dict(path=solution_path, role='judge_only', mime_type='text/html', sha256=store.sha(solution_path))]
        flavor = BeautifulSoup((ROOT / row['source_file']).read_bytes(), 'html.parser')
        content = flavor.select_one('.puzzle .content')
        flavor_text = '\n'.join(p.get_text(' ', strip=True) for p in content.find_all('p', recursive=False)) if content else ''
        row['problem_description'] = (f'# {slug}\n\n{flavor_text}\n\nRead the complete reviewed puzzle pages {record["pages"]} with read_problem_pdf. '
            'Only this puzzle’s pages are approved for this task. Submit one final answer. '
            'Public historical background research is allowed; puzzle solutions and answer keys are forbidden. '
            'This is isolated puzzle-answer accuracy, not full-hunt progression or an official contest score.')
        if key == '02220':
            row['problem_description'] += ' The first page is an overview; subsequent pages are lossless, overlapping original-image tiles labeled by pixel coordinates. No clues or grid cells are filled.'
        row['evaluation'].update(evaluator_id='gold_answer_v1', status='ready_with_limitations',
            reason='Complete reviewed contestant PDF delivery and official answer verified; deterministic grading and PDF-reader checks passed.',
            limitations='Vision-capable solver required. Historical public background research may be necessary. Isolated static puzzle only, not a physical simulation or full-hunt score. Offline checks do not establish solving accuracy.')
        row.setdefault('source_review', {})[f'delivery_{YEAR}_20260917'] = dict(packet=asset_path,
            pages=record['pages'], official_solution=url, source_packet_sha256=record['original_packet_sha256'],
            visual_review=review, assembler_render_pixels_preserved=True)
        row.setdefault('provenance', {})['files'] = deepcopy(row['assets'])
        allowlist['assets'] = [a for a in allowlist['assets'] if a['problem_id'] != row['problem_id']]
        allowlist['assets'].append(dict(problem_id=row['problem_id'], path=asset_path, sha256=sha(OUTPUT),
            pages=record['pages'], review_status='approved_problem_only',
            review_evidence='All approved pages visually inspected, original contestant content only. Page assembly preserves source rendering. No answers or solution annotations.'))
        parts = load_gold_parts(row['gold_label'])
        scores = [GoldAnswerEvaluator(parts, a).evaluate().total_score for a in [expected, expected.lower(), 'WRONG FIXTURE ANSWER']]
        assert scores == [1,1,0], (key,scores)
        if key == '02146':
            assert GoldAnswerEvaluator(parts, 'BLUE INDIGO').evaluate().total_score == 1
        report['tests'][row['problem_id']] = dict(grader=scores, pages=len(record['pages']))
        report['promoted'].append(row['problem_id'])
    rows = [r for r in rows if not (r.get('year') == YEAR and r['problem_id'][-5:] in REMOVE)]
    mini = store.read('data/mini_data/benchmarks/mystery_hunt/benchmark.json')
    assert not any(r.get('year') == YEAR for r in mini)
    store.save('data/problem_pdf_allowlist.json', allowlist)
    for row in rows:
        if row.get('year') == YEAR and row['problem_id'][-5:] in KEEP:
            for page in manifest['records'][row['problem_id'][-5:]]['pages']:
                payload, attachments = read_problem_pdf(row, pages=[page])
                assert payload['status'] == 'ok' and len(attachments) == 1
    store.save(path, rows)
    rule_path = 'data/rules/mystery_hunt/evaluation.json'
    rule = store.read(rule_path)
    sync_rules('mystery_hunt', rule, rows)
    store.save(rule_path, rule)
    index = store.read('data/benchmarks/index.json')
    update_track_index(index, 'mystery_hunt', rows)
    store.save('data/benchmarks/index.json', index)
    summary_and_figures(store, index, {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']})
    store.save(f'output/mystery_{YEAR}_repair_20260917.json', report)
    store.finish(report)
    print(dict(promoted=len(report['promoted']), removed=len(report['removed']), backup=str(store.backup)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args()
    promote() if args.promote else build()
