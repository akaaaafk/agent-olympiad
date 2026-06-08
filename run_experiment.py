"""
IEO Agentic Benchmark — Experiment Runner

Supports two Perplexity APIs:
  Sonar API  (default): sonar, sonar-pro, sonar-reasoning-pro
  Agent API  (prefix model with "agent:"): openai/gpt-5.5, anthropic/claude-sonnet-4-6, etc.

Usage:
  python3 run_experiment.py                          # default: sonar-pro
  python3 run_experiment.py sonar-pro                # Sonar API
  python3 run_experiment.py agent:openai/gpt-5.5    # Agent API with GPT-5.5
  python3 run_experiment.py agent:anthropic/claude-sonnet-4-6

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

raw_model = sys.argv[1] if len(sys.argv) > 1 else "sonar-pro"

# Route to Agent API if model prefixed with "agent:"
if raw_model.startswith("agent:"):
    MODEL = raw_model[len("agent:"):]
    API = "agent"
else:
    MODEL = raw_model
    API = "sonar"

print(f"Model: {MODEL}  |  API: {API}")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def call_sonar(system_prompt, user_prompt, max_retries=5):
    """Sonar (Chat Completions) API — supports sonar, sonar-pro, sonar-reasoning-pro."""
    from openai import OpenAI, RateLimitError, APIStatusError
    client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")
    for attempt in range(max_retries):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_prompt}]
            )
            return r.choices[0].message.content
        except (RateLimitError, APIStatusError) as e:
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [retry {attempt+1}/{max_retries}, waiting {wait}s]")
                time.sleep(wait)
            else:
                raise


def call_agent(system_prompt, user_prompt, max_retries=5):
    """Agent API — supports openai/gpt-5.5, anthropic/claude-*, google/gemini-*, etc."""
    full_input = f"{system_prompt}\n\n{user_prompt}"
    for attempt in range(max_retries):
        try:
            r = requests.post(
                "https://api.perplexity.ai/v1/agent",
                headers=HEADERS,
                json={"model": MODEL, "input": full_input},
                timeout=120
            )
            r.raise_for_status()
            data = r.json()
            # Extract text from output
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content["text"]
            return str(data)
        except requests.exceptions.HTTPError as e:
            if r.status_code == 429 and attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [429 retry {attempt+1}/{max_retries}, waiting {wait}s]")
                time.sleep(wait)
            else:
                raise


def generate(system_prompt, user_prompt):
    if API == "agent":
        return call_agent(system_prompt, user_prompt)
    else:
        return call_sonar(system_prompt, user_prompt)


with open("data/processed/ieo_benchmark.json") as f:
    problems = json.load(f)

results = []

for problem in problems:
    print(f"\n{'='*60}")
    print(f"Running: {problem['problem_id']} — {problem['topic']}")

    # Step 1: Agent attempts the problem
    agent_answer = generate(
        "You are a student taking the International Economics Olympiad. "
        "Answer the following question as completely and carefully as possible. "
        "Show all your reasoning and working.",
        problem["problem_description"]
    )
    print(f"  Agent answered ({len(agent_answer)} chars)")

    # Step 2: LLM Judge scores the answer
    judge_prompt = f"""You are an expert economics judge scoring a student's answer to an International Economics Olympiad question.

QUESTION:
{problem["problem_description"]}

OFFICIAL SAMPLE SOLUTION:
{problem["gold_label"]["sample_solution"]}

OFFICIAL GRADING RUBRIC:
{problem["gold_label"]["grading_rubric"]}

STUDENT'S ANSWER:
{agent_answer}

Your task:
1. Score the student's answer according to the official grading rubric above.
2. The maximum score is {problem["total_points"]} points.
3. For each criterion in the rubric, state how many points the student earned and why.
4. End with a TOTAL SCORE in the format: "TOTAL: X/{problem["total_points"]}"
"""
    judge_feedback = generate(
        "You are a strict but fair economics olympiad judge. "
        "Score answers accurately according to the provided rubric.",
        judge_prompt
    )
    print(f"  Judge scored.")

    results.append({
        "problem_id": problem["problem_id"],
        "year": problem["year"],
        "topic": problem["topic"],
        "total_points": problem["total_points"],
        "model": MODEL,
        "api": API,
        "agent_answer": agent_answer,
        "judge_feedback": judge_feedback
    })

# Save results
safe_model = MODEL.replace("/", "_").replace(".", "_")
output_path = f"data/processed/results_{safe_model}.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n\nAll done! Results saved to {output_path}")

# Print summary table
print("\n" + "="*60)
print(f"SCORE SUMMARY — {MODEL}")
print("="*60)
for r in results:
    lines = r["judge_feedback"].split("\n")
    score_line = next((l for l in reversed(lines) if "TOTAL:" in l), "TOTAL: ?")
    score = score_line.replace("**", "").replace("TOTAL:", "").strip()
    print(f"{r['problem_id']:<30} {score}")
