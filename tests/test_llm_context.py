import json

import pytest

from engine.llm import OllamaChatClient, OllamaError


def client(monkeypatch, num_ctx="16384"):
    monkeypatch.setenv("BORDERLINE_OLLAMA_NUM_CTX", num_ctx)
    return OllamaChatClient()


def test_ollama_requests_an_explicit_context_window(monkeypatch):
    sent = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps({"message": {"content": json.dumps({"ok": True})}}).encode()

    def fake_urlopen(request, timeout):
        sent.update(json.loads(request.data))
        return Response()

    monkeypatch.setattr("engine.llm.urlopen", fake_urlopen)
    from pydantic import BaseModel

    class Out(BaseModel):
        ok: bool

    client(monkeypatch, "12000").generate("system", "user", Out)
    assert sent["options"]["num_ctx"] == 12000


def test_prompt_too_large_for_the_window_is_refused_not_truncated(monkeypatch):
    llm = client(monkeypatch, "4096")
    with pytest.raises(OllamaError, match="does not fit"):
        llm.check_prompt_fits("s", "x" * 28000, {})
    client(monkeypatch, "16384").check_prompt_fits("s", "x" * 28000, {})
