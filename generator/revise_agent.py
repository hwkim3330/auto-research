from utils.llm import call_llm, default_middle_model
from utils.prompts import load_prompt

SYSTEM_PROMPT = load_prompt("revise_system.md")


def revise_paper(paper_markdown, review, model=None):
    user = (
        f"# Current paper\n{paper_markdown}\n\n"
        "# Reviewer feedback\n"
        f"Scores: soundness={review['soundness']}, novelty={review['novelty']}, "
        f"clarity={review['clarity']}, significance={review['significance']}, "
        f"overall={review['overall_score']} ({review['recommendation']})\n"
        f"Weaknesses: {review['weaknesses']}\n"
        f"Questions: {review['questions_for_authors']}\n\n"
        "Revise the paper to address the weaknesses and questions above."
    )
    return call_llm(SYSTEM_PROMPT, user, model=model or default_middle_model())
