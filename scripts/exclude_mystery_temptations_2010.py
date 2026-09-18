"""Exclude an archived host-exchange puzzle incorrectly keyed to the host response."""
import hashlib
from bs4 import BeautifulSoup
import requests
from exclude_mystery_interactive_2010 import main


if __name__ == '__main__':
    url = 'https://puzzles.mit.edu/2010/puzzles/1952/temptations/solution.html'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = BeautifulSoup(response.content, 'html.parser').get_text(' ', strip=True)
    assert 'BRING US CIBO' in text
    assert 'When teams provided HQ with' in text
    assert 'they were provided the puzzle answer, DOGES' in text
    main(
        targets={'mystery_hunt_01324': (
            'Turkish Delight and other treats suitable for a ruler.',
            'Official solution yields BRING US CIBO, then requires delivering Italian food to HQ to receive DOGES. Missing host exchange; keyed final answer is not derivable from the isolated contestant packet.')},
        report_path='output/hunt_temptations_exclusion_20260917.json',
        required_limitation='No physical enactment, cross-task state or end-to-end grading is supplied.',
        external_evidence={'url': url, 'sha256': hashlib.sha256(response.content).hexdigest(),
                           'original_html': response.content.decode('utf-8'), 'reviewed_text': text},
    )
