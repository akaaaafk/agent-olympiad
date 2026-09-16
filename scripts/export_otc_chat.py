"""Export full archived chat from saved sessions without changing those sessions."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from contest_transcript import write_communication_sidecars


def export_one(path):
    path = Path(path)
    source = json.loads(path.read_text(encoding='utf-8'))
    return write_communication_sidecars(path.parent, source)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path)
    args = parser.parse_args()
    exported = export_one(args.session)
    print(json.dumps({'event_count': exported['event_count']}))
