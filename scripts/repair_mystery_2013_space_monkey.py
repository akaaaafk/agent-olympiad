"""Archive Space Monkey Mafia's unsupported HQ performance workflow; retain its original score PDF."""
import argparse
import repair_mystery_2016 as repair

repair.YEAR = 2013
repair.SELECTED_ONLY = True
repair.KEEP = []
repair.REMOVE = {'01692': 'Original three-page score is intact. Its extraction SING ABOUT COINS is an instruction, not the final hunt answer. Publisher states teams must sing at HQ to receive AVENGERS. Missing performance acceptance/HQ response adapter; do not replace the starting packet with the host response or certify the intermediate label as final-answer accuracy.'}
repair.PDF_IDS = {'01692': 'puzzle.pdf'}
repair.SOLUTION_URLS = {'01692': 'https://puzzles.mit.edu/2013/coinheist.com/feynman/space_monkey_mafia/answer/index.html'}
repair.OUTPUT = repair.ROOT / 'data/raw/mystery_hunt/reviewed_2013_20260917/puzzles.pdf'
repair.STAGE = repair.ROOT / 'tmp/pdfs/mystery_2013'
repair.MANIFEST = repair.STAGE / 'manifest.json'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args()
    if args.promote:
        import requests
        from bs4 import BeautifulSoup
        response = requests.get(repair.SOLUTION_URLS['01692'], timeout=30)
        response.raise_for_status()
        text = BeautifulSoup(response.content, 'html.parser').get_text(' ', strip=True)
        assert 'SING ABOUT COINS' in text and 'AVENGERS' in text
        assert 'Teams who came to HQ and sang about coins' in text
        repair.promote()
    else:
        # Export the original sheet music for source preservation, not readiness.
        repair.KEEP = ['01692']
        repair.REMOVE = {}
        repair.build()
