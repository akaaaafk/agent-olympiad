"""Select an isolated data catalog without changing the default dataset."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def data_root():
    value = os.environ.get('AGENT_OLYMPIAD_DATA_ROOT')
    root = Path(value).resolve() if value else REPO_ROOT / 'data'
    if value and not (root / 'benchmarks/index.json').is_file():
        raise ValueError(f'Dataset has no benchmark index: {root}')
    return root
