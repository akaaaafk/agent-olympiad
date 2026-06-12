"""
IEO Multi-Agent Business Case Experiment

5 agents collaborate on the IEO Business Case with no pre-assigned roles.
Each agent sees the full shared discussion history and contributes freely.
After 3 rounds of discussion, the team produces a final report which is scored
by an external judge on the 4 official IEO Business Case evaluation dimensions.

Key design choice: agents are NOT given roles. We want to observe whether
they self-organize, divide work, and produce emergent collaboration — or not.
That finding (whether emergent coordination happens) is itself the research result.

Usage:
  python3 run_multiagent_experiment.py <model> [judge_model]

  # Same model for all agents + external judge:
  python3 run_multiagent_experiment.py agent:openai/gpt-5.5 agent:openai/gpt-5.5
  python3 run_multiagent_experiment.py agent:anthropic/claude-sonnet-4-6 agent:openai/gpt-5.5

Set PERPLEXITY_API_KEY environment variable before running.
"""

import json
import os
import sys
import time
import requests

API_KEY = os.environ.get("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("Set PERPLEXITY_API_KEY environment variable")


def parse_model_arg(arg):
    """Returns (model_name, api_type) from a CLI argument."""
    if arg.startswith("agent:"):
        return arg[len("agent:"):], "agent"
    return arg, "sonar"


raw_agent = sys.argv[1] if len(sys.argv) > 1 else "agent:openai/gpt-5.5"
raw_judge = sys.argv[2] if len(sys.argv) > 2 else raw_agent

AGENT_MODEL, AGENT_API = parse_model_arg(raw_agent)
JUDGE_MODEL, JUDGE_API = parse_model_arg(raw_judge)

NUM_AGENTS = 5
NUM_ROUNDS = 3

print(f"Agent model : {AGENT_MODEL}")
print(f"Judge model : {JUDGE_MODEL}")
print(f"Agents      : {NUM_AGENTS}")
print(f"Rounds      : {NUM_ROUNDS}")

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


# ─── API helpers (same as run_experiment.py) ──────────────────────────────────

def call_sonar(model, system_prompt, user_prompt, max_retries=5):
    from openai import OpenAI, RateLimitError, APIStatusError
    client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")
    for attempt in range(max_retries):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user",   "content": user_prompt}]
            )
            return r.choices[0].message.content
        except (RateLimitError, APIStatusError):
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [retry {attempt+1}/{max_retries}, waiting {wait}s]")
                time.sleep(wait)
            else:
                raise


def call_agent(model, system_prompt, user_prompt, max_retries=5):
    full_input = f"{system_prompt}\n\n{user_prompt}"
    for attempt in range(max_retries):
        try:
            r = requests.post(
                "https://api.perplexity.ai/v1/agent",
                headers=HEADERS,
                json={"model": model, "input": full_input},
                timeout=180
            )
            r.raise_for_status()
            data = r.json()
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content["text"]
            return str(data)
        except requests.exceptions.HTTPError:
            if r.status_code == 429 and attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [429 retry {attempt+1}/{max_retries}, waiting {wait}s]")
                time.sleep(wait)
            else:
                raise


def generate(model, api, system_prompt, user_prompt):
    if api == "agent":
        return call_agent(model, system_prompt, user_prompt)
    else:
        return call_sonar(model, system_prompt, user_prompt)


# ─── Prompts ──────────────────────────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are one of 5 high school students competing in the International Economics Olympiad Business Case competition. You are working as a team to prepare a business case recommendation for a construction company.

You will see what your teammates have already written in the shared workspace. Read it carefully, then add your contribution. You can:
- Add analysis your team has not covered yet
- Challenge or refine something a teammate said, if you disagree
- Coordinate with your team (e.g. suggest who should handle what next)
- Propose a structure or approach for the final report

There are no assigned roles — figure out how to work together as a real team would.
Be concise but substantive. Do not repeat what teammates have already said."""


SYNTHESIS_SYSTEM_PROMPT = """You are one of 5 students on an IEO Business Case team. Your team has just finished discussing. Now write the final business case report that synthesizes your team's best thinking into one coherent document."""


JUDGE_SYSTEM_PROMPT = """You are an expert judge for the International Economics Olympiad Business Case competition. Score student teams fairly and strictly according to the official rubric."""


def build_discussion_history(messages):
    """Formats the list of agent messages into a readable shared workspace."""
    if not messages:
        return "(no messages yet — you are the first to contribute)"
    lines = []
    for msg in messages:
        lines.append(f"[Student {msg['agent_id']} — Round {msg['round']}]")
        lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines)


def build_agent_user_prompt(case_text, messages, round_num, agent_id):
    history = build_discussion_history(messages)
    return f"""=== BUSINESS CASE ===
{case_text}

=== TEAM DISCUSSION SO FAR ===
{history}

=== YOUR TURN ===
You are Student {agent_id}. This is Round {round_num} of {NUM_ROUNDS}.
What is your contribution to the team's analysis?"""


