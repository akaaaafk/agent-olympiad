"""Publish the verified active-catalog snapshot and its unresolved review queue."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_data_catalog import Store
from scripts.repair_catalog_glyphs_20260913 import verify
from scripts.repair_iol_sources_20260913 import read, sha, require

REPORT = "data/benchmarks/all_data_audit_20260913.json"
TESTS = [
    "tests.test_catalog_glyph_repair", "tests.test_iol_source_repair",
    "tests.test_iol_followup_repair", "tests.test_iol_emoji_repair",
    "tests.test_iol_lao_repair", "tests.test_ijso_2005_packet_repair",
    "tests.test_ijso_answerless_exclusion", "tests.test_mystery_hunt_source_repair",
    "tests.test_mystery_hunt_exclusion", "tests.test_dataset_integrity_repair",
]
REVIEW = {
    "iiot/iiot_2021_05": "Example scheduling diagram was flattened into numbers and control characters; reconstruct against the complete source page, preserving task IDs, durations and dependency edges.",
    "eoes/eoes_EOES2025_Task1_TaskSheet-final": "Chemical and mathematical font mappings are corrupted; page-by-page equation transcription and visual verification required.",
    "eoes/eoes_EOES2025_Task2_TaskSheet_final": "Chemical and mathematical font mappings are corrupted; page-by-page equation transcription and visual verification required.",
    "eoes/eoes_EUSO_I_2004_TaskB": "Eight apparent page-number glyphs require source-page verification before replacement.",
    "eoes/eoes_TEST2 final version English": "Five apparent list bullets and three assistant-direction symbols require source-page verification.",
    "eoes/eoes_P1Tasks": "One nonprinting glyph occurs between 24 and h; source-page verification is still required.",
    "eoes/eoes_additionalfileschallenge1": "Extensive font/padding corruption in the additional-material preview; re-extract and visually compare rather than blanket stripping.",
    "odyssey_of_the_mind/odyssey_of_the_mind_spontaneous_examples_page": "One apparent bullet remains in the Last Straw example; verify its original source rather than changing the archived Markdown source.",
}


def main():
    require(not (ROOT/REPORT).exists(), "Published snapshot already exists")
    before = read(ROOT/"data/.cache/all_data_audit_20260913/before.json")
    after = read(ROOT/"data/.cache/all_data_audit_20260913/after.json")
    repair = read(ROOT/"data/benchmarks/catalog_glyph_repair_20260913.json")
    require(not after["issues"], "Unresolved structural audit errors")
    for path, digest in after["source_snapshot"].items():
        require(sha(ROOT/path) == digest, "Canonical data changed after audit: "+path)
    for key in ("active_tracks", "active_records", "status_counts", "split_counts", "license_counts"):
        require(before[key] == after[key], "Unexpected membership/readiness/metadata change")
    validation = verify(read(ROOT/"data/.cache/catalog_glyph_repair_20260913/plan.json"))
    manifest = read(ROOT/repair["backup"]/"manifest.json")
    for change in manifest["changed_files"]:
        require(sha(ROOT/change["path"]) == change["after_sha256"], "Repair post-hash mismatch")
        if change["before_sha256"]:
            require(sha(ROOT/repair["backup"]/change["path"]) == change["before_sha256"], "Backup hash mismatch")
    result = subprocess.run([sys.executable, "-m", "unittest", *TESTS, "-q"], cwd=ROOT,
                            text=True, capture_output=True)
    require(result.returncode == 0 and "Ran 100 tests" in result.stderr and "\nOK" in result.stderr,
            "Regression suite failed or test count changed: "+result.stdout+result.stderr)
    pending = [v for v in after["review_candidates"] if v["kind"] == "prompt_control_characters"]
    require({v["task"] for v in pending} == set(REVIEW), "Review queue changed")
    data = deepcopy(after)
    data.update(
        outcome="structural_checks_passed_with_explicit_semantic_and_readiness_backlog",
        repair_report="data/benchmarks/catalog_glyph_repair_20260913.json",
        repair_validation=validation,
        regression=dict(tests=100, result="passed", modules=TESTS, output=result.stderr),
        repair_manifest_verified=dict(path=repair["backup"]+"/manifest.json", files=len(manifest["changed_files"]),
                                      backed_up_files=sum(bool(c["before_sha256"]) for c in manifest["changed_files"])),
        prompt_review_queue=[dict(v, next_check=REVIEW[v["task"]]) for v in pending],
        duplicate_byte_review=dict(records=9, disposition="retained",
            finding="The identified overlaps are challenge input files copied into judge solution trees, not grounds for automatic deletion.",
            limitation="This byte-overlap review does not establish the absence of semantic answer leakage throughout all assets."),
        not_ready_counts={t["id"]:t["statuses"]["not_ready"] for t in after["tracks"] if t["statuses"].get("not_ready")},
        interpretation_limits=[
            "All 43 active tracks were structurally audited; inactive raw archives and historical results were not globally re-audited.",
            "Header validation checks PDF format, not page completeness, edition correctness, or readability of every page.",
            "Scorecard equality establishes configuration synchronization, not universally correct official score weights or gold answers.",
            "The C0 control-character scan does not detect every corrupted glyph, flattened equation, diagram or partial text preview.",
            "Readiness counts are catalog labels, not a claim that all ready tasks passed end-to-end execution in this audit.",
            "No programs, services, robots, paid model experiments or contest judges were executed.",
            "An unknown official total may be legitimate for a question-level evaluation unit; no official weights were invented.",
            "No split assignments or redistribution rights were invented. Cross-split near-duplicate contamination and licensing remain separate audits.",
        ],
    )
    store = Store(ROOT)
    store.save(REPORT, data)
    store.finish(dict(operation="publish_all_data_health_snapshot", report=REPORT))
    require(read(ROOT/REPORT) == data, "Published report readback mismatch")
    print(json.dumps(dict(report=REPORT, tracks=data["active_tracks"], records=data["active_records"],
        issues=data["issue_counts"], prompt_review_pending=len(pending), regression_tests=100,
        repair_backup=repair["backup"], manifest_files_verified=len(manifest["changed_files"])), indent=2))


if __name__ == "__main__":
    main()
