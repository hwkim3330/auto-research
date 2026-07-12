"""Synthetic ablation for evidence-locked numerical claims."""
import json
import random


SEED = 42
N = 1000
random.seed(SEED)


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
    }


evidence = {}
for i in range(40):
    value = random.uniform(0.1, 9.9)
    evidence[f"metric_{i}"] = {"value": value, "printed": f"{value:.4f}"}

claims = []
labels = []
for _ in range(N):
    metric = random.choice(list(evidence))
    reference = evidence[metric]["value"]
    mode = random.random()
    if mode < 0.60:
        value = reference
        printed = f"{reference:.4f}"
        supported = True
    elif mode < 0.80:
        value = round(reference, 2)
        printed = f"{value:.2f}"
        supported = True
    elif mode < 0.95:
        value = reference + random.choice([-1, 1]) * random.uniform(0.02, 0.50)
        printed = f"{value:.4f}"
        supported = False
    else:
        value = random.uniform(10.0, 99.0)
        printed = f"{value:.4f}"
        supported = False
    claims.append({"metric": metric, "value": value, "printed": printed})
    labels.append(supported)

results = [
    evaluate("No gate", [True] * N, labels),
    evaluate("Exact string gate", [exact_gate(c, evidence) for c in claims], labels),
    evaluate("Normalized evidence gate", [normalized_gate(c, evidence) for c in claims], labels),
]

payload = {
    "seed": SEED,
    "claims": N,
    "supported_claims": sum(labels),
    "unsupported_claims": sum(not x for x in labels),
    "results": results,
}
print(json.dumps(payload, indent=2))