def build_synthesis_user_prompt(case_text, messages):
    history = build_discussion_history(messages)
    return f"""=== BUSINESS CASE ===
{case_text}

=== FULL TEAM DISCUSSION ===
{history}

=== FINAL REPORT ===
Based on everything your team has discussed, write the complete final business case report.
It must cover all five required deliverables:
1. Environmental analysis — opportunities and risks
2. Cost breakdown — design, construction, operating costs, insurance, interest
3. Capital composition — debt vs equity, cost of capital
4. Green building benefits — for occupants and wider society
5. Break-even analysis — if applicable
6. Final recommendation — apply at €94M / counter-propose a different amount / do not apply

Be thorough and precise. Use numbers where possible."""


def build_judge_user_prompt(case_text, final_report):
    return f"""=== BUSINESS CASE TASK ===
{case_text}

=== TEAM'S FINAL REPORT ===
{final_report}

=== SCORING INSTRUCTIONS ===
Score this report on 4 dimensions, each worth 25 points (total /100):

1. ANALYTICAL (25 pts)
   - Did the team identify the right problems and goals?
   - Did they synthesize information from multiple angles?
   - Did they consider different stakeholders?

2. CONCEPTUAL (25 pts)
   - Is the model of analysis sound and well-structured?
   - Are assumptions realistic and backed by evidence?
   - Is the recommendation complete and feasible?
   - Did they think creatively?

3. QUANTITATIVE (25 pts)
   - Are cost calculations precise and realistic?
   - Is the break-even analysis convincing?
   - Are financial projections backed by reasoning?

4. COMMUNICATION (25 pts)
   - Is the report well-structured and easy to follow?
   - Is the writing professional and clear?
   - Are all 5 required deliverables covered?

For each dimension: state the score (e.g. "ANALYTICAL: 18/25") and a 2-3 sentence justification.
End with: TOTAL: X/100"""


# ─── Load benchmark ───────────────────────────────────────────────────────────

with open("data/processed/ieo_benchmark.json") as f:
    all_problems = json.load(f)

business_cases = [p for p in all_problems if p["task_type"] == "business_case"]

if not business_cases:
    print("No business case problems found in benchmark. Exiting.")
    sys.exit(1)

all_results = []

for problem in business_cases:
    print(f"\n{'='*60}")
    print(f"Case: {problem['problem_id']} — {problem['topic']}")
    print(f"{'='*60}")

    case_text = problem["problem_description"]
    shared_messages = []   # grows as agents post

    # ── Rounds of discussion ──────────────────────────────────────────────────
    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"\n  --- Round {round_num} ---")
        for agent_id in range(1, NUM_AGENTS + 1):
            print(f"  Agent {agent_id} thinking...", end=" ", flush=True)
            user_prompt = build_agent_user_prompt(
                case_text, shared_messages, round_num, agent_id
            )
            response = generate(AGENT_MODEL, AGENT_API, AGENT_SYSTEM_PROMPT, user_prompt)
            shared_messages.append({
                "agent_id": agent_id,
                "round": round_num,
                "content": response
            })
            print(f"done ({len(response)} chars)")

    # ── Synthesis: one agent writes the final report ──────────────────────────
    print(f"\n  --- Final synthesis ---")
    synthesis_prompt = build_synthesis_user_prompt(case_text, shared_messages)
    final_report = generate(AGENT_MODEL, AGENT_API, SYNTHESIS_SYSTEM_PROMPT, synthesis_prompt)
    print(f"  Final report written ({len(final_report)} chars)")

    # ── Judge scores the final report ─────────────────────────────────────────
    print(f"  Judge scoring...", end=" ", flush=True)
    judge_prompt = build_judge_user_prompt(case_text, final_report)
    judge_feedback = generate(JUDGE_MODEL, JUDGE_API, JUDGE_SYSTEM_PROMPT, judge_prompt)
    print("done")

    all_results.append({
        "problem_id":     problem["problem_id"],
        "year":           problem["year"],
        "topic":          problem["topic"],
        "agent_model":    AGENT_MODEL,
        "judge_model":    JUDGE_MODEL,
        "num_agents":     NUM_AGENTS,
        "num_rounds":     NUM_ROUNDS,
        "discussion":     shared_messages,
        "final_report":   final_report,
        "judge_feedback": judge_feedback
    })

# ─── Save results ─────────────────────────────────────────────────────────────
safe_model = AGENT_MODEL.replace("/", "_").replace(".", "_")
safe_judge = JUDGE_MODEL.replace("/", "_").replace(".", "_")
output_path = f"data/processed/multiagent_{safe_model}_judgedby_{safe_judge}.json"

with open(output_path, "w") as f:
    json.dump(all_results, f, indent=2)

print(f"\n\nAll done! Results saved to {output_path}")

# ── Print score summary ───────────────────────────────────────────────────────
print("\n" + "="*60)
print(f"SCORE SUMMARY  |  Agents: {AGENT_MODEL}  |  Judge: {JUDGE_MODEL}")
print("="*60)
for r in all_results:
    lines = r["judge_feedback"].split("\n")
    score_line = next((l for l in reversed(lines) if "TOTAL:" in l), "TOTAL: ?")
    score = score_line.replace("**", "").replace("TOTAL:", "").strip()
    print(f"{r['problem_id']:<35} {score}")
