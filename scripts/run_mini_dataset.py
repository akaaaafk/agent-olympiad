"""Run the self-contained mini dataset through the normal evaluated pipeline."""
import os
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
os.environ['AGENT_OLYMPIAD_DATA_ROOT'] = str(ROOT / 'data/mini_data')

if __name__ == '__main__':
    runpy.run_path(str(ROOT / 'scripts/run_pipeline.py'), run_name='__main__')
