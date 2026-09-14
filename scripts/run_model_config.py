"""Run a model profile through the shared contest runner; preview by default."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from env_config import load_repo_dotenv


def read_config(path: Path, allowed: set[str]) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError(f"Invalid or unknown configuration fields: {path}")
    return value


def build_command(model: dict, experiment: dict, variant: str, output: Path, resume: bool) -> list[str]:
    command = [sys.executable, "-u", str(ROOT / "src/run_competition_batch.py"),
               "--live", "--provider", model["provider"], "--model", model["model"],
               "--judge-provider", model["provider"], "--judge-model", model["model"],
               "--action-calling", model["action_calling"],
               "--system-variant", variant, "--output", str(output)]
    for key, value in experiment.items():
        flag = "--" + key.replace("_", "-")
        if isinstance(value, bool):
            command.append(flag if value else "--no-" + key.replace("_", "-"))
        else:
            command.extend([flag, str(value)])
    if resume:
        command.append("--resume")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-config", type=Path, required=True)
    parser.add_argument("--experiment-config", type=Path,
                        default=Path("configs/experiments/arml2009.json"))
    parser.add_argument("--variant", default="vallina_otc")
    parser.add_argument("--output", type=Path, required=True,
                        help="Use a separate directory for each model/method/repetition.")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Actually call the model; otherwise preview only.")
    args = parser.parse_args()
    os.chdir(ROOT)
    model = read_config(args.model_config, {"provider", "model", "base_url", "api_key_env", "action_calling"})
    experiment = read_config(args.experiment_config, {
        "contest_manifest", "temperature", "max_output_tokens", "max_total_tokens",
        "start_seat", "deadline_submit", "judge_task", "judge_collab", "judge_cce",
    })
    if model.get("provider") not in {"tinker", "openai"}:
        raise ValueError("Profile provider must be tinker or openai")
    if not all(model.get(key) for key in ("model", "api_key_env", "action_calling")):
        raise ValueError("Model profile requires model, api_key_env and action_calling")
    if not Path(experiment.get("contest_manifest", "")).is_file():
        raise ValueError("Experiment requires an existing contest_manifest")
    if model["provider"] == "openai" and not model.get("base_url"):
        raise ValueError("OpenAI-compatible profiles require an explicit base_url")
    command = build_command(model, experiment, args.variant, args.output.resolve(), args.resume)
    # Validate against the actual runner and its resume fingerprint without API calls.
    from run_competition_batch import inspect_contest_run
    state, identity = inspect_contest_run(command[3:])
    print(json.dumps({"command": command, "state": state,
                      "execution": identity["settings"]["execution"],
                      "config": identity["settings"]["config"],
                      "api_key_env": model["api_key_env"],
                      "base_url": model.get("base_url"),
                      "execute": args.execute}, ensure_ascii=False, indent=2), flush=True)
    if not args.execute:
        return 0
    load_repo_dotenv()
    key = os.environ.get(model["api_key_env"])
    if not key:
        raise ValueError(f"Missing credential environment variable: {model['api_key_env']}")
    child_env = os.environ.copy()
    if model["provider"] == "openai":
        child_env.update(OPENAI_BASE_URL=model["base_url"], OPENAI_API_KEY=key, OPENAGENTS_API_KEY=key)
    else:
        child_env["TINKER_API_KEY"] = key
    return subprocess.run(command, cwd=ROOT, env=child_env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
