"""Export the implemented, card-permitted competition preparation interface."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from action_modules.competition_tools import PROFILES
from rules.loader import DEFAULT_RULES_ROOT, load_rule_card
from rules.storage import iter_rule_card_ids
from tool_registry import ACTION_REGISTRY, ACTION_SET_VERSION, render_function_tools, resolve_action_names


def export(destination=None):
    directory = Path(destination) if destination else ROOT / "docs" / "from_zhongzheng"
    directory.mkdir(parents=True, exist_ok=True)
    stem = "competition-specific-tools-20260913"
    cards = set(iter_rule_card_ids(DEFAULT_RULES_ROOT))
    index = json.loads((DEFAULT_RULES_ROOT.parent / 'benchmarks/index.json').read_text(encoding='utf-8'))
    active = {entry['id'] for entry in index['olympiads']}
    if not active <= cards or not active <= {p.competition for p in PROFILES}:
        raise ValueError("Every active catalog track requires a rule card and tool profile")
    rows = []
    not_exposed = []
    for profile in sorted(PROFILES, key=lambda p: p.competition):
        if profile.competition not in active:
            continue
        permitted = profile.name in load_rule_card(profile.competition).allowed_tools
        runtime_names = {runtime: profile.name in resolve_action_names(profile.competition, runtime=runtime)
                         for runtime in ("env", "session")}
        if not permitted or not all(runtime_names.values()):
            not_exposed.append(dict(competition=profile.competition, name=profile.name,
                card_permitted=permitted, runtimes=runtime_names,
                current_allowed_tools=list(load_rule_card(profile.competition).allowed_tools)))
            continue
        rows.append({**asdict(profile), "status": "implemented_preparation_tool",
                     "rule_card": f"data/rules/{profile.competition}/competition.json",
                     "permission": "explicit_card_allowlist", "runtimes": runtime_names,
                     "schema": render_function_tools([ACTION_REGISTRY[profile.name]])[0]})
    report = {"action_set_version": ACTION_SET_VERSION, "competition_count": len(rows),
              "active_catalog_count": len(active), "preparation_profiles_not_exposed": not_exposed,
              "new_tool_count": len(rows), "scope": "preparation_and_structure_checks",
              "live_contest_simulators_added": False, "competitions": rows}
    (directory / f"{stem}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Competition-specific tools for {len(rows)} active competitions", "",
        "The original implementation added one task_specific tool per competition, 43 in total, using one ActionSpec registry for both env and contest-session execution. ACTION_SET_VERSION advanced from 8 to 9 while preserving the original 30 action parameter contracts.", "",
        "The subsequent v10 update added explicitly enabled stateful actions for Guts and Science Bowl; see the [two stateful pilots](competition-flow-pilots-20260913.md). This document and its original validation record describe the preparation-tool layer. Ordinary static tasks do not automatically enable the new competition flows.", "",
        "The scope covers task preparation, input validation, candidate answer/report assembly and structural checks. Tools return format_ok, issues, warnings, candidate_text and domain data. They do not assess correctness or automatically save or submit candidates. Use work to save candidates, and existing submit/submit_code actions with their permissions and review gates to submit.", "",
        "These are benchmark helper interfaces, not claims about officially permitted software. Rule-card allowed_tools explicitly includes the corresponding names. Official rules, calculator/network permissions and source text are preserved. Experiment comparisons require the new action_set_version and fresh output directories.", "",
        "Competition-specific tools use the same competition definitions across all five baselines. They make no LLM, network, external-judge or file-read calls and do not access gold answers. Results are visible only to the caller. Each invocation consumes one action turn and one tool call under the existing budget; memory-on/off differences are preserved.", "",
        "Each row below describes an implemented tool. Related competitions share underlying checks while retaining separate ownership, fields, descriptions, edition selection and permissions.", "",
        "Only preparation tools exposed by the current rule card in both runtimes appear below. The JSON field preparation_profiles_not_exposed records inactive helpers and current allowed tools, including tracks that use a dedicated staged workflow.", "",
        "| Competition | Tool | Features and behavior | Parameters |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| [{row['competition']}](../../{row['rule_card']}) | `{row['name']}` | {row['feature']} | {', '.join('`' + f + '`' for f in row['fields'])} |")
    lines += ["", "## Example inputs and results", "",
        "Purple Comet `prepare_purple_comet_answers(problem_ids=[\"q1\"], answers=[\"17\"])` produces `q1. 17`; `2+3`, negative numbers and decimals are reported as invalid formats. Problem IDs must come from the currently public packet. Partial answers list unanswered IDs.", "",
        "HMMT Guts selects nov/feb from the current task season. Three November answers form one set; the same input in February reports that four answers are required. A missing season is reported explicitly, never inferred from team size. The preparation tool does not release another set, lock submitted answers or simulate live scores.", "",
        "Power `dependencies=[\"\", \"a\"]` means the first part has no dependency and the second uses a. Missing parts, forward references and dependency cycles are reported. Graph validation does not verify a mathematical proof.", "",
        "Mystery Hunt `answers=[\"CAT\", \"DOG\"], indices=[2,2]` extracts `AO` using one-based positions in the original strings, preserving case and spaces. It does not verify feeder or meta answers.", "",
        "Wharton reports over-allocation for 60%+50%. WSC reports duplicate authors or tasks that violate the three-author assignment structure. Measurement checks cover aligned arrays, finite values, units and nonnegative uncertainty while preserving contestant-provided provenance.", "",
        "## Single-team scope and required task environments", "",
        "All competitions follow the [single-team scope](single-team-scope.md). Opponent generation, two-team competition and cross-team coalitions are outside the implementation scope and are not missing features or runtime blockers. Descriptions about not simulating opponents state this boundary only.", "",
        "Required team environments retain their actual implementation status: task release in Physics Brawl/Mystery Hunt, quiz answer eligibility and phases, CTF containers, CCDC services, WRO robot interfaces, team debate roles and speeches, and WSC independent-writing stages. Guts release and Science Bowl team-answer stages exist in explicitly enabled stateful pilots; preparation tools do not perform those state changes.", "",
    ]
    for row in rows:
        if row["limitation"] != "Checks structure and supplied evidence only, not correctness.":
            lines.append(f"- **{row['competition']}**: {row['limitation']}")
    lines += ["", "## Code and reproduction", "",
        "- Registry and per-competition contracts: `src/action_modules/competition_tools.py`.",
        "- Deterministic execution: `src/competition_tool_runtime.py`; accepts only allowlisted public selectors and contestant input.",
        "- Env, session and adapters share the implementation. Rule cards, competition ownership, active tasks/locks and assignments still govern access.",
        "- Generate the inventory: `python scripts/export_competition_tools.py`.",
        "- Focused checks: `python -m unittest discover -s tests -p test_competition_tools.py`.",
        "- The JSON inventory includes the complete native function schema for every tool.", "",
        "See [validation.json](competition-specific-tools-20260913-validation.json) for the original unit tests, 43-by-5 offline smoke, both execution entry points and rule-preservation checks.", "",
    ]
    (directory / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"competitions": len(rows), "tools": len(rows), "output": str(directory / f"{stem}.md")}))
    return report


if __name__ == "__main__":
    export()
