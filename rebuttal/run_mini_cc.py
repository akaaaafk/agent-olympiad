"""Run the mini catalog (data/mini_data) for one Claude Code setting.

    python rebuttal/run_mini_cc.py all --setting single --model claude-haiku-4-5 --output results/mini_cc_single
    python rebuttal/run_mini_cc.py all --setting multi  --model claude-haiku-4-5 --output results/mini_cc_multi
    python rebuttal/run_mini_cc.py all --setting otc    --model claude-haiku-4-5 --output results/mini_cc_otc

This is ``scripts/run_mini_dataset.py`` (= ``scripts/run_pipeline.py`` on
``data/mini_data``) with three changes and nothing else:

1. ``--setting`` picks the engine preset: single -> ``single_agent``,
   multi -> ``decentralized``, otc -> ``otc`` (``--otc-variant vallina_otc``
   is also accepted);
2. every child job runs through ``rebuttal/cc_child.py``, so each model call
   (seats, Coach, judges) goes to Claude Code (``--provider anthropic`` is
   the internal route);
3. every competition's active roster is pinned to ``--team-size`` (default 3)
   through a copied rules tree under ``<output>/rules_overlay``. single_agent
   always uses 1 seat.

Everything else (registration, Docker/VJudge-Kattis checks for ICPC, CTF image
checks, artifact routes, resume, the report) is the pipeline's own code. Other
pipeline flags (``--competitions``, ``--years``, ``--sessions``, ``--limit``,
``--max-turns``...) pass through unchanged.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHILD = Path(__file__).resolve().parent / "cc_child.py"
VARIANTS = {"single": "single_agent", "multi": "decentralized", "otc": "otc"}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--setting", required=True, choices=sorted(VARIANTS))
    pre.add_argument("--team-size", type=int, default=3)
    pre.add_argument("--otc-variant", default="otc", choices=("otc", "vallina_otc"))
    pre.add_argument("--data-root", type=Path, default=ROOT / "data" / "mini_data")
    pre.add_argument("--max-inner-turns", type=int, default=None)
    pre.add_argument("--session-mode", choices=("per_call", "per_seat"), default=None)
    pre.add_argument("--bedrock-model", default=None,
                   help="run Claude Code on AWS Bedrock with this model id / inference profile ARN "
                        "(sets AO_CC_BEDROCK_MODEL; AWS credentials from the normal AWS chain)")
    pre.add_argument("--aws-region", default=None, help="Bedrock region (default us-east-1)")
    ours, rest = pre.parse_known_args(argv)
    if any(a == "--system-variant" or a.startswith("--system-variant=") for a in rest):
        raise SystemExit("use --setting instead of --system-variant")
    if any(a == "--provider" or a.startswith("--provider=") for a in rest):
        raise SystemExit("the provider is fixed to the Claude Code route")

    os.environ["AGENT_OLYMPIAD_DATA_ROOT"] = str(ours.data_root.resolve())
    if ours.bedrock_model:
        os.environ["AO_CC_BEDROCK_MODEL"] = ours.bedrock_model
    if ours.aws_region:
        os.environ["AO_CC_AWS_REGION"] = ours.aws_region
    if ours.max_inner_turns:
        os.environ["AO_CC_MAX_INNER_TURNS"] = str(ours.max_inner_turns)
    if ours.session_mode:
        os.environ["AO_CC_SESSION_MODE"] = ours.session_mode
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts"))

    spec = importlib.util.spec_from_file_location("run_pipeline_cc", ROOT / "scripts" / "run_pipeline.py")
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)

    from claude_code import policy
    import otc_artifact_pipeline
    import run_competition_batch as rcb

    out_arg = next((rest[i + 1] for i, a in enumerate(rest) if a == "--output" and i + 1 < len(rest)), None)
    out = Path(out_arg or ROOT / "results" / f"mini_cc_{ours.setting}").resolve()
    out.mkdir(parents=True, exist_ok=True)
    overlay = policy.team_rules_overlay(None, max(ours.team_size, 2), out)
    rules_flag = ["--rules-root", str(overlay)]

    # Identity checks inside the pipeline must see the same rules root as the child.
    original_inspect = rcb.inspect_contest_run
    rcb.inspect_contest_run = lambda cli: original_inspect([*cli, *rules_flag])
    original_prepare = otc_artifact_pipeline.prepare_artifact_run

    def prepare(**kw):
        kw.setdefault("rules_root", overlay)
        if kw.get("rules_root") is None:
            kw["rules_root"] = overlay
        return original_prepare(**kw)
    otc_artifact_pipeline.prepare_artifact_run = prepare

    original_command = pipeline.command

    def command(job, out_dir, args, **kw):
        cmd = original_command(job, out_dir, args, **kw)
        if cmd is None:
            return None
        script = Path(cmd[2]).name
        kind = {"run_competition_batch.py": "batch", "run_otc_artifact.py": "artifact"}[script]
        return [cmd[0], cmd[1], str(CHILD), kind, *cmd[3:], *rules_flag]
    pipeline.command = command

    variant = VARIANTS[ours.setting] if ours.setting != "otc" else ours.otc_variant
    sys.argv = ["run_pipeline.py", *rest, "--provider", "anthropic", "--system-variant", variant,
                *([] if out_arg else ["--output", str(out)])]
    print(f"Claude Code setting={ours.setting} variant={variant} team_size="
          f"{1 if variant == 'single_agent' else ours.team_size} data={ours.data_root} rules={overlay} "
          f"backend={'bedrock:' + ours.bedrock_model if ours.bedrock_model else 'first_party'}", flush=True)
    return pipeline.main()


if __name__ == "__main__":
    raise SystemExit(main())
