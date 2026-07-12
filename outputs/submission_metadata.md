# OpenAgentReview Submission Metadata

Use the exact matching title and abstract below in the submission form.

## Track 1 — Submission

**Title**

Gradient-Norm Damping Stabilizes Mini-Batch Training but Does Not Improve Test Error

**Abstract**

Small-batch stochastic optimization can produce noisy updates. We test a simple gradient-norm damping rule that scales each mini-batch update by the inverse of one plus its norm. On a fixed synthetic linear-regression task, damping reduces the standard deviation of the final training-loss trajectory from 0.000086 to 0.000077, but increases held-out test mean-squared error from 0.138566 to 0.139685. The result is a reproducible partial negative: the stability hypothesis receives limited support, while the generalization hypothesis does not.

**PDF**: `outputs/paper_track1_candidate.pdf`

## Track 2 — Technical Report

**Title**

A Robust Local Review Agent for Fast, Evidence-Grounded Paper Assessment

**Abstract**

We present a local Review Agent designed for the Ralphthon ICML 2026 Track 2 technical-report submission. The system accepts assigned paper PDFs, extracts their text, evaluates each paper with a structured ICML-style rubric, detects reviewer-directed prompt injection, computes the overall recommendation deterministically, and exports a reproducible JSON, Markdown, and PDF review bundle. The implementation is optimized for a short review window: PDF parsing is local, independent papers can be processed concurrently, and all model calls use a local Ollama Gemma model so no cloud API key or paper content leaves the machine. The design prioritizes calibrated failure handling over confident but unsupported scores.

**PDF**: `outputs/track2_technical_report.pdf`
