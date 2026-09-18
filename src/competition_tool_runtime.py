"""Deterministic, gold-blind implementation of competition preparation tools.

The shared interface accepts only public identifiers/selectors and the caller's
work. It never receives a benchmark row, evaluator, filesystem path resolver,
network client, or submission mutator.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
import json
import math
import re
from typing import Any

from action_modules.competition_tools import BY_NAME


SELECTORS = ("season", "division", "event", "year", "host_year", "category", "age_group", "competition_scope")


def public_context(competition, task_id, *, expected_ids=(), metadata=None, task_metadata=None):
    """Allowlist edition selectors; never forward arbitrary benchmark metadata."""
    selected = {}
    for source in (metadata or {}, task_metadata or {}):
        for key in SELECTORS:
            value = source.get(key)
            if isinstance(value, (str, int)) and not isinstance(value, bool):
                selected[key] = str(value)
    return {"competition_id": competition, "task_id": task_id,
            "expected_problem_ids": [str(i) for i in expected_ids], "selectors": selected}


def _number(value):
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _duplicates(values):
    return sorted(v for v, count in Counter(values).items() if count > 1)


def _dependency_issues(ids, dependencies):
    graph = {}
    issues = []
    positions = {key: i for i, key in enumerate(ids)}
    for key, text in zip(ids, dependencies):
        refs = [r.strip() for r in text.split(",") if r.strip()]
        graph[key] = refs
        for ref in refs:
            if ref not in positions:
                issues.append(f"{key}: unknown dependency {ref}")
            elif positions[ref] >= positions[key]:
                issues.append(f"{key}: dependency {ref} is not an earlier part")
    # Iterative DFS keeps maliciously deep caller graphs off the Python stack.
    visited, visiting = set(), set()
    for root in ids:
        stack = [(root, False)]
        while stack:
            node, leaving = stack.pop()
            if leaving:
                visiting.discard(node)
                visited.add(node)
            elif node in visiting:
                issues.append(f"circular proof dependency at {node}")
                break
            elif node not in visited:
                visiting.add(node)
                stack.append((node, True))
                stack.extend((ref, False) for ref in graph.get(node, ()) if ref in graph)
    return graph, list(dict.fromkeys(issues))


def execute_preparation_tool(action: str, arguments: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Return format diagnostics and a candidate, without mutating contest state."""
    from tool_registry import ACTION_REGISTRY, validate_action_payload

    profile = BY_NAME.get(action)
    if profile is None or context.get("competition_id") != profile.competition:
        raise ValueError("preparation tool belongs to a different competition")
    errors = validate_action_payload(ACTION_REGISTRY[action], arguments)
    if errors:
        raise ValueError("; ".join(errors))
    from argument_limits import PREPARATION_MAX_CHARS
    if len(json.dumps(arguments, ensure_ascii=False)) > PREPARATION_MAX_CHARS:
        raise ValueError(f"preparation input exceeds {PREPARATION_MAX_CHARS} characters")
    issues, warnings = [], []
    data = {}
    candidate = ""
    arrays = {k: v for k, v in arguments.items() if isinstance(v, list)}
    lengths = {len(v) for v in arrays.values()}
    if len(lengths) > 1:
        issues.append("Parallel arrays must have the same number of rows")
    if any(len(v) > 200 for v in arrays.values()):
        issues.append("At most 200 rows may be checked at once")
    allowed_blank = {"dependencies", "counterexamples", "uncertainties", "inputs", "expected_outputs", "justifications"}
    for key, value in arguments.items():
        rows = value if isinstance(value, list) else [value]
        for index, row in enumerate(rows):
            if isinstance(row, str) and not row.strip() and key not in allowed_blank:
                # Short-answer mode has no multiple-choice option text.
                if key == "option_text" and arguments.get("answer_type") == "short_answer":
                    continue
                issues.append(f"{key}[{index}]: empty value")
            if isinstance(row, (int, float)) and (isinstance(row, bool) or not math.isfinite(row)):
                issues.append(f"{key}[{index}]: expected a finite number")
    if not issues:
        kind = profile.kind
        if kind in {"answers", "integers", "seasonal_answers", "guts", "event_answers"}:
            ids, answers = arguments["problem_ids"], arguments["answers"]
            ids = [i.strip() for i in ids]
            duplicates = _duplicates(ids)
            if duplicates:
                issues.append(f"Duplicate problem ids: {duplicates}")
            expected = context.get("expected_problem_ids") or []
            unknown = sorted(set(ids) - set(expected)) if expected else []
            if unknown:
                issues.append(f"Unknown problem ids: {unknown}; use the current packet's exact ids")
            data["missing_problem_ids"] = [i for i in expected if i not in ids]
            if data["missing_problem_ids"] and kind != "guts":
                warnings.append("Partial sheet: some current packet problems have no supplied answer")
            if kind == "integers":
                for key, answer in zip(ids, answers):
                    if not re.fullmatch(r"[0-9]+", answer.strip()):
                        issues.append(f"{key}: Purple Comet requires a non-negative integer, not an expression")
            season = str(context.get("selectors", {}).get("season", "")).lower()
            season = {"november": "nov", "february": "feb"}.get(season, season)
            if kind in {"guts", "seasonal_answers"} and season not in {"nov", "feb"}:
                issues.append("The task must select season nov or feb; do not guess from team size")
            if kind == "guts" and season in {"nov", "feb"}:
                size = 3 if season == "nov" else 4
                data["set_size"] = size
                if len(ids) != size:
                    issues.append(f"{season} Guts candidate set needs exactly {size} answers")
            if kind == "event_answers":
                for selector in ("season", "division", "event"):
                    if selector not in context.get("selectors", {}):
                        issues.append(f"Selected event packet is missing {selector}")
            candidate = "\n".join(f"{key}. {answer.strip()}" for key, answer in zip(ids, answers))
            if kind == "seasonal_answers" and season == "feb":
                if any(not proof.strip() for proof in arguments["justifications"]):
                    issues.append("February Team Round needs a justification for each supplied answer")
                candidate = "\n\n".join(f"{key}. {answer.strip()}\nJustification: {proof.strip()}"
                    for key, answer, proof in zip(ids, answers, arguments["justifications"]))
            data["answer_count"] = len(ids)
        elif kind == "proofs":
            ids = [i.strip() for i in arguments["part_ids"]]
            if _duplicates(ids):
                issues.append("Proof part ids must be unique")
            graph, dependency_errors = _dependency_issues(ids, arguments["dependencies"])
            issues.extend(dependency_errors)
            data["dependency_graph"] = graph
            candidate = "\n\n".join(f"{key}. {claim}\nProof: {proof}\nUses: {deps or 'none'}"
                for key, claim, proof, deps in zip(ids, arguments["claims"], arguments["proofs"], arguments["dependencies"]))
        elif kind in {"quantities", "measurements"}:
            for i, (value, unit) in enumerate(zip(arguments["values"], arguments["units"])):
                if _number(value) is None:
                    issues.append(f"row {i + 1}: value must be a finite numeric literal")
                if kind == "quantities" and unit.strip() != arguments["required_units"][i].strip():
                    issues.append(f"row {i + 1}: unit differs from the supplied required unit; no implicit conversion")
                if kind == "measurements":
                    text = arguments["uncertainties"][i].strip()
                    uncertainty = _number(text) if text else None
                    if text and (uncertainty is None or uncertainty < 0):
                        issues.append(f"row {i + 1}: uncertainty must be a finite non-negative literal")
                    if not text:
                        warnings.append(f"row {i + 1}: uncertainty not supplied")
            data["rows"] = [dict(zip(arrays, row)) for row in zip(*arrays.values())]
            warnings.append("Values and source references are supplied by the contestant; observation provenance is not authenticated")
        elif kind == "io_cases":
            if _duplicates(arguments["case_ids"]):
                issues.append("Test case ids must be unique")
            by_input = {}
            for case, stdin, stdout in zip(arguments["case_ids"], arguments["inputs"], arguments["expected_outputs"]):
                if stdin in by_input and by_input[stdin][1] != stdout:
                    issues.append(f"Contradictory expected outputs for cases {by_input[stdin][0]} and {case}")
                by_input[stdin] = (case, stdout)
            data["cases"] = [dict(zip(("id", "stdin", "expected_stdout"), row))
                             for row in zip(arguments["case_ids"], arguments["inputs"], arguments["expected_outputs"])]
            data["test_scope"] = "contestant_supplied"
        elif kind in {"linguistics", "observations", "constraints", "ai_artifacts", "authorities"}:
            data["rows"] = [dict(zip(arrays, row)) for row in zip(*arrays.values())]
            if kind == "linguistics":
                if _duplicates(arguments["rule_ids"]):
                    issues.append("Linguistic rule ids must be unique")
                data["rules_with_counterexamples"] = [key for key, example in zip(arguments["rule_ids"], arguments["counterexamples"]) if example.strip()]
                if data["rules_with_counterexamples"]:
                    warnings.append("Some proposed linguistic rules have supplied counterexamples")
            if kind == "authorities":
                allowed_sides = {"applicant", "respondent"} if profile.competition == "jessup" else {"claimant", "respondent"}
                if any(side.strip().lower() not in allowed_sides for side in arguments["sides"]):
                    issues.append(f"Sides must be one of {sorted(allowed_sides)}")
                warnings.append("Citations and facts are not independently verified")
            if kind == "ai_artifacts":
                if _duplicates(arguments["artifact_names"]):
                    issues.append("Artifact names must be unique")
                if not context.get("selectors", {}).get("year"):
                    issues.append("The task must select an IOAI year; the 2024 and 2025 contracts differ")
                if any(not re.fullmatch(r"[\w.+-]+/[\w.+-]+", value) for value in arguments["media_types"]):
                    issues.append("Each media type must be a MIME type such as image/png")
                warnings.append("Inventory does not verify file existence or edition-specific scoring requirements")
        elif kind in {"short_answer", "science_answer", "flag"}:
            key = "flag" if kind == "flag" else "answer"
            answer = arguments[key].strip()
            if "\n" in answer or "\r" in answer:
                issues.append("The answer must be a single line")
            if kind == "science_answer":
                if arguments["answer_type"] not in {"multiple_choice", "short_answer"}:
                    issues.append("answer_type must be multiple_choice or short_answer")
                elif arguments["answer_type"] == "multiple_choice":
                    if not re.fullmatch(r"[WXYZABCD]", answer):
                        issues.append("Multiple-choice answer must be one option letter from the provided question")
                    answer = f"{answer}. {arguments['option_text'].strip()}"
                elif arguments["option_text"].strip():
                    issues.append("option_text must be empty for a short answer")
            candidate = answer
            if kind == "flag":
                data["recovery_evidence"] = arguments["recovery_evidence"]
                data["flag_verified"] = False
        elif kind == "speeches":
            expected = ["PM", "LO", "DPM", "DLO", "MG", "MO", "GW", "OW"]
            if arguments["roles"] != expected:
                issues.append(f"Complete BP transcript must use exactly this order: {expected}")
            candidate = "\n\n".join(f"{role}\n{speech}" for role, speech in zip(arguments["roles"], arguments["speeches"]))
        elif kind == "portfolio":
            symbols = [s.strip().upper() for s in arguments["symbols"]]
            if _duplicates(symbols):
                issues.append("Duplicate holdings: combine their allocations explicitly")
            weights = [Decimal(str(w)) for w in arguments["weights_percent"]]
            if any(w < 0 or w > 100 for w in weights):
                issues.append("Each supplied long-only allocation must lie between 0 and 100 percent")
            total = sum(weights, Decimal(0))
            data.update(total_percent=str(total), unallocated_percent=str(Decimal(100) - total))
            if total > 100:
                issues.append("Portfolio is overallocated above 100 percent")
            elif total < 100:
                warnings.append("Allocation is below 100 percent; identify cash or an intentionally partial portfolio")
            data["positions"] = [dict(symbol=s, weight_percent=str(w), rationale=r)
                for s, w, r in zip(symbols, weights, arguments["rationales"])]
            data["client_objectives"] = arguments["client_objectives"]
            warnings.append("Does not verify trading eligibility, prices, suitability, or actual holdings")
        elif kind == "extraction":
            if _duplicates(arguments["feeder_ids"]):
                issues.append("Feeder ids must be unique")
            chars = []
            for key, answer, index in zip(arguments["feeder_ids"], arguments["answers"], arguments["indices"]):
                if isinstance(index, bool) or not 1 <= index <= len(answer):
                    issues.append(f"{key}: index outside the supplied answer's one-based character range")
                else:
                    chars.append(answer[index - 1])
            data["extraction"] = "".join(chars) if not issues else None
            candidate = data["extraction"] or ""
        elif kind == "robot":
            times = arguments["durations_seconds"]
            limit = arguments["run_limit_seconds"]
            if limit <= 0 or any(t < 0 for t in times):
                issues.append("Run limit must be positive and step durations non-negative")
            total = sum(Decimal(str(t)) for t in times)
            data.update(planned_seconds=str(total), supplied_limit_seconds=limit, physical_execution=False)
            if total > Decimal(str(limit)):
                issues.append("Planned sequence exceeds the supplied run limit")
        elif kind == "writing":
            warnings.append("Author and prompt ids are contestant-supplied; roster and provided-prompt membership are not authenticated")
            if len(arguments["authors"]) != 3:
                issues.append("The WSC packet requires exactly three responses")
            if len({s.strip() for s in arguments["authors"]}) != 3:
                issues.append("The three responses must have distinct authors")
            if len({s.strip() for s in arguments["prompt_ids"]}) != 3:
                issues.append("The three responses must answer distinct prompts")
            candidate = "\n\n".join(f"{author} — prompt {prompt}\n{response}"
                for author, prompt, response in zip(arguments["authors"], arguments["prompt_ids"], arguments["responses"]))
        elif kind == "sections":
            candidate = "\n\n".join(f"{key.replace('_', ' ').title()}\n{arguments[key].strip()}" for key in profile.fields)
            data["section_order"] = list(profile.fields)
            warnings.append("A structured outline is not a rendered final document or slide deck")
        else:
            raise ValueError(f"Unimplemented preparation kind: {kind}")
    return {
        "valid": True, "format_ok": not issues, "competition_id": profile.competition,
        "task_id": context.get("task_id"), "tool": action,
        "scope": "contestant_supplied_preparation", "correctness_checked": False,
        "submitted": False, "issues": issues, "warnings": warnings,
        "candidate_text": candidate if not issues else "", "data": data,
        "limitation": profile.limitation,
    }
