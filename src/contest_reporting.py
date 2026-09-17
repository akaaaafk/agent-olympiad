"""Flat contest metrics with explicit missing values and separate judge usage."""
import csv
import json
import math
import os
import tempfile
import time
from pathlib import Path


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def report_row(result):
    grade = result.get("grade") or {}
    budget = result.get("budget") or {}
    metrics = result.get("metrics") or {}
    settings = (result.get("run_identity") or {}).get("settings") or {}
    config = settings.get("config") or {}
    evaluation = settings.get("evaluation") or {}
    stage = (result.get("evaluation_stages") or {}).get("coordination") or {}
    reasons = {}

    def number(name, value, reason):
        if finite(value):
            return value
        reasons[name] = reason
        return "N/A"

    row = {"model": (settings.get('execution') or {}).get('model', 'N/A'),
           "system_variant": result.get("system_variant", "N/A"),
           "rule_card_mode": (result.get("baseline") or config.get("baseline") or {}).get("rule_card", "N/A"),
           "rule_card_hash": config.get("rule_card_hash") or "N/A"}
    for key in ("score", "max_score"):
        row[key] = number(key, grade.get(key), "grading_unavailable")
    score, maximum = grade.get("score"), grade.get("max_score")
    row["accuracy"] = number("accuracy", score / maximum if finite(score) and finite(maximum) and maximum > 0 else None,
                             "score_or_positive_max_score_unavailable")
    unavailable = stage.get("error") or ("judge_disabled" if not evaluation.get("judge_collab") else "judge_incomplete")
    single_agent = result.get("system_variant") == "single_agent"
    if single_agent:
        unavailable = "not_applicable_single_agent"
    for label, key in (("Communication", "communication_score"), ("Planning", "planning_score")):
        value = metrics.get(key) if stage.get("status") != "failed" and not single_agent else None
        row[label] = number(label, value, unavailable)
    row["CS"] = number("CS", (row["Communication"] + row["Planning"]) / 2
                       if finite(row["Communication"]) and finite(row["Planning"]) else None, unavailable)
    for label, key in (("turns", "turns_used"), ("api_calls", "api_calls_used"), ("tokens", "tokens_used"), ("sec", "wall_seconds_used")):
        row[label] = number(label, budget.get(key), "runtime_usage_unavailable")
    provider = (settings.get("execution") or {}).get("provider")
    row["tokens_basis"] = "estimated_output_text_length" if provider == "tinker" else "runtime_output_token_budget"
    usage = result.get("evaluation_usage")
    disabled = not evaluation.get("judge_collab") and not evaluation.get("judge_cce")
    for label, key in (("eval_api_calls", "api_calls"), ("eval_tokens", "output_tokens"), ("eval_sec", "sec")):
        row[label] = number(label, usage.get(key) if usage else 0 if disabled else None, "evaluation_usage_not_recorded")
    row["eval_tokens_basis"] = "estimated_output_text_length" if evaluation.get("provider") == "tinker" else "provider_reported_output_tokens"
    if usage and usage.get("unmetered_calls"):
        row["eval_tokens"] = "N/A"
        reasons["eval_tokens"] = "partial_usage: provider_call_failed_or_usage_missing"
    row["missing_reasons"] = json.dumps(reasons, ensure_ascii=True, sort_keys=True)
    return row


REPORT_FIELDS = tuple(report_row({}))


def metered_judge(request_fn, result):
    def call(request):
        usage = result.setdefault("evaluation_usage", {"api_calls": 0, "output_tokens": 0, "sec": 0.0, "unmetered_calls": 0})
        started = time.monotonic()
        usage["api_calls"] += 1
        try:
            response = request_fn(request)
            reported = response.usage or {}
            usage["api_calls"] += max(0, int(reported.get("api_calls", 1)) - 1)
            tokens = reported.get("output_tokens", reported.get("completion_tokens"))
            if finite(tokens):
                usage["output_tokens"] += tokens
            else:
                usage["unmetered_calls"] += 1
            return response
        except Exception:
            usage["unmetered_calls"] += 1
            raise
        finally:
            usage["sec"] += time.monotonic() - started
    return call


def write_report(directory, result):
    row = report_row(result)
    path = Path(directory) / "contest_summary.csv"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=directory, delete=False) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow(row)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return row
