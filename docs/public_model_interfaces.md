# Additional model interfaces

These interfaces are additive. Existing `openai`, `perplexity`, `tinker`,
`openagents`, and `vectorengine` names and model defaults are retained.
Use your own provider key and an explicit model ID available to your account.
The contestant and judges continue to use the same provider. No model is
silently substituted; a separate judge model on that provider remains optional.

| `--provider` | API key environment variable | Interface | PDF input |
|---|---|---|---|
| `anthropic` | `ANTHROPIC_API_KEY` | Claude Messages | Native PDF and images |
| `gemini` | `GEMINI_API_KEY` | Gemini generateContent | Native PDF and images |
| `deepseek` | `DEEPSEEK_API_KEY` | Chat Completions | Extracted text |
| `openai_compatible` | `OPENAI_COMPATIBLE_API_KEY` | Chat Completions | Extracted text |

Native input support is model-dependent. Text-only PDF delivery does not read
diagrams or guarantee layout preservation. Unreviewed pages with no extracted
text fail explicitly. The generic interface requires a server/model supporting
Chat Completions and function calling; compatibility with every proxy is not
assumed. Existing OpenAI support remains available with `--provider openai`.

## Install and configure

From the code checkout, install the existing dependencies:

```shell
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` only if you do not already have a `.env`, then fill
in the relevant key. Do not replace existing settings. Native adapters use the
existing `requests` package; no additional SDK installation is required.

For a custom Chat Completions endpoint, configure:

```dotenv
OPENAI_COMPATIBLE_API_KEY=your-own-key
OPENAI_COMPATIBLE_BASE_URL=https://your-service.example/v1
```

Each new interface also accepts `--base-url`; this overrides only its own
endpoint. Include the API version prefix, not the final operation path:

- Anthropic: `https://api.anthropic.com/v1`
- Gemini: `https://generativelanguage.googleapis.com/v1beta`
- DeepSeek: `https://api.deepseek.com`
- Generic: the provider's documented Chat Completions prefix, often ending `/v1`

For keyless local servers, supply a nonempty placeholder key only if that server
accepts it. No key is borrowed from another provider. Use `--api-key-env MY_KEY`
to select a key from your shell; keys are inherited by child processes and not
written into run identities. Avoid putting real keys in shell command history.

## Check your endpoint first

Replace `YOUR_MODEL_ID` with the exact model you intend to run:

```shell
python scripts/check_provider.py --provider anthropic --model YOUR_MODEL_ID
python scripts/check_provider.py --provider gemini --model YOUR_MODEL_ID
python scripts/check_provider.py --provider deepseek --model YOUR_MODEL_ID
python scripts/check_provider.py --provider openai_compatible --model YOUR_MODEL_ID --base-url https://your-service.example/v1
```

This makes two small authenticated calls: a text response and a single function
call. It does not execute a competition. Provider calls may incur charges.
For PDF tasks, optionally add `--pdf path/to/example.pdf --pdf-expected-text HEADING`.
Only page 1 is sent. Without an expected marker the PDF check verifies transport,
not that the model accurately read the page. Use a page whose heading you know.

## Run the existing benchmark command

```shell
python scripts/run_mini_dataset.py all --provider anthropic --model YOUR_MODEL_ID --competitions arml_local --system-variant single_agent --output results/mini_anthropic_new
```

Change only `--provider`, `--model`, credentials, and output directory for another
service. Omit `--competitions arml_local` to select all mini tracks. The normal
readiness checks, external tool requirements, and baseline rules still apply.
Use a fresh output directory for a new experiment. An endpoint change is recorded
in the run identity and cannot be silently mixed into an earlier run.

## Call the interface from Python

From the code checkout:

```python
import sys
sys.path.insert(0, "src")
from env_config import load_repo_dotenv
from llm import LLMRequest, resolve_request_fn

load_repo_dotenv()
call = resolve_request_fn("gemini", "YOUR_MODEL_ID", max_output_tokens=1024)
response = call(LLMRequest("Answer concisely.", "Explain the task."))
print(response.text)
print(response.usage)
```

This is a model interface, not an HTTP benchmark server or a packaged benchmark
SDK. All adapters return the existing `LLMResponse` / `LLMToolCall` types.
Multiple calls are retained for the existing atomic action validator; partial
or blocked responses do not execute tool calls. Tool execution stays in the
existing contest engine. Native Gemini requests are fresh, reconstructed turns,
not an exposed multi-turn chat-history API.

Provider token-limit stop reasons are normalized to `finish_reason="length"`;
`provider_finish_reason` retains the original value. The contest action
controller can retry once within the remaining API/output budget. Refusals and
filtered responses do not trigger token-limit retries. A malformed tool batch
returns no calls and a `tool_error`, retaining returned usage so the engine can
record a failed action without crashing. Gemini output usage includes candidate
and thinking tokens, including responses reporting thinking tokens alone.

## Non-action query adapters

The contest engine preserves `query(system_prompt, user_prompt) -> str` for
custom legacy callbacks. Such callbacks have estimated visible-text token usage.
To support remaining-budget metadata and actual usage for Coach, private-think
and leader planning, attach the structured request interface:

```python
def query(system_prompt, user_prompt):
    return call(LLMRequest(system_prompt, user_prompt)).text

query.request = call  # LLMRequest -> LLMResponse
query.supports_budgeted_requests = True
query.max_output_tokens = 1024
```

The engine reserves the current call, then sends `max_transport_attempts`,
`max_transport_output_tokens` and `max_output_tokens_override` when constrained.
Your adapter must apply those limits before sampling and share them across its
internal retries. Return aggregate `api_calls` and `output_tokens` (or
`completion_tokens`), including generated reasoning and continuation tokens.
Unknown failed-attempt usage belongs in `unknown_usage_attempts`; an exception
can carry a `usage` dictionary with known counts. An explicit local zero-call
failure uses `api_calls=0, output_tokens=0`. Incomplete responses must signal
`tool_error` or `finish_reason="length"`; they are charged but not accepted as
completed thoughts. A reported overrun is recorded in full and stops the run.

`max_transport_output_tokens` is the remaining total across attempts, not a new
per-call limit. Apply the configured output limit to each request as well. The
engine records reported usage without clipping it to the requested budget.
Provider exceptions save a checkpoint after charging accumulated usage; resume
retries only the pending work with the remaining allowance. Local attachment
failures before sampling report zero calls. OpenAI Responses overall incomplete
status is rejected even when its output contains parseable text or a tool call.

These attributes are installed by the built-in live contest factories. They do
not alter the existing action registry or baseline definitions. The engine's
runtime event records whether non-action tokens were provider-reported or
estimated. Failed-request tokens may be unknown, so the runtime output budget
is not an exact account-billing statement.

## Validation and API references

Automated protocol tests mock API responses; they cover keys, endpoints, tools,
usage, selected PDF pages, truncation, and normal runner registration. They do
not establish live account access. Use `check_provider.py` with your own key
and model for that verification.

Request formats follow [Claude Messages](https://platform.claude.com/docs/en/api/messages/create),
[Claude PDF input](https://platform.claude.com/docs/en/build-with-claude/pdf-support),
[Gemini generateContent](https://ai.google.dev/api/generate-content), and
[Chat Completions](https://developers.openai.com/api/reference/resources/chat).
DeepSeek publishes its [Chat Completions interface](https://api-docs.deepseek.com/api/create-chat-completion/).
