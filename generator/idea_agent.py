from lit_search import search_arxiv
from utils.llm import call_llm
from utils.prompts import load_prompt

SYSTEM_PROMPT = load_prompt("idea_system.md")

IDEA_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "research_question": {"type": "string"},
        "hypothesis": {"type": "string"},
        "proposed_method": {"type": "string"},
        "experiment_plan": {"type": "string"},
        "novelty_claim": {"type": "string"},
        "baseline": {"type": "string"},
        "success_criteria": {"type": "string"},
        "risks_and_fallbacks": {"type": "string"},
    },
    "required": [
        "title",
        "research_question",
        "hypothesis",
        "proposed_method",
        "experiment_plan",
        "novelty_claim",
        "baseline",
        "success_criteria",
        "risks_and_fallbacks",
    ],
}


def generate_idea(topic, model=None):
    related = search_arxiv(topic, max_results=6)
    related_block = "\n".join(f"- {p['title']} — {p['summary'][:200]}" for p in related) or "(no related papers found)"
    user = (
        f"Topic: {topic}\n\n"
        "## Existing related work found via arXiv search (ground your novelty claim against "
        f"these -- do not claim novelty over anything already listed here):\n{related_block}\n\n"
        "Propose one specific, narrow, testable research idea. Include a strong but "
        "simple baseline, a measurable success criterion, and a fallback if the "
        "hypothesis fails. Optimize for a convincing, reproducible hackathon demo."
    )
    idea = call_llm(SYSTEM_PROMPT, user, model=model, schema=IDEA_SCHEMA, schema_name="submit_idea")
    required = IDEA_SCHEMA["required"]
    missing = [key for key in required if not idea.get(key)]
    if missing:
        # Small local models occasionally omit fields despite JSON mode. A
        # targeted retry is cheaper and safer than letting a partial idea
        # crash the whole submission run later.
        retry_user = user + (
            "\n\nIMPORTANT: your previous response omitted required fields. Return a complete "
            "object with every key exactly as spelled here, with non-empty string values: "
            + ", ".join(required)
        )
        idea = call_llm(SYSTEM_PROMPT, retry_user, model=model, schema=IDEA_SCHEMA, schema_name="submit_idea")
        missing = [key for key in required if not idea.get(key)]
        if missing:
            raise RuntimeError(f"Idea model omitted required fields after retry: {missing}")
    idea["related_work"] = related
    return idea
