"""Generator <-> critic orchestrator.

Supports two modes so you can run the actual ablation this project is meant
to test -- literature surveyed for this project found no verified evidence
that a generator-critic self-play loop reliably improves research-paper
quality (as opposed to general reasoning/code tasks). Don't assume `loop` beats
`single`: run both and compare the review scores yourself.

  single: one-pass baseline, no critic loop at all.
  loop:   generator -> reviewer -> revise, repeated up to `rounds` times or
          until the reviewer recommends Accept.
"""
import json
import os
import time

from generator.idea_agent import generate_idea
from generator.paper_agent import write_paper
from generator.revise_agent import revise_paper
from reviewer.review_agent import review_paper


def run_pipeline(topic, mode="loop", rounds=3, outdir="outputs"):
    os.makedirs(outdir, exist_ok=True)
    log = {"topic": topic, "mode": mode, "rounds_requested": rounds, "history": []}

    idea = generate_idea(topic)
    log["idea"] = idea

    draft = write_paper(idea)
    paper_md = draft["paper_markdown"]
    log["experiment_code"] = draft["experiment_code"]
    log["experiment_result"] = draft["experiment_result"]

    if mode == "single":
        review = review_paper(paper_md)
        log["history"].append({"round": 0, "paper": paper_md, "review": review})
        log["final_paper"] = paper_md
        return _save(log, outdir)

    best = {"paper": paper_md, "review": None, "round": -1}
    for i in range(rounds):
        review = review_paper(paper_md)
        log["history"].append({"round": i, "paper": paper_md, "review": review})
        print(f"[round {i}] overall={review['overall_score']} recommendation={review['recommendation']}")
        if best["review"] is None or review["overall_score"] > best["review"]["overall_score"]:
            best = {"paper": paper_md, "review": review, "round": i}
        if review["recommendation"] == "Accept":
            break
        paper_md = revise_paper(paper_md, review)

    final_review = review_paper(paper_md)
    log["history"].append({"round": len(log["history"]), "paper": paper_md, "review": final_review})
    if final_review["overall_score"] > best["review"]["overall_score"]:
        best = {"paper": paper_md, "review": final_review, "round": len(log["history"]) - 1}
    log["selected_round"] = best["round"]
    log["selected_review"] = best["review"]
    log["final_paper"] = best["paper"]
    return _save(log, outdir)


def _save(log, outdir):
    stamp = str(int(time.time()))
    json_path = os.path.join(outdir, f"run_{stamp}.json")
    with open(json_path, "w") as f:
        json.dump(log, f, indent=2)
    md_path = os.path.join(outdir, f"paper_{stamp}.md")
    with open(md_path, "w") as f:
        f.write(log["final_paper"])
    print(f"Saved run log to {json_path}")
    print(f"Saved final paper to {md_path}")
    return log
