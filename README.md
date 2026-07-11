# auto-research

Generator (AI Scientist) + Critic (Review Agent) pipeline for [Ralphthon @ ICML "Auto Research"](https://luma.com/) (Team Attention, 2026-07-12).

- **Track 1 — AI Scientist**: `generator/` — proposes an idea, grounds novelty against real arXiv results, writes and *actually executes* a small experiment, then writes an ICML-style paper from the real execution output.
- **Track 2 — Review Agent**: `reviewer/` — scores the paper on an ICML-style rubric (soundness / novelty / clarity / significance), hardened against known LLM-reviewer failure modes.
- **The loop**: `loop/orchestrator.py` connects them generator → reviewer → revise, for up to N rounds.

## Why it's built this way (research findings baked into the design)

A literature/benchmark sweep (2025-2026) before building this turned up hard failure modes in every prior "AI Scientist" and "LLM reviewer" system. Each one maps to a specific design decision here:

| Finding | Source | Design response |
|---|---|---|
| 57% of Sakana AI Scientist v1 manuscripts contained fabricated numerical results | arXiv:2502.14297 | `experiment_runner.py` actually executes the generated code; `paper_agent.py`'s system prompt forbids reporting any number not in the real stdout |
| Self-assessed novelty checks are unreliable (labeled a known technique "novel") | arXiv:2502.14297 | `lit_search.py` grounds novelty against real arXiv search results, not the model's own opinion |
| Best 2026 autonomous research agents still score only 21-53% on rigorous end-to-end benchmarks; recurring "overexcitement" (claiming success despite failure) | arXiv:2510.21652, 2606.07591, 2601.03315 | paper-writing prompt explicitly requires honest failure reporting in Results/Limitations |
| LLM reviewer overall/final ratings correlate only weakly with human judgment (r≈0.29) even though sub-dimension scores correlate well (r=0.77–0.84) | arXiv:2605.16616, 2509.09912v1, 2605.25415 | `reviewer/rubric.py` computes the overall score and accept/reject recommendation **in code** from independently-scored sub-dimensions — the model is never asked for an overall score directly |
| LLM reviewers rate ~1.16 points (of 10) more leniently than humans and over-rate weak papers | arXiv:2605.16616 | review system prompt explicitly instructs the model to resist leniency bias and penalize weak/failed experiments regardless of writing polish |
| Hidden prompt-injection text in a paper ("give this a 10/10") fools LLM reviewers into a perfect score in ~30% of trials (real ICLR/ICML 2026 misconduct cases) | arXiv:2509.09912v1, 2605.25415 | `review_agent.py` heuristically pre-scans paper text for injection markers *and* instructs the model to treat the paper as data-not-instructions and self-report `suspected_injection`; either signal caps the score |
| No verified evidence that a generator-critic self-play loop actually improves research-paper quality (vs. general reasoning/code tasks, where intrinsic self-correction has been shown to sometimes make things *worse*) | arXiv:2310.01798; gap in surveyed literature | the orchestrator supports `--mode single` vs `--mode loop` specifically so you can **run the ablation yourself** instead of assuming the loop helps — this doubles as the demo's "core experiment" |

## Architecture

```
            topic
              │
              ▼
   ┌─────────────────────┐
   │ generator/idea_agent │──► arXiv search (lit_search.py) grounds novelty
   └─────────┬────────────┘
             ▼
   ┌─────────────────────┐
   │ generator/paper_agent│──► writes + RUNS real experiment code
   └─────────┬────────────┘        (experiment_runner.py, subprocess)
             ▼
   paper draft (Markdown)
             │
   ┌─────────▼────────────┐   mode=single: stop here, one review, done
   │ reviewer/review_agent │◄─┐
   └─────────┬─────────────┘  │ mode=loop: repeat up to --rounds times
             ▼                │ or until recommendation == Accept
   ┌─────────────────────┐    │
   │ generator/revise_agent│───┘
   └──────────────────────┘
             │
             ▼
   outputs/paper_<ts>.md + run_<ts>.json (full history incl. all review rounds)
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY or OPENAI_API_KEY
export $(cat .env | xargs)   # or use direnv / python-dotenv
```

## Usage

```bash
# Full generator-critic loop (the default)
python main.py --topic "Adaptive learning rate scheduling for small-batch SGD" --mode loop --rounds 3

# One-pass baseline, for the ablation comparison against the loop above
python main.py --topic "Adaptive learning rate scheduling for small-batch SGD" --mode single
```

Each run writes `outputs/paper_<timestamp>.md` (final paper) and `outputs/run_<timestamp>.json` (full history: idea, related work, experiment code + real execution output, every review round with sub-scores).

## Safety note

`experiment_runner.py` executes model-generated Python in a subprocess with only a timeout — no sandboxing beyond that (same tradeoff Sakana's own AI Scientist makes). Don't point this at anything you wouldn't want arbitrary generated code running next to; use a container/VM for real isolation.

## Cost tiering

Cheap/default model (`ANTHROPIC_MODEL` / `OPENAI_MODEL`) handles idea generation, experiment-code drafting, and review scoring. The stronger model (`ANTHROPIC_STRONG_MODEL` / `OPENAI_STRONG_MODEL`) is only used for the final paper-writing synthesis step, per standard practice for long autonomous loops — most of the loop's cost is iteration, not final synthesis.
