# OpenAgentReview Submission Metadata

Use the exact matching title and abstract below in the submission form.

## Track 1 — Submission

**Title**

Evidence-Locked Scientific Writing for Autonomous Research Agents

**Abstract**

Autonomous research agents can execute experiments yet still report unsupported numerical claims when converting logs into papers. We introduce an evidence lock that treats subprocess output as a typed ledger and permits a numerical claim only when its metric identity and value match recorded evidence. A 30-seed, 30,000-claim synthetic ablation compares no gate, exact-string matching, and tolerance-aware normalized matching. Exact matching rejects every unsupported claim but recalls only 75.21% (+/-0.62% 95% CI) of supported claims because harmless rounding changes the string representation. The normalized gate achieves 99.59% (+/-0.07%) precision and 100% supported-claim recall while accepting 1.68% (+/-0.29%) of unsupported claims. This identifies a reproducible safety-quality trade-off and yields a small, auditable component for generator-reviewer research loops.

**PDF**: `outputs/track1_submission.pdf`

## Track 2 — Technical Report

**Title**

CalibratedBatchReview: A Secure Local Review Agent for Timed Paper Assessment

**Abstract**

We present CalibratedBatchReview, a local agent for reviewing multiple research PDFs under a short deadline. The system extracts assigned PDFs, scores soundness, novelty, clarity, and significance independently, computes the overall recommendation in deterministic code, detects reviewer-directed prompt injection, and exports aligned JSON, Markdown, and PDF artifacts. A security ablation with three groups of eight texts shows that the layered lexical pre-scan detects 100% of direct attacks and 100% of paraphrased attacks with 0% false positives on clean controls. Exact markers catch known attacks while bounded semantic patterns cover rating demands, suppressed criticism, evidence bypass, and overlooked failures. The design emphasizes auditability, conservative failure recovery, and bounded concurrency over confident but opaque reviewing.

**PDF**: `outputs/track2_submission.pdf`
