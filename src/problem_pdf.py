"""Contestant PDF reader. Only hash-bound, explicitly reviewed pages are exposed.

The registry is host configuration, never an agent-supplied path. Rendering sends
pixels only: annotations, hidden text, embedded files and PDF links are not sent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from contextlib import contextmanager
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
from dataset_paths import data_root
REGISTRY = data_root() / "problem_pdf_allowlist.json"
MAX_PAGES = 2


class ProblemPdfError(ValueError):
    pass


def approved_assets(row, *, root=None, registry=None):
    root = Path(root or ROOT).resolve()
    registry = Path(registry or REGISTRY)
    if not registry.is_file():
        return []
    entries = json.loads(registry.read_text(encoding="utf-8"))["assets"]
    assets = row.get("assets") or []
    forbidden = {a.get("sha256") for a in assets if a.get("role") == "judge_only"}
    accepted = []
    for entry in entries:
        if entry.get("problem_id") != row.get("problem_id"):
            continue
        if entry.get("review_status") != "approved_problem_only" or not entry.get("review_evidence"):
            continue
        match = next((a for a in assets if a.get("path") == entry.get("path")
                      and a.get("sha256") == entry.get("sha256")
                      and a.get("role") == "agent_visible"
                      and a.get("mime_type") == "application/pdf"), None)
        if not match or entry.get("sha256") in forbidden:
            continue
        path = (root / entry["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            continue
        pages = entry.get("pages") or []
        if not pages or any(type(p) is not int or p < 1 for p in pages):
            continue
        lower = match.get("page_start") or 1
        upper = match.get("page_end")
        if any(p < lower or (upper is not None and p > upper) for p in pages):
            continue
        accepted.append({**entry, "resolved_path": path})
    return accepted


def describe(row):
    return [{"document": i + 1, "pages": a["pages"]}
            for i, a in enumerate(approved_assets(row))]


def read_problem_pdf(row, pages=None, document=1, *, root=None, registry=None, render=True):
    assets = approved_assets(row, root=root, registry=registry)
    if type(document) is not int or document < 1 or document > len(assets):
        raise ProblemPdfError("No approved problem PDF for this document. Unreviewed and judge material is unavailable.")
    asset = assets[document - 1]
    selected = asset["pages"][:MAX_PAGES] if pages is None else pages
    if (not isinstance(selected, (list, tuple)) or not 1 <= len(selected) <= MAX_PAGES
            or any(type(p) is not int or p not in asset["pages"] for p in selected)
            or len(set(selected)) != len(selected)):
        raise ProblemPdfError("Request one or two distinct approved page numbers.")
    payload = {"status": "ok", "problem_id": row["problem_id"],
               "document": document, "pages": list(selected),
               "available_pages": asset["pages"], "sha256": asset["sha256"],
               "delivery": "Page images are attached to your next action request. Read additional pages explicitly."}
    if not render:
        return payload, ()
    import pymupdf
    from llm import LLMAttachment
    attachments = []
    # Unique private output directory avoids following agent-created cache files.
    out = Path(tempfile.mkdtemp(prefix="contest-problem-pages-"))
    pdf_bytes = asset["resolved_path"].read_bytes()
    if hashlib.sha256(pdf_bytes).hexdigest() != asset["sha256"]:
        out.rmdir()
        raise ProblemPdfError("Problem PDF changed before rendering.")
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        if any(p > len(pdf) for p in selected):
            raise ProblemPdfError("Reviewed page range is invalid.")
        for number in selected:
            image = out / f"page-{number}.png"
            pdf[number - 1].get_pixmap(dpi=120, annots=False).save(image)
            attachments.append(LLMAttachment(image, "image/png"))
    return payload, tuple(attachments)


def access_identity(manifest):
    """Freeze reviewed scope in run identity so resume cannot change access."""
    ids = {t.parent_problem_id for t in manifest.tasks}
    if not REGISTRY.is_file():
        return []
    return [a for a in json.loads(REGISTRY.read_text(encoding="utf-8"))["assets"]
            if a.get("problem_id") in ids]


def visible_benchmark(manifest, session, task):
    """Do not expose a whole packet if some of its split tasks are unreleased.

    Subset-only experiments also require their own separately reviewed packet.
    """
    if task.question_id is not None:
        visible = {t.task_id for t in session.visible_tasks}
        released = {t.question_id for t in manifest.tasks
                    if t.parent_problem_id == task.parent_problem_id and t.task_id in visible}
        required = {str(p["id"]) for p in (task.benchmark.get("gold_label") or {}).get("parts", [])}
        if not required or not required <= released:
            return {"problem_id": task.parent_problem_id, "assets": []}
    return task.benchmark


def latest_read(manifest, session, memory, agent):
    visible = {t.task_id for t in session.visible_tasks}
    tasks = {t.task_id: t for t in manifest.tasks}
    for event in reversed(memory.view(agent)):
        if event.kind == "read_problem_pdf_result" and event.task_id in visible:
            if event.payload.get("status") == "ok":
                return tasks[event.task_id], event.payload
            return None
    return None


def request_attachments(manifest, session, memory, agent):
    latest = latest_read(manifest, session, memory, agent)
    if latest is None:
        return ()
    task, payload = latest
    # Revalidate host registry and file hash on every model request, including resume.
    result, attachments = read_problem_pdf(visible_benchmark(manifest, session, task), payload["pages"], payload["document"])
    if result["sha256"] != payload["sha256"]:
        raise ProblemPdfError("Problem PDF changed since the read request.")
    return attachments


@contextmanager
def attached_request(request, manifest, session, memory, agent, *, text_only=False):
    if text_only:
        latest = latest_read(manifest, session, memory, agent)
        if latest is None:
            yield request
            return
        task, payload = latest
        row = visible_benchmark(manifest, session, task)
        result, _ = read_problem_pdf(row, payload["pages"], payload["document"], render=False)
        if result["sha256"] != payload["sha256"]:
            raise ProblemPdfError("Problem PDF changed since the read request.")
        asset = approved_assets(row)[payload["document"] - 1]
        from llm import LLMAttachment, pdf_text_request
        pages = tuple(LLMAttachment(asset["resolved_path"], "application/pdf",
                      page_start=p, page_end=p) for p in payload["pages"])
        yield pdf_text_request(replace(request, attachments=request.attachments + pages))
        return
    attachments = request_attachments(manifest, session, memory, agent)
    try:
        yield replace(request, attachments=request.attachments + attachments)
    finally:
        for attachment in attachments:
            attachment.path.unlink(missing_ok=True)
        if attachments:
            attachments[0].path.parent.rmdir()


def prompt_context(manifest, session, memory, agent):
    tasks = {t.task_id: t for t in manifest.tasks}
    available = {t.task_id: describe(visible_benchmark(manifest, session, tasks[t.task_id])) for t in session.visible_tasks}
    available = {k: v for k, v in available.items() if v}
    latest = latest_read(manifest, session, memory, agent)
    if not available and latest is None:
        return ""
    return ("\nPROBLEM PDF READING\nIf the JSON statement is missing, incomplete, or has unclear formulas/diagrams, "
            "use read_problem_pdf(problem_id, pages, document). Page numbers are 1-based; at most two per call. "
            "Only the reviewed pages listed here can be read.\n"
            + json.dumps({"available": available, "last_read": latest[1] if latest else None}) + "\n")
