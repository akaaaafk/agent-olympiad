# Controlled OTC comparisons

Use `vallina_otc` for the current-team-round-only condition and `otc` for the
memory-enabled condition. Both use the same OTC focus algorithm. The latter
can use permitted historical evidence; the former cannot retain previous-round
drafts, messages, reviews, or private thoughts. Audit files still preserve the
full run, and the environment retains submissions for final grading.

## Freeze the opening brief

Pass the **same** `--coach-brief-file` to both runs to remove independently
generated Coach advice as a source of variation. A generic, problem-blind ARML
example is [arml_shared_coach_brief.txt](../configs/experiments/arml_shared_coach_brief.txt).
Do not author the brief from evaluation answers or solution traces.

Add these arguments to each otherwise matched contest command:

```text
--coach-brief-file configs/experiments/arml_shared_coach_brief.txt
--temperature 0.2
--max-output-tokens 8192
```

Keep the manifest, model/provider, team size, turn budget, token budget, action
transport and grading policy identical. Use fresh run identities and output
directories. Record the input and source hashes before launching a pair.

The CLI reads UTF-8 text (with an optional BOM), trims outer whitespace, checks
the Coach character limit before making model calls, and binds the text into
the run identity. A provided brief makes zero Coach API calls and consumes zero
generated-output tokens. It is stored once at turn zero with a SHA-256 digest;
resuming with a different brief fails. Both conditions must use the provided
brief mode to keep this budget treatment equal.

Without this flag, each run still generates its own opening brief. That remains
a separate experimental condition. Do not compare a new shared-brief run against
an old generated-brief run as a memory-only ablation.

## Sampling and scheduling

For the CLI Perplexity Agent path, `--temperature` and `--max-output-tokens` now
reach the private-think request as well as the native-action path. Previously
the text-call factory ignored those CLI values. Verify actual recorded requests
when running live; matching command-line labels alone is insufficient.

OTC focus version 3 uses a common round-based tie-break rotation. Once blank
tasks have been considered, a rejected draft takes precedence over an unreviewed
peer draft. Two consecutive `speak`/`rest` visits to one task yield that focus
when another permitted task exists; intervening visible work, reviews or
deliberation evidence reset that streak. This changes suggested focus and does
not create reviews, approve answers, or relax action permissions. The strict
control applies this algorithm only to its permitted current-round view.

Old focus-version checkpoints are intentionally incompatible with version 3.
Preserve completed results and start fresh validation runs. These changes fix
comparison controls and task allocation; improved mathematical accuracy still
requires new paired live evidence.
