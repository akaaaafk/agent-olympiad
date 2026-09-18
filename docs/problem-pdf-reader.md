# Original problem PDF reader

Implemented 2026-09-15 in the contest-session runtime. The action-set version is 11.

## Agent interface

`read_problem_pdf(problem_id, pages=[1, 2], document=1)` reads at most two
reviewed pages per action. Page numbers and document numbers start at 1.
The prompt lists available documents/pages. The next request by the same agent
receives PNG images, and keeps those pages available until its next read.
For Tinker, the same action delivers extracted text from the requested approved
pages, with page labels and no image attachments. This uses `supports_pdf_text`,
separate from vision support. Blank/scanned pages without extractable text fail
explicitly; equations, diagrams and layout may be lost. Page, role and hash
restrictions still apply. Other providers keep the existing image delivery.
The read does not select a task, change an answer, or count as an independent review.
The action costs one ordinary turn and is common to all baselines.

Agents can use this when JSON is absent, truncated or loses formulas/diagrams.
When an entire approved packet cannot be split from JSON, manifest loading can
create question-specific reading instructions instead of refusing the packet.
Question IDs and scoring still come from the existing catalog; no answers enter
those instructions. A subset of a split packet or unreleased questions cannot
expose the whole packet. Prepare a separately reviewed subset first.

## Enforced access boundary

- `data/problem_pdf_allowlist.json` is host-controlled, keyed by parent problem
  ID, exact asset path, SHA-256 and reviewed page numbers. Agent arguments never
  include paths, URLs, roles or approval flags.
- An entry must match an existing `agent_visible` PDF asset and explicit review
  evidence. Unknown/unreviewed assets, judge-only assets, changed hashes,
  out-of-root paths and unapproved pages are denied.
- The image renderer reads hash-checked bytes and sends pixels only, with PDF
  annotations disabled. It never sends the original mixed PDF, hidden text,
  embedded attachments or navigable links to the agent. Tinker's explicit text
  route extracts the selected approved pages instead of rendering them; it
  does not forward the binary PDF, annotations or embedded attachments.
- `LLMRequest` rejects judge-only attachments for contestant/coach/action
  requests across providers. Only explicit evaluator purposes may use them.
- Results are private to the requesting seat. Pages are checked again on each
  model request. Temporary images are deleted after the provider returns.
- Run identity records the applicable allowlist entries, so changing access
  invalidates reuse of an existing experiment output.
- The legacy text-only environment does not advertise this action. Text-only
  providers without an explicit PDF-text route are filtered out. A live image model must actually support image
  input; mocked transport tests do not establish a particular model's vision quality.

Official examples, sample I/O and public scoring instructions printed as part
of a problem are contestant material. Answer keys, worked solutions to the
scored task and judge-only marking materials are not. A mixed page requires a
separately inspected clean asset before approval. The heading scanner cannot
make that decision automatically.

## Initially reviewed scope

All pages of these four original problem files were visually inspected:

| Problem | Approved pages |
|---|---|
| arml_local_2009 | 1-2 |
| purple_comet_hs_2005 | 1-6 |
| hmmt_guts_2000 | 1-8 |
| iiot_2017_01 | 1-2 |

This is 18 pages, not approval of the entire library. Other assets stay closed
until their content and page boundaries are reviewed. Adding a record to the
allowlist does not change its evaluator readiness.

## Audit and verification

## Tinker document contests

`src/run_otc_artifact.py --provider tinker --judge-provider tinker` supports
document contests such as MCM. Task PDFs and rendered report PDFs are extracted
to text by the Tinker adapter, including on emulated action retries. The host
task mapping rejects judge-only PDFs as contestant tasks. Judge-only references
remain restricted to evaluator requests. Reports are still compiled/rendered,
versioned, submitted and scored through the shared artifact pipeline.

The run identity records `task_delivery=extracted_text_v1` and the emulated
action transport. `task_extracted.txt` and `task_delivery.json` preserve the
exact task text, page range and hashes used by a run. Scoring remains a rubric
LLM proxy. This is a text-reading experiment and does not evaluate vision.

Prepare the current MCM queue with
`python scripts/run_qwen_mcm_pdftext_20260916.py prepare`, then run the same
script without `prepare`. It uses the current checkout and a fresh output root;
the earlier `run_qwen_mcm_textonly_20260916.py` snapshot script is not used.

## Original audit and verification

Run `python scripts/audit_problem_pdf.py` from the repository root. It writes
`output/problem_pdf_audit/audit.json` and `audit.md`, including per-record
limitations, file/hash/page checks and candidate answer headings. It does not
modify canonical or derived datasets, access the network, run a paid experiment,
or execute evaluators.

The 2026-09-15 audit covers 43 tracks / 1,720 records. There are 493 contestant
PDF assets across 451 records, with no missing/hash/page/parse errors found.
Four assets are approved; 489 assets across the remaining 447 PDF-bearing
records still require content review. 107 assets trigger a deliberately broad
heading heuristic. Some checked flags are ordinary mathematical uses of
"solutions", chemical solutions or blank answer sheets, so these are not 107
confirmed leaks.

110 records have fewer than 80 characters of JSON statement; 109 of those have
no contestant PDF. This is a triage heuristic, not proof that all are invalid.
The distribution is NYU CTF 91, Cybench 9, Science Bowl 7, DebateBench 2 and
Mystery Hunt 1. The one with a PDF is `nyu_ctf_2015f-for-mandiant` (76 pages,
unreviewed). The 1,269 records without a PDF are not inherently broken if their
text/assets suffice.

706 records remain `not_ready`: Mystery Hunt 247, NYU CTF 194, Odyssey 50,
Cybench 39, DebateBench 32, IIOT 31, EOES 30, WRO 20, CFA 19, CCDC 16,
IOL 9, GCCH 7, IJSO 4, Wharton 4, IOAI 2, ARML Power 1, Science Olympiad 1.
Their existing per-record limitations are retained in the audit.

160 focused tests passed; results are saved in `output/problem_pdf_audit/tests.json`
and `tests.txt`. They cover page/path/role/hash rejection, private image delivery,
the real contest action loop with a mocked model, missing-JSON manifest fallback,
baseline action resolution, native provider serialization and action transport.
No paid model or judge was called. Two additional Docker execution/isolation
tests could not run because the Docker Desktop Linux engine was not running;
the missing-backend test verifies that code does not fall back to host execution.
