"""
IEO Multi-Agent Business Case Experiment

5 agents collaborate on the IEO Business Case with no pre-assigned roles.
Each agent sees the full shared discussion history and contributes freely.
After 3 rounds of discussion, the team produces a final report which is scored
by an external judge on the 4 official IEO Business Case evaluation dimensions.

Key design choice: agents are NOT given roles. We observe whether they
self-organize, divide work, and produce emergent collaboration — or not.
That finding is itself a research result.

Usage:
  python3 run_multiagent_experiment.py <model> [judge_model] [format]

  format: "report" (default) or "slides"

  python3 run_multiagent_experiment.py agent:openai/gpt-5.5 agent:openai/gpt-5.5 slides
  python3 run_multiagent_experiment.py agent:google/gemini-3.5-flash agent:openai/gpt-5.5 slides

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
    if arg.startswith("agent:"):
        return arg[len("agent:"):], "agent"
    return arg, "sonar"


raw_agent = sys.argv[1] if len(sys.argv) > 1 else "agent:openai/gpt-5.5"
raw_judge = sys.argv[2] if len(sys.argv) > 2 else raw_agent
OUTPUT_FORMAT = sys.argv[3].lower() if len(sys.argv) > 3 else "report"
if OUTPUT_FORMAT not in ("report", "slides"):
    raise ValueError("Third argument must be 'report' or 'slides'")

AGENT_MODEL, AGENT_API = parse_model_arg(raw_agent)
JUDGE_MODEL, JUDGE_API = parse_model_arg(raw_judge)

NUM_AGENTS = 5
NUM_ROUNDS = 3

print(f"Agent model : {AGENT_MODEL}")
print(f"Judge model : {JUDGE_MODEL}")
print(f"Format      : {OUTPUT_FORMAT}")
print(f"Agents      : {NUM_AGENTS}")
print(f"Rounds      : {NUM_ROUNDS}")

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


# ─── API helpers ──────────────────────────────────────────────────────────────

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

AGENT_SYSTEM_PROMPT = """You are one of 5 high school students competing in the International Economics Olympiad Business Case competition. You are working as a team to prepare a strategic case presentation.

You will see what your teammates have already written in the shared workspace. Read it carefully, then add your contribution. You can:
- Add analysis your team has not covered yet
- Challenge or refine something a teammate said, if you disagree
- Coordinate with your team (e.g. suggest who should handle what next)
- Propose a structure or approach for the final presentation

There are no assigned roles — figure out how to work together as a real team would.
Be concise but substantive. Do not repeat what teammates have already said."""


SYNTHESIS_REPORT_PROMPT = """You are one of 5 students on an IEO Business Case team. Your team has just finished discussing. Now write the final strategic case report that synthesizes your team's best thinking into one coherent document."""

SYNTHESIS_SLIDES_PROMPT = """You are one of 5 students on an IEO Business Case team. Your team has just finished discussing. Now create the final presentation slide deck (as if for a 10-minute IEO Business Case oral presentation) that synthesizes your team's best thinking."""

JUDGE_SYSTEM_PROMPT = """You are an expert judge for the International Economics Olympiad Business Case competition. Score student teams fairly and strictly according to the official rubric."""


def build_discussion_history(messages):
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


def build_synthesis_user_prompt(case_text, messages, output_format):
    history = build_discussion_history(messages)
    if output_format == "slides":
        return f"""=== BUSINESS CASE ===
{case_text}

=== FULL TEAM DISCUSSION ===
{history}

=== FINAL SLIDE DECK ===
Based on everything your team discussed, create a complete presentation slide deck.

Requirements (matching real IEO Business Case format):
- 10–15 slides total
- Each slide must use this exact format:

--- Slide N: [Title] ---
• Bullet point (max 5 bullets per slide, concise)
• ...
Speaker notes: [1-3 sentences the presenter would say aloud for this slide]

Cover all required areas:
1. Executive summary / recommendation
2. Economic and logistical viability
3. Regional and global trade impact
4. Environmental, legal, and technical considerations
5. Financing and stakeholder management
6. Alternative solutions
7. Conclusion and next steps

Use numbers and real-world comparisons where possible. Keep slides presentation-ready, not essay-like."""

    return f"""=== BUSINESS CASE ===
{case_text}

=== FULL TEAM DISCUSSION ===
{history}

=== FINAL REPORT ===
Based on everything your team discussed, write the complete final strategic case report.
It must cover all required deliverables:
1. Executive summary
2. Structured analysis (economic viability, trade impact, environmental/legal, financing/stakeholders, alternatives)
3. Economic models or trade flow analysis where applicable
4. Recommendations and conclusion

Be thorough and precise. Use numbers and real-world comparisons where possible."""


