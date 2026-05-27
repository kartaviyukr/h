import json

import httpx

from app.core.config import settings


class DeepSeekError(Exception):
    pass


def generate_menu_json(system_prompt: str, user_prompt: str) -> dict:
    """Call DeepSeek chat completions and return the parsed JSON object.

    Raises DeepSeekError on configuration, network, HTTP or parsing failures.
    """
    if not settings.deepseek_api_key:
        raise DeepSeekError("DeepSeek API key is not configured")

    url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
    body = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {settings.deepseek_api_key}"}

    last_exc: Exception | None = None
    for _ in range(2):
        try:
            with httpx.Client(timeout=settings.deepseek_timeout_s) as client:
                response = client.post(url, json=body, headers=headers)
            if response.status_code >= 500:
                last_exc = DeepSeekError(f"DeepSeek server error {response.status_code}")
                continue
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
            last_exc = exc
            continue
    raise DeepSeekError(f"DeepSeek request failed: {last_exc}")
