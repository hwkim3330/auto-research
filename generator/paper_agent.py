from generator.experiment_runner import run_experiment
from utils.llm import call_llm, default_strong_model
from utils.prompts import load_prompt

SYSTEM_PROMPT = load_prompt("paper_system.md")

CODE_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": (
                "Self-contained Python script (stdlib + numpy/pandas/sklearn only, no "
                "network access, must finish in under 60s) that actually tests the idea "
                "and prints every metric it wants reported, clearly labeled."
            ),
        }
    },
    "required": ["code"],
}


def draft_experiment_code(idea, model=None):
    user = (
        f"Idea: {idea['title']}\n{idea['proposed_method']}\n\n"
        f"Experiment plan: {idea['experiment_plan']}\n\n"
        "Write a small, self-contained Python script that actually tests this idea and "
        "prints every metric it wants reported, clearly labeled."
    )
    result = call_llm(SYSTEM_PROMPT, user, model=model, schema=CODE_SCHEMA, schema_name="submit_code")
    return result["code"]


def write_paper(idea, model=None, strong_model=None):
    code = draft_experiment_code(idea, model=model)
    exec_result = run_experiment(code)

    grounding = (
        "## ACTUAL experiment execution output (this is the ONLY source of truth for "
        "numbers in the paper -- do not invent any number not present here):\n"
        f"success={exec_result['success']}\n"
        f"stdout:\n{exec_result['stdout']}\n"
        f"stderr:\n{exec_result['stderr']}\n"
    )
    if not exec_result["success"]:
        grounding += (
            "\nThe experiment FAILED. The paper MUST honestly report this as a "
            "negative/failed result, not invent success.\n"
        )

    related_block = "\n".join(f"- {p['title']}" for p in idea.get("related_work", []))
    user = (
        f"# Idea\nTitle: {idea['title']}\nResearch question: {idea['research_question']}\n"
        f"Hypothesis: {idea['hypothesis']}\nMethod: {idea['proposed_method']}\n\n"
        f"# Related work found (cite/compare against, do not claim novelty over these)\n{related_block}\n\n"
        f"{grounding}\n"
        "Write a short ICML-style paper (Abstract, Introduction, Method, Experiments, "
        "Results, Related Work, Limitations, Conclusion) in Markdown. Every number in "
        "Results MUST come from the execution output above."
    )
    paper_md = call_llm(SYSTEM_PROMPT, user, model=strong_model or default_strong_model())
    return {"paper_markdown": paper_md, "experiment_code": code, "experiment_result": exec_result}
