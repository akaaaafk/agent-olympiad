"""Check mini dependency snapshots without changing provenance or task data."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / 'data/mini_data'


def audit():
    manifest = json.loads((MINI / 'dependency_manifest.json').read_text())
    issues = []
    for relative, binding in manifest['files'].items():
        path = (MINI / relative).resolve()
        if not path.is_relative_to(MINI) or not path.is_file():
            issues.append({'path': relative, 'kind': 'missing_or_external'})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if binding.get('mini_sha256') and digest != binding['mini_sha256']:
            issues.append({'path': relative, 'kind': 'mini_snapshot_drift', 'actual': digest})
    return issues


if __name__ == '__main__':
    issues = audit()
    print(json.dumps(issues, indent=2))
    sys.exit(bool(issues))
