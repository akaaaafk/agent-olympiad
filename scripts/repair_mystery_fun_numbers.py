"""Deliver the original-history/base-ten branch, not the full two-history puzzle."""
import argparse
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import uuid
import io

from bs4 import BeautifulSoup, Comment
import pymupdf
import requests
from PIL import Image as PillowImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from scripts.repair_data_catalog import Store, sync_rules, summary_and_figures
from dataset_catalog import update_track_index
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from problem_pdf import read_problem_pdf

PID = 'mystery_hunt_01361'
PDF = 'data/raw/mystery_hunt/reviewed_numbers_20260917/fun_numbers_base10.pdf'
SCOPE = ('Solve only the original-history version using base 10 throughout. '
         'Submit its final answer. The alternate-history/base-27 version is excluded: '
         'its supplementary 1983 material is not provided. This is one isolated puzzle, not full-hunt scoring.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args()
    store = Store(ROOT, ROOT.parent / 'dataset_backups')
    store.backup = store.backup.with_name(store.backup.name + '_hunt_numbers_' + uuid.uuid4().hex[:8])
    path = 'data/benchmarks/mystery_hunt/benchmark.json'
    rows = deepcopy(store.read(path))
    row = next(r for r in rows if r['problem_id'] == PID)
    assert row['evaluation']['status'] == 'not_ready'
    source = store.path(row['source_file'])
    soup = BeautifulSoup(source.read_text(encoding='utf-8'), 'html.parser')
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()  # HTML comments are not rendered contestant wording.
    clues = soup.find_all('li')
    assert len(clues) == 26 and len(soup.find_all('img')) == 1
    assert soup.img['src'] == 'formula.gif'
    for asset in row['assets']:
        assert store.sha(asset['path']) == asset['sha256']
    target = ROOT / PDF
    if not args.promote:
        if target.exists():
            store.archive(PDF)  # Preserve failed-build output before regeneration.
        target.parent.mkdir(parents=True, exist_ok=True)
        styles = getSampleStyleSheet()
        style = styles['BodyText']
        style.fontSize = 10
        style.leading = 13
        story = [Paragraph('Fun With Numbers - original history', styles['Title']),
                 Paragraph(SCOPE, style), Spacer(1, 12)]
        story += [Paragraph(''.join(map(str, p.contents)), style) for p in soup.find_all('p')]
        story += [Spacer(1, 10), Image(str(source.parent / 'formula.gif'), width=414, height=148), Spacer(1, 10)]
        story += [Paragraph(''.join(map(str, li.contents)), style, bulletText='-') for li in clues]
        SimpleDocTemplate(str(target), leftMargin=42, rightMargin=42, topMargin=36, bottomMargin=36).build(story)
        with pymupdf.open(target) as pdf:
            normalize = lambda s: ''.join(s.split())
            extracted = normalize(''.join(p.get_text() for p in pdf))
            assert all(normalize(li.get_text()) in extracted for li in clues)
            assert 'RUNUPASCORE' not in extracted
            previews = ROOT / 'tmp/pdfs/mystery_numbers_review'
            previews.mkdir(parents=True, exist_ok=True)
            for i, page in enumerate(pdf):
                page.get_pixmap(dpi=110).save(previews / f'page-{i+1}.png')
            print({'pdf': str(target), 'pages': len(pdf), 'clues_verified': 26, 'preview': str(previews)})
        return
    assert target.is_file()
    with pymupdf.open(target) as pdf:
        normalize = lambda s: ''.join(s.split())
        extracted = normalize(''.join(p.get_text() for p in pdf))
        assert all(normalize(li.get_text()) in extracted for li in clues)
        assert 'RUNUPASCORE' not in extracted
        images = [image for page in pdf for image in page.get_images()]
        assert len(images) == 1
        white = lambda image: PillowImage.alpha_composite(
            PillowImage.new('RGBA', image.size, 'white'), image.convert('RGBA')).convert('RGB')
        embedded = white(PillowImage.open(io.BytesIO(pdf.extract_image(images[0][0])['image'])))
        original_image = white(PillowImage.open(source.parent / 'formula.gif'))
        assert embedded.size == original_image.size and embedded.tobytes() == original_image.tobytes()
    response = requests.get(row['source_url'] + 'solution.html', timeout=30)
    response.raise_for_status()
    solution = BeautifulSoup(response.content, 'html.parser').get_text(' ', strip=True)
    assert 'RUN UP A SCORE / FEEL LIKE A MILLION' in solution
    assert 'original history' in solution and 'base 27' in solution
    evidence_path = 'data/raw/mystery_hunt/reviewed_numbers_20260917/official_solution.html'
    store.save_text(evidence_path, response.content.decode('utf-8'))
    asset_path = 'data/raw/mystery_hunt/reviewed_numbers_20260917/fun_numbers_base10.pdf'
    # Binary generated contestant input belongs in data, not runtime output.
    import shutil
    destination = store.path(asset_path)
    if target.resolve() != destination.resolve():
        assert not destination.exists()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, destination)
    digest = store.sha(asset_path)
    row['assets'] += [dict(path=asset_path, role='agent_visible', mime_type='application/pdf', sha256=digest),
                      dict(path=evidence_path, role='judge_only', mime_type='text/html', sha256=store.sha(evidence_path))]
    row['problem_description'] = SCOPE + '\nRead the reviewed PDF with read_problem_pdf; it contains all 26 clues and the unchanged formula image.'
    row['evaluation'].update(evaluator_id='gold_answer_v1', status='ready_with_limitations',
        reason='All 26 original clues and formula delivered in reviewed PDF; original-history short-answer grading tested.',
        limitations='Base-ten original-history branch only. Alternate-history base-27 and supplementary 1983 context excluded; no full-hunt progression or official score claim.')
    with pymupdf.open(target) as pdf:
        pages = list(range(1, len(pdf)+1))
    allowlist = store.read('data/problem_pdf_allowlist.json')
    assert not any(a['problem_id'] == PID for a in allowlist['assets'])
    allowlist['assets'].append(dict(problem_id=PID, path=asset_path, sha256=digest, pages=pages,
        review_status='approved_problem_only', review_evidence='All rendered pages visually reviewed; 26 clue texts verified; original formula image, no solution. Base-ten branch explicitly bounded.'))
    store.save('data/problem_pdf_allowlist.json', allowlist)
    for page in pages:
        payload, attachments = read_problem_pdf(row, pages=[page])
        assert payload['status'] == 'ok' and len(attachments) == 1
    parts = load_gold_parts(row['gold_label'])
    assert row['gold_label']['expected_answer'] == 'RUN UP A SCORE'
    scores = {a: GoldAnswerEvaluator(parts, a).evaluate().total_score
              for a in ['RUN UP A SCORE', 'run up a score', 'WRONG', 'FEEL LIKE A MILLION']}
    assert list(scores.values()) == [1, 1, 0, 0]
    row.setdefault('source_review', {})['base10_delivery'] = dict(original_html=source.relative_to(ROOT).as_posix(),
        original_html_sha256=store.sha(source.relative_to(ROOT)), formula_sha256=store.sha(source.parent.relative_to(ROOT) / 'formula.gif'),
        official_solution_url=row['source_url'] + 'solution.html', pdf=asset_path, pdf_sha256=digest,
        clues=26, pages=pages, branch='original history/base 10', grader_tests=scores)
    store.save(path, rows)
    rule_path = 'data/rules/mystery_hunt/evaluation.json'
    rule = store.read(rule_path)
    sync_rules('mystery_hunt', rule, rows)
    store.save(rule_path, rule)
    index = store.read('data/benchmarks/index.json')
    update_track_index(index, 'mystery_hunt', rows)
    store.save('data/benchmarks/index.json', index)
    summary_and_figures(store, index, {t['id']: store.read(t['benchmark_path']) for t in index['olympiads']})
    report = dict(competition='mystery_hunt', promoted=[PID], removed=[], paid_model_calls=0,
                  mini_membership='unchanged', raw_sources='preserved', grader_tests=scores, scope=SCOPE)
    store.save('output/hunt_numbers_repair_20260917.json', report)
    store.finish(report)
    print(report)


if __name__ == '__main__':
    main()