def build_judge_user_prompt(case_text, rubric, final_output, output_format):
    deliverable_label = "SLIDE DECK" if output_format == "slides" else "FINAL REPORT"
    deliverable_note = (
        "Score the slide deck as submitted for a 10-minute oral presentation. "
        "You cannot evaluate live delivery or Q&A, but evaluate clarity, structure, "
        "professionalism, and whether the deck supports the team's recommendations."
        if output_format == "slides"
        else "Score the written report."
    )
    return f"""=== BUSINESS CASE TASK ===
{case_text}

=== OFFICIAL EVALUATION RUBRIC ===
{rubric}

=== TEAM'S {deliverable_label} ===
{final_output}

=== SCORING INSTRUCTIONS ===
{deliverable_note}
Score strictly on the 4 official dimensions from the rubric above.
The total is out of 50 points. Allocate points across the 4 dimensions as you see fit
based on their relative weight in the rubric.

For each dimension: state the score and a 2-3 sentence justification.
End with: TOTAL: X/50"""


# ─── Load benchmark ───────────────────────────────────────────────────────────

with open("data/processed/ieo_benchmark.json") as f:
    all_problems = json.load(f)

business_cases = [p for p in all_problems if p["task_type"] == "business_case"]

if not business_cases:
    print("No business case problems found in benchmark. Exiting.")
    sys.exit(1)

print(f"\nFound {len(business_cases)} business case(s) to run.")

all_results = []

for problem in business_cases:
    print(f"\n{'='*60}")
    print(f"Case: {problem['problem_id']} — {problem['topic']}")
    print(f"{'='*60}")

    case_text = problem["problem_description"]
    rubric = problem["gold_label"]["grading_rubric"]
    shared_messages = []

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

    # ── Synthesis ─────────────────────────────────────────────────────────────
    print(f"\n  --- Final synthesis ({OUTPUT_FORMAT}) ---")
    synthesis_prompt = build_synthesis_user_prompt(case_text, shared_messages, OUTPUT_FORMAT)
    synthesis_system = SYNTHESIS_SLIDES_PROMPT if OUTPUT_FORMAT == "slides" else SYNTHESIS_REPORT_PROMPT
    final_output = generate(AGENT_MODEL, AGENT_API, synthesis_system, synthesis_prompt)
    print(f"  Final {OUTPUT_FORMAT} written ({len(final_output)} chars)")

    # ── Judge ─────────────────────────────────────────────────────────────────
    print(f"  Judge scoring...", end=" ", flush=True)
    judge_prompt = build_judge_user_prompt(case_text, rubric, final_output, OUTPUT_FORMAT)
    judge_feedback = generate(JUDGE_MODEL, JUDGE_API, JUDGE_SYSTEM_PROMPT, judge_prompt)
    print("done")

    result = {
        "problem_id":     problem["problem_id"],
        "year":           problem["year"],
        "topic":          problem["topic"],
        "agent_model":    AGENT_MODEL,
        "judge_model":    JUDGE_MODEL,
        "output_format":  OUTPUT_FORMAT,
        "num_agents":     NUM_AGENTS,
        "num_rounds":     NUM_ROUNDS,
        "discussion":     shared_messages,
        "judge_feedback": judge_feedback
    }
    if OUTPUT_FORMAT == "slides":
        result["final_slides"] = final_output
    else:
        result["final_report"] = final_output
    all_results.append(result)

# ─── Save results ─────────────────────────────────────────────────────────────
safe_model = AGENT_MODEL.replace("/", "_").replace(".", "_")
safe_judge = JUDGE_MODEL.replace("/", "_").replace(".", "_")
format_suffix = f"_{OUTPUT_FORMAT}" if OUTPUT_FORMAT != "report" else ""
output_path = f"data/processed/multiagent{format_suffix}_{safe_model}_judgedby_{safe_judge}.json"
md_path = output_path.replace(".json", ".md")

with open(output_path, "w") as f:
    json.dump(all_results, f, indent=2)

with open(md_path, "w") as f:
    for r in all_results:
        f.write(f"# {r['problem_id']} — {r['topic']}\n\n")
        f.write(f"**Agents:** {r['agent_model']}  \n")
        f.write(f"**Judge:** {r['judge_model']}  \n")
        f.write(f"**Format:** {r['output_format']}  \n\n")
        f.write("## Score\n\n")
        f.write(r["judge_feedback"] + "\n\n")
        f.write("---\n\n")
        content = r.get("final_slides") or r.get("final_report", "")
        label = "Slides" if r["output_format"] == "slides" else "Report"
        f.write(f"## {label}\n\n{content}\n")

print(f"\n\nAll done! Results saved to {output_path}")
print(f"Readable version: {md_path}")

print("\n" + "="*60)
print(f"SCORE SUMMARY  |  Agents: {AGENT_MODEL}  |  Judge: {JUDGE_MODEL}")
print("="*60)
for r in all_results:
    lines = r["judge_feedback"].split("\n")
    score_line = next((l for l in reversed(lines) if "TOTAL:" in l), "TOTAL: ?")
    score = score_line.replace("**", "").replace("TOTAL:", "").strip()
    print(f"{r['problem_id']:<35} {score}")
