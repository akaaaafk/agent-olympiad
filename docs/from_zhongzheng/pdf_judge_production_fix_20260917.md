# Permanent PDF judge transport fix

The normal `run_mini_dataset.py` / `run_pipeline.py` path now includes the
fixes previously applied only through `repair_reviewed_pdf_judges.py`.
No repair script or additional CLI option is required for new runs.

- `src/artifacts/reviewed_pdf_text.py` binds the reviewed CCDC cover and CFA
  blank page to their exact PDF SHA-256 and page number. Other empty scanned
  pages still fail. Original PDF assets are not modified.
- `src/artifacts/pdf_ingest.py` uses these reviewed transcriptions only when
  the corresponding page has no extracted text.
- `src/llm.py` automatically prepares judge PDF text. CFA task excerpts are
  removed only when their non-whitespace characters exactly match a delivered
  original PDF page. The full packet remains; unmatched excerpts, instructions,
  submissions and rubric text remain. The long CFA PDF's whitespace is
  normalized; this is a text-only route, not a claim of visual comprehension.
- The Tinker Qwen/Qwen3.6-35B-A3B caller checks the actual tokenized prompt
  against the observed 65,536-token deployment limit, reserves 256 tokens,
  and reduces the requested output allowance to available space. It does not
  truncate input. If insufficient room remains, it fails before sampling.
  Effective output limits and PDF transport metadata are included in usage.
- Pipeline reports now reconcile cached `evaluation_pending` states only after
  validating the saved result's identity and completion envelope.

Existing processes retain imported code. New processes use the fix; existing
results keep their original identity and must not be relabeled as new-code runs.
Changing source hashes can cause an old output directory to fail reuse checks;
use a fresh timestamped output for new experiments. No completed contestants
were rerun to validate this patch. Existing CCDC/CFA repaired scores remain.

Regression coverage: real CCDC and CFA PDFs through the normal adapter,
unmatched-excerpt retention, contestant/judge separation, unknown empty-page
rejection, token budgeting before sampling, effective usage reporting, and
validated reconciliation of a repaired saved result. SDK sampling is mocked
for automated tests; the earlier successful paid evaluations were not repeated.
