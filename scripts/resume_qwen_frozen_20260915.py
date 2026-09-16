"""Resume the original identity from recovered bytes, then launch the extension."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT.parent / "tinker-frozen-runtime-20260915"
OUT = ROOT / "results/tinker_task_based_arml_icpc_20260914"
NEXT = ROOT / "results/tinker_requested_remaining_20260915"
sys.path.insert(0, str(ROOT / "src"))
from dotenv import dotenv_values
values = dotenv_values(ROOT / ".env")
for name, value in values.items():
    if value is not None:
        os.environ[name] = value
sys.path.insert(0, str(SNAP / "scripts"))
from run_tinker_two_lanes import lane, read, write

keys = [os.environ.get("TINKER_API_KEY"), os.environ.get("TINKER_API_KEY2")]
if not all(keys) or keys[0] == keys[1]:
    raise ValueError("Two distinct credentials required")
registry = read(OUT / "registry.json")
registry["data"] = str(SNAP / "data")
registry["file_hashes"] = {str(SNAP / Path(p).relative_to(ROOT)): h
                           for p, h in registry["file_hashes"].items()}
lock = OUT / "supervisor.lock"
with lock.open("x") as handle:
    handle.write(str(os.getpid()))
try:
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(lane, OUT, registry, i, keys[i]) for i in range(2)]
        for future in futures:
            future.result()
    missing = [j["id"] for j in registry["jobs"]
               if not (OUT / "runs" / j["id"] / "contest_session.json").exists()]
    write(OUT / "frozen_recovery_status.json", {"solving_complete": not missing, "missing": missing})
    if missing:
        raise RuntimeError("Original solving jobs remain unfinished; extension not launched")
finally:
    lock.unlink(missing_ok=True)
print("Original solving complete; waiting for the reviewed extension registry.", flush=True)
while not (NEXT / "READY.json").exists():
    time.sleep(30)
subprocess.run([sys.executable, "-u", str(ROOT / "scripts/run_qwen_requested_remaining_20260915.py")],
               cwd=ROOT, check=True)
