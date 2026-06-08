# Experiment Results — Multi-Model Comparison

**Benchmark:** IEO Agentic Questions (5 questions, 30 pts each)  
**Judge:** same model as agent (self-judging — see observations)

## Score Summary

| Topic | gemini-2.5-flash-lite | openai/gpt-5.5 | sonar-pro | sonar-reasoning-pro |
|---|---|---|---|---|
| Mechanism Design (2019) | **25/30** | **30/30** | **10/30** | **12/30** |
| Dynamic Equilibrium (2021) | **30/30** | **30/30** | **10/30** | **30/30** |
| Going Green (2022) | **26/30** | **30/30** | **22/30** | **None/30** |
| Optimal Lockdown (2020) | **28/30** | **28/30** | **30/30** | **30/30** |
| Buying Cars (2025) | **30/30** | **30/30** | **30/30** | **30/30** |
| **TOTAL /150** | **139/150** | **148/150** | **102/150** | **102/150** |

## Key Observations

- **Self-judging bias**: each model judges its own answers, which inflates scores — GPT-5.5 and Gemini score near-perfect
- **sonar-pro** shows the most spread (102/150), struggling on Mechanism Design and Dynamic Equilibrium (10/30 each)
- **Next step**: use a fixed external judge (e.g. always use GPT-5.5 as judge for all models) for a fairer comparison
- The benchmark does differentiate between models, validating its design