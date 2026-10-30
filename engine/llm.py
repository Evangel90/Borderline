"""Structured chat clients for local Ollama and remote OpenAI-compatible APIs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ValidationError


class OllamaError(RuntimeError):
    """Raised when the configured model cannot produce a valid response."""


def _load_project_env() -> None:
    """Load simple KEY=value entries from the repo-root .env without overriding the shell."""
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


class OllamaChatClient:
    def __init__(self) -> None:
        _load_project_env()
        self.base_url = os.environ.get("BORDERLINE_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        self.model = os.environ.get("BORDERLINE_LLM_MODEL", "qwen3:8b")
        self.timeout = float(os.environ.get("BORDERLINE_LLM_TIMEOUT", "180"))

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        output_schema: dict | None = None,
    ) -> BaseModel:
        """Return one Pydantic-validated response using Ollama JSON-schema mode."""
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": output_schema or schema.model_json_schema(),
            "stream": False,
            "think": False,
            "options": {"temperature": 0},
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaError(
                f"Ollama returned HTTP {exc.code} for model {self.model}: {detail}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise OllamaError(
                f"Cannot reach Ollama at {self.base_url}. Start it with `ollama serve`; "
                f"then install the configured model with `ollama pull {self.model}`. ({exc})"
            ) from exc
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise OllamaError(f"Ollama returned an invalid chat response: {exc}") from exc

        try:
            content = result["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise OllamaError("Ollama response is missing message.content") from exc
        try:
            parsed = json.loads(content)
            return schema.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise OllamaError(f"Model response did not match {schema.__name__}: {exc}") from exc


class OpenRouterChatClient:
    """OpenRouter client using its free-model router and JSON-schema outputs."""

    def __init__(self) -> None:
        _load_project_env()
        self.base_url = os.environ.get(
            "BORDERLINE_OPENROUTER_URL", "https://openrouter.ai/api/v1"
        ).rstrip("/")
        self.model = os.environ.get("BORDERLINE_LLM_MODEL", "openrouter/free")
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.timeout = float(os.environ.get("BORDERLINE_LLM_TIMEOUT", "180"))
        if not self.api_key:
            raise OllamaError(
                "OPENROUTER_API_KEY is required when BORDERLINE_LLM_PROVIDER=openrouter. "
                "Create a free OpenRouter key and export it in your shell."
            )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        output_schema: dict | None = None,
    ) -> BaseModel:
        """Return one Pydantic-validated response using JSON-schema mode."""
        schema_name = schema.__name__.lower()
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": output_schema or schema.model_json_schema(),
                },
            },
            "temperature": 0,
            "max_tokens": 4096,
            "reasoning": {"max_tokens": 512, "exclude": True},
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/Evangel90/Borderline",
                "X-Title": "Borderline Hackathon Drill",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaError(
                f"OpenRouter returned HTTP {exc.code} for model {self.model}: {detail}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise OllamaError(f"Cannot reach OpenRouter at {self.base_url}: {exc}") from exc
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise OllamaError(f"OpenRouter returned an invalid chat response: {exc}") from exc

        try:
            choice = result["choices"][0]
            message = choice["message"]
            content = message.get("content")
            self.model = result.get("model", self.model)
            if content is None:
                raise OllamaError(
                    "OpenRouter returned no final content "
                    f"(model={self.model}, finish_reason={choice.get('finish_reason')}, "
                    f"refusal={bool(message.get('refusal'))})."
                )
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "") for item in content if isinstance(item, dict)
                )
            parsed = json.loads(content)
            return schema.model_validate(parsed)
        except OllamaError:
            raise
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            raise OllamaError(
                f"OpenRouter response did not match {schema.__name__}: {exc}"
            ) from exc


def create_chat_client() -> OllamaChatClient | OpenRouterChatClient:
    _load_project_env()
    provider = os.environ.get("BORDERLINE_LLM_PROVIDER", "openrouter").lower()
    if provider == "openrouter":
        return OpenRouterChatClient()
    if provider == "ollama":
        return OllamaChatClient()
    raise OllamaError(
        f"Unsupported BORDERLINE_LLM_PROVIDER '{provider}'. Use 'openrouter' or 'ollama'."
    )
