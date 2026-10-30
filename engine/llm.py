"""Small client for structured local Ollama chat completions."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ValidationError


class OllamaError(RuntimeError):
    """Raised when the configured local model cannot produce a valid response."""


class OllamaChatClient:
    def __init__(self) -> None:
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
