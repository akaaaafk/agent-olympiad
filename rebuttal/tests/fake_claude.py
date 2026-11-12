#!/usr/bin/env python3
"""Stand-in for the ``claude`` CLI used by offline tests (CLAUDE_CODE_BIN=this file).

Reads the prompt from stdin and answers like ``claude -p --output-format json``:
answer sheets get "0" everywhere, contest actions pick ``rest`` (or the first
action) with placeholder arguments, text calls get a short plan.
"""
import json
import sys

argv = sys.argv[1:]
sys.stdin.read()
schema = json.loads(argv[argv.index("--json-schema") + 1]) if "--json-schema" in argv else None
base = {"session_id": "fake-session-0001", "usage": {"input_tokens": 10, "output_tokens": 5},
        "total_cost_usd": 0.0, "num_turns": 1, "is_error": False, "result": ""}
if schema is None:
    base["result"] = '{"score": 0, "rationale": "fake"}'
elif "action" in schema["properties"]:
    variants = schema["properties"]["action"]["anyOf"]
    pick = next((v for v in variants if v["properties"]["name"]["const"] == "rest"), variants[0])
    params = pick["properties"]["arguments"]
    args = {k: ("ok" if params["properties"][k].get("type", "string") == "string" else 0)
            for k in params.get("required", [])}
    base["structured_output"] = {"action": {"name": pick["properties"]["name"]["const"], "arguments": args}}
else:
    tids = list(schema["properties"]["answers"]["properties"])
    out = {"answers": {t: "0" for t in tids}, "done": True}
    if "message" in schema["properties"]:
        out["message"] = "fake"
    base["structured_output"] = out
print(json.dumps(base))
