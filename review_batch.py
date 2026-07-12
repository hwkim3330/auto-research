"""Review a directory of PDF papers concurrently for Ralphthon Track 2."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pypdf import PdfReader

from reviewer.review_agent import review_paper


def extract_pdf(path):
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def review_one(path):
    text = extract_pdf(path)
    if not text.strip():
        raise ValueError(f"No extractable text in {path.name}")
    return {"file": path.name, "review": review_paper(text)}


def run_batch(input_dir, output_dir, workers=5):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    papers = sorted(input_dir.glob("*.pdf"))
    if not papers:
        raise SystemExit(f"No PDF papers found in {input_dir}")

    results = []
    with ThreadPoolExecutor(max_workers=min(workers, len(papers))) as pool:
        futures = {pool.submit(review_one, path): path for path in papers}
        for future in as_completed(futures):
            path = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"file": path.name, "error": str(exc)}
            results.append(result)
            print(f"[{'ok' if 'review' in result else 'error'}] {path.name}")

    results.sort(key=lambda item: item["file"])
    json_path = output_dir / "batch_reviews.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    md_path = output_dir / "batch_reviews.md"
    lines = ["# Track 2 Batch Reviews", ""]
    for item in results:
        lines.append(f"## {item['file']}")
        if "error" in item:
            lines.append(f"**Error:** {item['error']}\n")
            continue
        review = item["review"]
        lines.extend([
            f"- Overall: **{review['overall_score']}** ({review['recommendation']})",
            f"- Soundness: {review['soundness']} | Novelty: {review['novelty']} | Clarity: {review['clarity']} | Significance: {review['significance']}",
            f"- Suspected injection: {review['suspected_injection']}",
            "",
            "### Strengths",
            *[f"- {x}" for x in review["strengths"]],
            "",
            "### Weaknesses",
            *[f"- {x}" for x in review["weaknesses"]],
            "",
        ])
    md_path.write_text("\n".join(lines))
    print(f"Saved {json_path}")
    print(f"Saved {md_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel PDF reviewer for Track 2")
    parser.add_argument("input_dir", help="Directory containing paper PDFs")
    parser.add_argument("--output-dir", default="outputs/track2", dest="output_dir")
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()
    run_batch(args.input_dir, args.output_dir, args.workers)
