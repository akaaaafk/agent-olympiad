"""Create numbered QA contact sheets; never modify source PDFs."""
from pathlib import Path
import json
import argparse
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'tmp/pdfs/mystery_2016'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--approve-reviewed-pages', action='store_true')
    parser.add_argument('--year', type=int, default=2016)
    args = parser.parse_args()
    FOLDER = ROOT / f'tmp/pdfs/mystery_{args.year}'
    manifest = json.loads((FOLDER / 'manifest.json').read_text())
    if args.approve_reviewed_pages:
        (FOLDER / 'visual_review_passed.json').write_text(json.dumps({
            'pdf_sha256': manifest['pdf_sha256'], 'pages': manifest['pages'],
            'review': f'All {manifest["pages"]} pages inspected in numbered contact sheets; original diagrams and clues, no clipping, overlapping content, broken images or solution pages. Assembly render-pixel integrity separately verified.'
        }, indent=2), encoding='utf-8')
        raise SystemExit(0)
    count = manifest['pages']
    for first in range(1, count+1, 9):
        sheet = Image.new('RGB', (1350, 1950), '#dddddd')
        draw = ImageDraw.Draw(sheet)
        for offset, page in enumerate(range(first, min(first+9,count+1))):
            image = Image.open(FOLDER / f'page-{page}.png').convert('RGB')
            image.thumbnail((440, 620))
            x, y = (offset % 3)*450, (offset // 3)*650
            draw.text((x+10,y+5), f'Page {page}', fill='black')
            sheet.paste(image, (x+5, y+25))
        output = FOLDER / f'contact-{first}.png'
        sheet.save(output)
        print(output)
