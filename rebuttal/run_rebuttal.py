"""Run one Claude Code harness setting on one contest manifest.

    python rebuttal/run_rebuttal.py --setting single --manifest data/contest_manifests/arml_local_2009.json
    python rebuttal/run_rebuttal.py --setting multi  --manifest ... --team-size 3
    python rebuttal/run_rebuttal.py --setting otc    --manifest ... --team-size 3

All settings use the same model, the same restricted Claude Code tool set,
the same number of contest rounds (the competition's engine turn budget) and
the same per-invocation inner-turn cap. Only the team structure changes:

  single : 1 Claude Code agent, its own harness loop
  multi  : N Claude Code agents, shared board + shared sheet, no OTC protocol
  otc    : OTC contest engine unchanged, each seat's API call -> its Claude Code instance

Results: <output>/result.json (+ <output>/engine/ for otc), graded with the
same deterministic grader the engine uses (grade_contest_result).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_code import policy  # noqa: E402
from claude_code.cc_client import DEFAULT_MODEL  # noqa: E402


def main(argv=None) -> dict:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--setting", required=True, choices=("single", "multi", "otc"))
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--team-size", type=int, default=3, help="multi/otc: number of Claude Code instances")
    p.add_argument("--rounds", type=int, default=None,
                   help="contest rounds (default: the competition's engine turn budget)")
    p.add_argument("--max-inner-turns", type=int, default=8,
                   help="Claude Code --max-turns per invocation (same for every setting)")
    p.add_argument("--max-output-tokens", type=int, default=None)
    p.add_argument("--otc-variant", default="otc", help="otc or vallina_otc")
    p.add_argument("--impl", default="engine", choices=("engine", "standalone"),
                   help="single/multi: engine presets (single_agent / decentralized) with Claude Code seats, "
                        "or the standalone Claude Code harness loops")
    p.add_argument("--session-mode", default="per_call", choices=("per_call", "per_seat"),
                   help="otc only: fresh Claude Code conversation per engine call, or one per seat")
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--bedrock-model", default=None,
                   help="run Claude Code on AWS Bedrock with this model id / inference profile ARN "
                        "(sets AO_CC_BEDROCK_MODEL; AWS credentials from the normal AWS chain)")
    p.add_argument("--aws-region", default=None, help="Bedrock region (default us-east-1)")
    p.add_argument("--workspace-root", type=Path, default=None,
                   help="where agent workspaces live (default: a temp dir outside the repo)")
    args = p.parse_args(argv)
    import os
    if args.bedrock_model:
        os.environ["AO_CC_BEDROCK_MODEL"] = args.bedrock_model
    if args.aws_region:
        os.environ["AO_CC_AWS_REGION"] = args.aws_region

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    manifest = policy.load_manifest(args.manifest)
    out = args.output or policy.REPO_ROOT / "results" / "rebuttal_claude_code" / f"{manifest.session_id}_{args.setting}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    # Workspaces must sit outside the repo/data roots, which are denied to agents.
    ws = args.workspace_root or Path(tempfile.mkdtemp(prefix=f"cc_{args.setting}_"))
    rounds = policy.contest_rounds(manifest.competition_id, args.rounds)
    common = dict(model=args.model, max_inner_turns=args.max_inner_turns, max_output_tokens=args.max_output_tokens)
    started = datetime.now(timezone.utc)

    if args.setting == "single" and args.impl == "standalone":
        from claude_code.single import run_single
        result = run_single(manifest, workspace_root=ws, rounds=rounds, **common)
    elif args.setting == "multi" and args.impl == "standalone":
        from claude_code.multi import run_multi
        result = run_multi(manifest, workspace_root=ws, rounds=rounds, team_size=args.team_size, **common)
    else:
        from claude_code.otc import run_engine
        variant = {"single": "single_agent", "multi": "decentralized"}.get(args.setting, args.otc_variant)
        session = run_engine(args.manifest, output=out, workspace_root=ws, team_size=args.team_size,
                             variant=variant, max_turns=rounds, session_mode=args.session_mode, **common)
        result = {"setting": args.setting, "impl": "engine", "team_size": session["harness"]["team_size"],
                  "variant": session["system_variant"], "submissions": session["submissions"],
                  "budget": session["budget"], "usage": session["harness"]["total"],
                  "harness": session["harness"], "engine_output": str(out / "engine")}

    result["grade"] = policy.grade(manifest, result["submissions"])
    result.update(session_id=manifest.session_id, competition_id=manifest.competition_id, model=args.model,
                  rounds=rounds, max_inner_turns=args.max_inner_turns, workspace_root=str(ws),
                  started_at=started.isoformat(), ended_at=datetime.now(timezone.utc).isoformat())
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    g = result["grade"]
    print(f"[{args.setting}] {manifest.session_id}: score={g['score']}/{g['max_score']} "
          f"utility={g['task_utility']} usage={result['usage']} -> {out / 'result.json'}")
    return result


if __name__ == "__main__":
    main()
