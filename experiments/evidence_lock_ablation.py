"""Multi-seed ablation for evidence-locked numerical claims."""
import json
import math
import random
import statistics


SEEDS = list(range(30))
CLAIMS_PER_SEED = 1000


def exact_gate(candidate, evidence):
    return candidate["printed"] == evidence[candidate["metric"]]["printed"]


def normalized_gate(candidate, evidence):
    reference = evidence[candidate["metric"]]["value"]
    tolerance = max(0.005, abs(reference) * 0.005)
    return abs(candidate["value"] - reference) <= tolerance


def evaluate(name, accepted, labels):
    tp = sum(a and y for a, y in zip(accepted, labels))
    fp = sum(a and not y for a, y in zip(accepted, labels))
    fn = sum((not a) and y for a, y in zip(accepted, labels))
    negatives = sum(not y for y in labels)
    return {
        "method": name,
        "precision": tp / (tp + fp) if tp + fp else 1.0,
        "supported_recall": tp / (tp + fn) if tp + fn else 1.0,
        "unsupported_accept_rate": fp / negatives if negatives else 0.0,
        "accepted": tp + fp,
        "unsupported_accepted": fp,
    }


def run_seed(seed):
    rng = random.Random(seed)
    evidence = {}
    for i in range(40):
        value = rng.uniform(0.1, 9.9)
        evidence[f"metric_{i}"] = {"value": value, "printed": f"{value:.4f}"}

    claims, labels = [], []
    for _ in range(CLAIMS_PER_SEED):
        metric = rng.choice(list(evidence))
        reference = evidence[metric]["value"]
        mode = rng.random()
        if mode < 0.60:
            value, printed, supported = reference, f"{reference:.4f}", True
        elif mode < 0.80:
            value, supported = round(reference, 2), True
            printed = f"{value:.2f}"
        elif mode < 0.95:
            value = reference + rng.choice([-1, 1]) * rng.uniform(0.02, 0.50)
            printed, supported = f"{value:.4f}", False
        else:
            value = rng.uniform(10.0, 99.0)
            printed, supported = f"{value:.4f}", False
        claims.append({"metric": metric, "value": value, "printed": printed})
        labels.append(supported)

    return {
        "supported": sum(labels),
        "unsupported": sum(not x for x in labels),
        "results": [
            evaluate("No gate", [True] * CLAIMS_PER_SEED, labels),
            evaluate("Exact string gate", [exact_gate(c, evidence) for c in claims], labels),
            evaluate("Normalized evidence gate", [normalized_gate(c, evidence) for c in claims], labels),
        ],
    }


def summarize(values):
    mean = statistics.mean(values)
    ci95 = 1.96 * statistics.stdev(values) / math.sqrt(len(values))
    return {"mean": mean, "ci95": ci95}


runs = [run_seed(seed) for seed in SEEDS]
methods = []
for method_index, method_name in enumerate(["No gate", "Exact string gate", "Normalized evidence gate"]):
    row = {"method": method_name}
    for metric in ["precision", "supported_recall", "unsupported_accept_rate"]:
        row[metric] = summarize([run["results"][method_index][metric] for run in runs])
    row["unsupported_accepted_total"] = sum(run["results"][method_index]["unsupported_accepted"] for run in runs)
    row["supported_accepted_total"] = sum(
        run["results"][method_index]["accepted"] - run["results"][method_index]["unsupported_accepted"]
        for run in runs
    )
    row["supported_rejected_total"] = sum(run["supported"] for run in runs) - row["supported_accepted_total"]
    methods.append(row)

payload = {
    "seeds": len(SEEDS),
    "claims_per_seed": CLAIMS_PER_SEED,
    "claims_total": len(SEEDS) * CLAIMS_PER_SEED,
    "supported_claims_total": sum(run["supported"] for run in runs),
    "unsupported_claims_total": sum(run["unsupported"] for run in runs),
    "methods": methods,
}
print(json.dumps(payload, indent=2))
