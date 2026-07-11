"""Thin provider-agnostic LLM wrapper.

Supports Anthropic and OpenAI. Structured output (a JSON-schema dict) is
enforced via forced tool/function calling on both providers so callers get
back a parsed dict, never free-text they have to regex out of a response.
"""
import json
import os


def default_model():
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
    return os.environ.get("OPENAI_MODEL", "gpt-5")


def default_strong_model():
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_STRONG_MODEL", "claude-opus-4-8")
    return os.environ.get("OPENAI_STRONG_MODEL", "gpt-5")


def call_llm(system, user, model=None, schema=None, schema_name="output", max_tokens=4096):
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "anthropic":
        return _call_anthropic(system, user, model, schema, schema_name, max_tokens)
    if provider == "openai":
        return _call_openai(system, user, model, schema, schema_name, max_tokens)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'anthropic' or 'openai')")


def _call_anthropic(system, user, model, schema, schema_name, max_tokens):
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    kwargs = dict(
        model=model or default_model(),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if schema:
        kwargs["tools"] = [
            {"name": schema_name, "description": f"Submit the {schema_name}.", "input_schema": schema}
        ]
        kwargs["tool_choice"] = {"type": "tool", "name": schema_name}
    resp = client.messages.create(**kwargs)
    if schema:
        for block in resp.content:
            if block.type == "tool_use":
                return block.input
        raise RuntimeError("Anthropic response had no tool_use block")
    return "".join(b.text for b in resp.content if b.type == "text")


def _call_openai(system, user, model, schema, schema_name, max_tokens):
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if schema:
        tools = [{"type": "function", "function": {"name": schema_name, "parameters": schema}}]
        resp = client.chat.completions.create(
            model=model or default_model(),
            messages=messages,
            max_completion_tokens=max_tokens,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": schema_name}},
        )
        call = resp.choices[0].message.tool_calls[0]
        return json.loads(call.function.arguments)
    resp = client.chat.completions.create(
        model=model or default_model(), messages=messages, max_completion_tokens=max_tokens
    )
    return resp.choices[0].message.content
