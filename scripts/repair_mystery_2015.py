"""Apply the reviewed isolated-delivery migration to the existing 2015 subset."""
import argparse
import repair_mystery_2016 as repair

repair.YEAR = 2015
repair.KEEP = ['01985', '01997', '02002', '02008', '02035', '02040',
               '02044', '02045', '02103', '02107', '02109', '02124']
repair.REMOVE = {
    '01970': 'Original animated Sokoban GIFs and chat moves are intact. Missing temporal/game delivery adapter; a single flattened frame is not an approved reconstruction.',
    '01994': 'Original drum-performance video/audio are intact. Rhythmic audio and performer/video synchronization are required; current PDF/native reader has no audiovisual delivery adapter.',
    '01995': 'Chemistry meta requires feeder answers and ordering images; the isolated initial page only requests calling in a submarine upgrade.',
    '02007': 'Dory requires applying its own errata to other puzzle inputs and comparing changed answers. Referenced puzzle packets and cross-puzzle state are absent from this isolated task.',
    '02030': 'Goldfish Memory requires playable browser/JavaScript state and action delivery, absent from the native puzzle reader. Do not expose private script answers or replace play with solution text.',
    '02037': 'Original polymorphic TIFF/ext2 binary is intact. Solving requires read-only filesystem/inode analysis, not only viewing an image; the compatible isolated binary-analysis environment is not provisioned.',
    '02062': 'Optics meta requires feeder answers and physical clue components; the isolated initial page only requests calling in a submarine upgrade.',
    '02080': 'School of Fish meta requires feeder answers and round components; the isolated initial page only requests calling in a submarine upgrade.',
}
repair.PDF_IDS = {}
repair.EXTRA_HTML = {'01997': ['clickbait.html']}
repair.OUTPUT = repair.ROOT / 'data/raw/mystery_hunt/reviewed_2015_20260917/puzzles.pdf'
repair.STAGE = repair.ROOT / 'tmp/pdfs/mystery_2015'
repair.MANIFEST = repair.STAGE / 'manifest.json'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args()
    repair.promote() if args.promote else repair.build()
