# Evidence-Locked Scientific Writing for Autonomous Research Agents

## Abstract

Autonomous research agents can execute experiments yet still report unsupported numerical claims when converting logs into papers. We introduce an evidence lock that treats subprocess output as a typed ledger and permits a numerical claim only when its metric identity and value match recorded evidence. A 30-seed, 30,000-claim synthetic ablation compares no gate, exact-string matching, and tolerance-aware normalized matching. Exact matching rejects every unsupported claim but recalls only 75.21% (+/-0.62% 95% CI) of supported claims because harmless rounding changes the string representation. The normalized gate achieves 99.59% (+/-0.07%) precision and 100% supported-claim recall while accepting 1.68% (+/-0.29%) of unsupported claims. This identifies a reproducible safety-quality trade-off and yields a small, auditable component for generator-reviewer research loops.

## 1. Introduction

AI Scientist systems join idea generation, code execution, analysis, and paper writing into one autonomous workflow. Executing code is necessary but not sufficient for scientific integrity: a writer can still introduce a value that was absent from the run, copy a number under the wrong metric name, or reject a legitimate rounded value. In a timed autonomous loop, these failures are particularly dangerous because a fluent manuscript can conceal a broken evidence chain.

We study one narrow question: can a deterministic evidence gate reduce unsupported numerical claims without discarding correctly rounded claims? Our contribution is an evidence-locking rule and a controlled ablation that exposes the trade-off between strict string identity and normalized numerical matching. The goal is not to establish general scientific validity; it is to make one failure mode measurable and auditable.

## 2. Evidence-Lock Method

The experiment runner emits a ledger of metric names, numeric values, and their printed representations. A candidate paper claim contains a metric identifier and a value. We compare three policies:

1. **No gate** accepts every generated claim.
2. **Exact string gate** accepts only a value whose printed string exactly matches the ledger.
3. **Normalized evidence gate** requires the same metric identity and accepts values within a tolerance of `max(0.005, 0.5% of |reference|)`.

The normalized gate is intentionally small and deterministic. It does not judge whether an experiment is well designed; it only checks whether a reported value can be traced to execution evidence.

## 3. Experimental Design

For each of 30 fixed seeds, we create 40 evidence metrics and 1,000 candidate claims, giving 30,000 claims in total: 23,987 supported and 6,013 unsupported. Supported claims are exact or rounded representations of ledger values; unsupported claims are perturbed values attached to a valid metric or unrelated values. We report the across-seed mean and 95% confidence interval (1.96 standard errors) for precision among accepted claims, recall of supported claims, and unsupported-claim acceptance. The complete deterministic experiment is implemented in `experiments/evidence_lock_ablation.py`.

## 4. Results

| Policy | Precision | Supported recall | Unsupported accepted |
|---|---:|---:|---:|
| No gate | 79.96 +/- 0.38% | 100.00 +/- 0.00% | 100.00 +/- 0.00% |
| Exact string gate | 100.00 +/- 0.00% | 75.21 +/- 0.62% | 0.00 +/- 0.00% |
| Normalized evidence gate | 99.59 +/- 0.07% | 100.00 +/- 0.00% | 1.68 +/- 0.29% |

The no-gate baseline accepts all 6,013 unsupported claims. Exact matching eliminates those errors but rejects 5,947 supported rounded claims. Normalized matching accepts every supported claim and rejects 5,913 of 6,013 unsupported claims; its 100 residual errors occur when a perturbation falls inside the declared tolerance. The confidence intervals show that the trade-off persists across seeds rather than depending on one favorable sample.

## 5. Integration into an Autonomous Research Loop

The gate sits between experiment execution and paper synthesis. The runner first captures stdout and structured metrics. The paper agent receives only this evidence block. Before export, candidate numerical claims are checked against the ledger, and the review agent separately scores soundness, novelty, clarity, and significance. The final PDF and JSON run history are generated from the selected draft, preserving both the artifact and its provenance.

This separation matters: generation remains flexible, while evidence validation and overall-score computation remain deterministic. A failed experiment can still produce an honest negative report, but it cannot silently become a successful numerical result.

## 6. Limitations

The benchmark is synthetic and isolates numerical provenance rather than full scientific quality. The tolerance is hand selected, and a real system should use metric-specific units and uncertainty. The gate cannot detect unsupported qualitative claims, data leakage, weak baselines, or incorrect experimental code. A malicious value can also fall inside tolerance. These limitations motivate combining evidence locking with code execution, independent review, and human inspection.

## 7. Conclusion

Evidence locking turns a vague instruction - “do not hallucinate numbers” - into a measurable control. Exact matching is safe but brittle; normalized matching preserves rounded claims while rejecting 98.32% of unsupported claims across 30 seeds. The component is deliberately modest, reproducible, and suitable for deployment inside an autonomous paper-generation loop.

## References

1. Lu et al. *The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery*. arXiv:2408.06292, 2024.
2. Kapoor et al. *AI Agents That Matter*. arXiv:2407.01502, 2024.
