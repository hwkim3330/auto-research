"""Thin provider-agnostic LLM wrapper.

Supports Anthropic and OpenAI. Structured output (a JSON-schema dict) is
enforced via forced tool/function calling on both providers so callers get
back a parsed dict, never free-text they have to regex out of a response.
"""
import json
import os
import urllib.error
import urllib.request

from json_repair import repair_json

from dotenv import load_dotenv

load_dotenv()


def default_model():
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "ollama":
        return os.environ.get("OLLAMA_MODEL", "gemma4:e4b-mlx")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
    return os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")


def default_strong_model():
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "ollama":
        return os.environ.get("OLLAMA_STRONG_MODEL", "gemma4:e4b-mlx")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_STRONG_MODEL", "claude-opus-4-8")
    return os.environ.get("OPENAI_STRONG_MODEL", "gpt-5.6-sol")


def default_middle_model():
    """Balanced model for code generation and revision passes."""
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "ollama":
        return os.environ.get("OLLAMA_MIDDLE_MODEL", "gemma4:e4b-mlx")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_MIDDLE_MODEL", default_model())
    return os.environ.get("OPENAI_MIDDLE_MODEL", "gpt-5.6-terra")


def call_llm(system, user, model=None, schema=None, schema_name="output", max_tokens=4096):
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "anthropic":
        return _call_anthropic(system, user, model, schema, schema_name, max_tokens)
    if provider == "openai":
        return _call_openai(system, user, model, schema, schema_name, max_tokens)
    if provider == "ollama":
        return _call_ollama(system, user, model, schema, max_tokens)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'anthropic', 'openai', or 'ollama')")


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
    if schema:
        # Responses API is the current OpenAI interface. Native structured
        # output avoids parsing brittle free-form model text.
        resp = client.responses.create(
            model=model or default_model(),
            instructions=system,
            input=user,
            max_output_tokens=max_tokens,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": _strict_schema(schema),
                }
            },
        )
        return json.loads(resp.output_text)
    resp = client.responses.create(
        model=model or default_model(),
        instructions=system,
        input=user,
        max_output_tokens=max_tokens,
    )
    return resp.output_text


def _call_ollama(system, user, model, schema, max_tokens):
    """Call a local Ollama model without requiring any cloud API key."""
    payload = {
        "model": model or default_model(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_ctx": int(os.environ.get("OLLAMA_NUM_CTX", "32768")),
            "num_predict": max_tokens,
        },
    }
    if schema:
        payload["format"] = _strict_schema(schema)
    request = urllib.request.Request(
        os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    result = _ollama_request(request)
    content = result.get("message", {}).get("content", "")
    if schema:
        try:
            return _coerce_schema_result(_parse_json_content(content), schema)
        except json.JSONDecodeError:
            # Some local models honor JSON mode but not the full schema. Retry
            # once with a compact schema instruction rather than failing the run.
            payload["format"] = "json"
            payload["messages"][0]["content"] += (
                "\nReturn ONLY one valid JSON object matching this schema, with no prose:\n"
                + json.dumps(_strict_schema(schema))
            )
            retry = urllib.request.Request(
                os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/chat",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            retry_content = _ollama_request(retry).get("message", {}).get("content", "")
            try:
                return _coerce_schema_result(_parse_json_content(retry_content), schema)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Ollama returned non-JSON structured output: {retry_content[:500]}") from exc
    return content


def _ollama_request(request):
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError("Ollama is not reachable. Start it with `ollama serve`.") from exc


def _parse_json_content(content):
    """Accept strict JSON plus the Markdown fences local models often add."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Local models sometimes emit LaTeX backslashes or trailing commas
        # inside otherwise valid JSON. Repair only after strict parsing fails.
        return json.loads(repair_json(cleaned))


def _coerce_schema_result(result, schema):
    """Normalize common local-model mistakes in simple object schemas."""
    if schema.get("type") == "object" and isinstance(result, list):
        if len(result) == 1 and isinstance(result[0], dict):
            result = result[0]
        elif len(schema.get("properties", {})) == 1 and result and isinstance(result[0], str):
            key = next(iter(schema["properties"]))
            result = {key: result[0]}
    return result


def _strict_schema(schema):
    """Make the repository's compact schemas valid strict JSON schemas."""
    schema = json.loads(json.dumps(schema))
    if schema.get("type") == "object":
        properties = schema.setdefault("properties", {})
        schema["additionalProperties"] = False
        schema["required"] = list(properties)
        for value in properties.values():
            _strict_schema(value)
    elif schema.get("type") == "array" and "items" in schema:
        _strict_schema(schema["items"])
    return schema
