"""Isolated 32768-token OTC pilot with response-metadata diagnostics."""
import json
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT.parent / "openagents-runtime-20260914"
OUT = ROOT / "results/openagents_glm52_arml2009_otc_32768probe_20260915"
sys.path.insert(0, str(ROOT / "src"))
from env_config import load_repo_dotenv
load_repo_dotenv()
sys.path.insert(0, str(RUNTIME / "src"))
import llm

if (OUT / "run_config.json").exists():
    raise SystemExit("Existing pilot; refuse automatic paid replay")
OUT.mkdir(parents=True, exist_ok=True)
original_resolve = llm.resolve_request_fn

def diagnostic_resolve(*args, **kwargs):
    request_fn = original_resolve(*args, **kwargs)
    def call(request):
        started = time.time()
        record = dict(purpose=request.purpose, requested_limit=kwargs.get("max_output_tokens"),
                      metadata=request.metadata, started_at=started)
        with (OUT / "response_metadata.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(event="request_started", **record)) + "\n")
        try:
            response = request_fn(request)
            record.update(usage=response.usage, text_chars=len(response.text),
                          tools=[t.name for t in response.tool_calls])
            return response
        except Exception as exc:
            record.update(error_type=type(exc).__name__)
            raise
        finally:
            record["elapsed_seconds"] = time.time() - started
            with (OUT / "response_metadata.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(dict(event="request_finished", **record)) + "\n")
    return call

llm.resolve_request_fn = diagnostic_resolve
sys.argv = [str(RUNTIME / "src/run_competition_batch.py"),
    "--live", "--provider", "openagents", "--model", "glm-5.2",
    "--contest-manifest", str(ROOT / "data/contest_manifests/arml_local_2009.json"),
    "--system-variant", "otc", "--team-size", "6", "--rules-mode", "enforced",
    "--action-calling", "native", "--max-output-tokens", "32768", "--max-total-tokens", "220000",
    "--temperature", "0.2", "--judge-collab", "--judge-provider", "openagents",
    "--judge-model", "glm-5.2", "--no-judge-cce", "--output", str(OUT)]
exit_code = 1
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
    exit_code = 0
finally:
    (OUT / "launcher_exit.json").write_text(json.dumps(dict(exit_code=exit_code)), encoding="utf-8")
