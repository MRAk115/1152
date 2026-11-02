import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import Settings


class ProviderError(RuntimeError):
    pass


def _request_chat(provider: str, messages: list[dict[str, str]], settings: Settings) -> str:
    if provider == "ollama":
        url = f"{settings.ollama_url}/api/chat"
        model = settings.ollama_model
        api_key = "ollama"
        request_body = {"model": model, "messages": messages, "stream": False}
        if model.startswith("qwen3.5:"):
            request_body.update(think=False, options={"num_predict": 512})
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ProviderError("JARVIS_OPENAI_API_KEY is not set.")
        url = "https://api.openai.com/v1/chat/completions"
        model = settings.openai_model
        api_key = settings.openai_api_key
        request_body = {"model": model, "messages": messages}
    else:
        raise ProviderError(f"Unsupported provider: {provider}")

    payload = json.dumps(request_body).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ProviderError(f"{provider} returned HTTP {error.code}: {detail[:500]}") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ProviderError(f"{provider} request failed: {error}") from error

    try:
        if provider == "ollama":
            content = result["message"]["content"]
        else:
            content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError(f"{provider} returned an unexpected chat response.") from error
    if not isinstance(content, str) or not content.strip():
        raise ProviderError(f"{provider} returned an empty response.")
    return content.strip()


def chat(messages: list[dict[str, str]], settings: Settings) -> tuple[str, str, bool]:
    try:
        return _request_chat(settings.provider, messages, settings), settings.provider, False
    except ProviderError as primary_error:
        fallback = settings.fallback_provider
        if fallback == "none" or fallback == settings.provider:
            raise
        try:
            return _request_chat(fallback, messages, settings), fallback, True
        except ProviderError as fallback_error:
            raise ProviderError(
                f"Primary provider failed ({primary_error}); fallback provider failed ({fallback_error})."
            ) from fallback_error
