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
    },
    "required": [
        "title",
        "research_question",
        "hypothesis",
        "proposed_method",
        "experiment_plan",
        "novelty_claim",
    ],
}


def generate_idea(topic, model=None):
    related = search_arxiv(topic, max_results=6)
    related_block = "\n".join(f"- {p['title']} — {p['summary'][:200]}" for p in related) or "(no related papers found)"
    user = (
        f"Topic: {topic}\n\n"
        "## Existing related work found via arXiv search (ground your novelty claim against "
        f"these -- do not claim novelty over anything already listed here):\n{related_block}\n\n"
        "Propose one specific, narrow, testable research idea."
    )
    idea = call_llm(SYSTEM_PROMPT, user, model=model, schema=IDEA_SCHEMA, schema_name="submit_idea")
    idea["related_work"] = related
    return idea
