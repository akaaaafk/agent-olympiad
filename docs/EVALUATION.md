# Evaluation strategy

The benchmark uses the simplest defensible evaluator for each deliverable type.
Scores from different evaluator versions are not treated as interchangeable.

## Evaluator registry

| Deliverable | Evaluator | Current status |
|---|---|---|
| Numerical answer sheet | Official gold / multipart deterministic grader | ARML pilot available; multipart grader still needs generalization |
| Proof or worked answer | Official marking scheme + structured LLM judge | Feasible after canonical score integration |
| Slide deck | Original task PDF + task-specific structured rubric + rendered-deck multimodal judge | `slide_deck_v1` MVP |
| Essay / report / memorial | Structured rubric judge | Later; requires domain-specific rubrics and calibration |
| Programming submission | Official tests in an isolated judge | Deferred until test data and sandbox exist |
| Physical lab task | Instrument observations + report rubric | Deferred; text-only simulation is not competition-faithful |
| Oral presentation / Q&A | Human or validated audiovisual protocol | Deferred; slides alone cannot measure delivery |

## Generic slide-deck evaluator v1

The evaluator receives:

1. the original task PDF;
2. a structured task-specific rubric;
3. the team's normalized submission PDF;
4. deterministic format checks.

Models may submit a self-contained HTML deck or a PDF. HTML is validated and
rendered to PDF before judging. The evaluator returns criterion-level JSON with
scores, visible slide evidence, justification, confidence, warnings, and
limitations. Oral delivery, timing, Q&A, and on-stage teamwork are explicitly
outside the score.

Run a complete PDF-first team experiment:

```bash
export OPENAI_API_KEY="..."
python3 src/run_presentation_artifact.py \
  --task-pdf path/to/task.pdf \
  --rubric path/to/rubric.json \
  --task-label "business case" \
  --rounds 3 \
  --agent-model gpt-4.1 \
  --judge-model gpt-4.1
```

Evaluate an existing HTML or PDF deck:

```bash
export OPENAI_API_KEY="..."
python3 src/evaluate_artifact.py path/to/slides.html \
  --task-pdf path/to/task.pdf \
  --rubric path/to/rubric.json \
  --model gpt-4.1
```

[`data/rubrics/business_case_slides_50.json`](../data/rubrics/business_case_slides_50.json)
is an example rubric for an IEO-like business case. It is not coupled to the
archived IEO experiment or to a benchmark ID.

## Human calibration protocol

Human calibration starts only after the evaluator passes schema, rendering, and
repeatability tests.

1. Select at least 12 anonymized decks spanning deliberately weak, medium, and
   strong quality.
2. Give every judge the same original case PDF, structured rubric, and written
   instruction that oral performance is not observable.
3. Obtain at least two independent human ratings per deck without showing AI
   scores or model identities.
4. Record criterion scores and cited slide evidence, not only a total.
5. Measure:
   - mean absolute error between AI and mean human score;
   - Spearman rank correlation;
   - criterion-level agreement;
   - human-human disagreement as the comparison ceiling.
6. Tune prompts on a calibration subset and report final agreement on a held-out
   subset.
7. Freeze evaluator, rubric, and prompt versions before benchmark reporting.

## Artifact safety

- Agent-visible and judge-only assets are separate.
- PDFs use repository-relative paths, checksums, and explicit page ranges.
- Missing assets or checksum mismatches fail the run.
- Official solutions must never be included in an agent-visible packet.
- Extracted text may support search/debugging, but it is not silently substituted
  for a missing source PDF in multimodal runs.
