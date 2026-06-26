# Multi-Agent Business Case Results

**Case:** IEO 2025 — The Caspian Connector (`econ_ieo_2025_bc`)  
**Setup:** 5 agents, 3 discussion rounds, no pre-assigned roles, emergent collaboration

## Scores (GPT-5.5 judge, /50)

| Format | Agents | Analytical | Conceptual | Quantitative | Communication | **Total** |
|---|---|---|---|---|---|---|
| Written report | GPT-5.5 (5 agents) | 14/15 | 14/15 | 9/10 | 9/10 | **46/50** |
| Slide deck | GPT-5.5 (5 agents) | 13/15 | 14/15 | 8/10 | 9/10 | **44/50** |

Report scored slightly higher (+2). Same recommendation in both runs: defer fixed link, pursue corridor upgrades first.

## Human baseline (2025 IEO, same case)

From [2025 IEO results](https://2025.ieo-official.org/results):

| Team | Raw score | Notes |
|---|---|---|
| Canada (1st place) | 92.5 | Only winner's raw score published |
| Other finalists | N/A | Full ranking not published |

Human teams are scored by a professional jury. Raw scores are normalized to final /50 via Z-scores. Direct comparison to our LLM judge scores is approximate.

## Files

| Format | JSON | Readable |
|---|---|---|
| Report | `multiagent_openai_gpt-5_5_judgedby_openai_gpt-5_5.json` | — |
| Slides | `multiagent_slides_openai_gpt-5_5_judgedby_openai_gpt-5_5.json` | `multiagent_slides_openai_gpt-5_5_judgedby_openai_gpt-5_5.md` |

Case source: `data/raw/business_case/2025.pdf`  
Script: `src/run.py` (add `slides` as third argument for slide format)
