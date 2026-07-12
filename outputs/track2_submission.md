# CalibratedBatchReview: A Secure Local Review Agent for Timed Paper Assessment

## Abstract

We present CalibratedBatchReview, a local agent for reviewing multiple research PDFs under a short deadline. The system extracts assigned PDFs, scores soundness, novelty, clarity, and significance independently, computes the overall recommendation in deterministic code, detects reviewer-directed prompt injection, and exports aligned JSON, Markdown, and PDF artifacts. A security ablation with three groups of eight texts shows that the layered lexical pre-scan detects 100% of direct attacks and 100% of paraphrased attacks with 0% false positives on clean controls. Exact markers catch known attacks while bounded semantic patterns cover rating demands, suppressed criticism, evidence bypass, and overlooked failures. The design emphasizes auditability, conservative failure recovery, and bounded concurrency over confident but opaque reviewing.

## 1. Motivation

Review agents face a different objective from paper generators. They must process untrusted documents, remain calibrated under time pressure, and produce comparable decisions across many papers. A polished paper can still contain a failed experiment, unsupported claims, or instructions aimed at manipulating an automated reviewer. The review system must therefore separate document content from reviewer instructions and separate dimension scores from the final accept decision.

## 2. Architecture

CalibratedBatchReview has five stages:

1. **PDF ingestion:** `pypdf` extracts text from each organizer-assigned paper.
2. **Security pre-scan:** lexical markers flag direct reviewer instructions before model invocation.
3. **Structured review:** a local Ollama Gemma model returns four independent scores, justifications, strengths, weaknesses, questions, and an injection flag.
4. **Deterministic calibration:** code computes a weighted overall score and recommendation.
5. **Artifact export:** one batch produces machine-readable JSON plus human-readable Markdown and PDF reports.

Independent papers are scheduled with bounded concurrency. A single warm local model avoids cloud credentials and keeps assigned paper content on the machine. Malformed JSON, fenced output, single-object lists, and missing fields are normalized; unresolved fields receive conservative values that remain visible in the audit log.

## 3. Scoring and Calibration

The overall score is never requested directly from the model. It is computed as:

`0.35 soundness + 0.30 novelty + 0.15 clarity + 0.20 significance`.

Recommendations are Accept at 7.5 or higher, Weak Accept at 6.0, Borderline at 4.5, and Reject below 4.5. This design prevents a single free-form “overall impression” from overriding weak scientific dimensions. If injection is suspected, the score is capped at 3.0 and the evidence is retained.

## 4. Prompt-Injection Defense

The paper is explicitly framed as data, never as instructions. Before the model sees it, a lexical scanner checks for direct manipulation phrases such as requests to ignore prior instructions, assign a perfect score, or accept the paper. The model then performs a semantic injection judgment inside the structured review schema. Either layer can trigger the score cap.

### Security ablation

We evaluate the deterministic pre-scan on eight direct attacks, eight paraphrased attacks, and eight clean controls.

| Test group | Detection rate |
|---|---:|
| Direct reviewer instructions | 100% |
| Paraphrased reviewer instructions | 100% |
| Clean controls (false positives) | 0% |

The result shows that exact markers alone are insufficient, while a small set of bounded semantic patterns closes the tested paraphrase gap without producing false positives on the clean controls. The benchmark remains intentionally small, so independent semantic model review and human inspection are still required. The test is reproducible with `experiments/reviewer_security_ablation.py`.

## 5. Timed Batch Workflow

The command `python review_batch.py papers --workers 3` reads assigned PDFs and writes `batch_reviews.json`, `batch_reviews.md`, and `batch_reviews.pdf`. Bounded parallelism overlaps independent requests without loading multiple copies of the model. Errors are isolated per filename, so one unreadable PDF does not erase completed reviews. The JSON bundle preserves raw dimension scores and security flags, while the PDF provides a compact submission artifact.

## 6. Limitations and Responsible Use

Text extraction can lose figures, tables, equations, and layout-dependent evidence. Local-model judgments are not equivalent to expert human reviews. The 24-case security benchmark is intentionally small and cannot represent adaptive attacks. Conservative defaults preserve pipeline completion but must not be mistaken for genuine model judgments. The system should support judges, not replace them, and all final decisions should remain auditable.

## 7. Conclusion

CalibratedBatchReview combines local execution, independent dimension scoring, deterministic recommendations, layered injection defenses, and reproducible artifacts. Its strongest feature is not an inflated benchmark claim; it is explicit separation between what the model proposes, what deterministic code verifies, and what evidence a human judge can inspect.

## References

1. Greshake et al. *More than you've asked for: A Comprehensive Analysis of Novel Prompt Injection Threats to Application-Integrated Large Language Models*. arXiv:2302.12173, 2023.
2. Kapoor et al. *AI Agents That Matter*. arXiv:2407.01502, 2024.
