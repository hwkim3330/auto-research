import os

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


def load_prompt(name):
    with open(os.path.join(_DIR, name), "r") as f:
        return f.read()
