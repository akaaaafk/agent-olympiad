"""Run an isolated OpenAgents OTC pilot without editing active Tinker sources."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from env_config import load_repo_dotenv

parser = argparse.ArgumentParser()
parser.add_argument("variant", choices=("vallina_otc", "otc"))
args = parser.parse_args()
load_repo_dotenv()
runtime = ROOT.parent / "openagents-runtime-20260914"
out = ROOT / "results" / ("openagents_glm52_arml2009_" + args.variant + "_8192fix_20260914")
out.mkdir(parents=True, exist_ok=True)
if (out / "run_config.json").exists():
    raise SystemExit("Existing run found; do not repeat a paid pilot automatically")
command = [sys.executable, "-u", str(runtime / "src/run_competition_batch.py"),
           "--live", "--provider", "openagents", "--model", "glm-5.2",
           "--contest-manifest", str(ROOT / "data/contest_manifests/arml_local_2009.json"),
           "--system-variant", args.variant, "--team-size", "6", "--rules-mode", "enforced",
           "--action-calling", "native", "--max-output-tokens", "8192", "--max-total-tokens", "220000",
           "--temperature", "0.2", "--judge-collab", "--judge-provider", "openagents",
           "--judge-model", "glm-5.2", "--no-judge-cce", "--output", str(out)]
with (out / "runner.log").open("a", encoding="utf-8") as log:
    result = subprocess.run(command, cwd=runtime, stdout=log, stderr=subprocess.STDOUT)
(out / "launcher_exit.json").write_text(json.dumps({"exit_code": result.returncode}), encoding="utf-8")
raise SystemExit(result.returncode)
