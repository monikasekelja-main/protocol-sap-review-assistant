"""One bounded model call; no tools, browsing, dynamic URLs or payload logging."""

import copy
import json
import urllib.error
import urllib.request

from django.conf import settings


class ProviderError(RuntimeError):
    pass


def provider_schema(model):
    schema = copy.deepcopy(model.model_json_schema())

    # API-constrained JSON schemas omit local-only size bounds; Pydantic enforces them afterwards.
    def clean(value):
        if isinstance(value, dict):
            for key in ["minLength", "maxLength", "maxItems", "minimum", "maximum", "title"]:
                value.pop(key, None)
            if value.get("minItems", 0) > 1:
                value.pop("minItems")
            for child in value.values():
                clean(child)
        elif isinstance(value, list):
            for child in value:
                clean(child)

    clean(schema)
    return schema


def generate(system, context, schema):
    if not settings.AI_ENABLED:
        raise ProviderError("AI is not configured.")
    if len(json.dumps(context)) > 180_000:
        raise ProviderError("The review context exceeds the model budget.")
    payload = {
        "model": settings.ANTHROPIC_MODEL,
        "max_tokens": 10000,
        "system": system,
        "messages": [{"role": "user", "content": json.dumps(context)}],
        "output_config": {"format": {"type": "json_schema", "schema": provider_schema(schema)}},
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.loads(response.read(1_000_000))
        if result.get("stop_reason") != "end_turn":
            raise ProviderError("The model response was incomplete.")
        text = "".join(c.get("text", "") for c in result["content"] if c["type"] == "text")
        return schema.model_validate_json(text), result.get("usage", {})
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as exc:
        raise ProviderError(
            "The model service could not return a verified response. Retry later."
        ) from exc
