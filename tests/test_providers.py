"""Anthropic, OpenAI and Gemini providers against fake SDK modules: no network, no key, no cost."""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace as NS

import pytest


class RateLimited(Exception):
    pass


# ── fake openai SDK ──────────────────────────────────────────────────────────

class FakeCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)  # exceptions to raise, then the answer
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if kwargs.get("stream"):
            return iter(
                NS(choices=[NS(delta=NS(content=c))] if c is not ... else [])
                for c in outcome
            )
        return NS(choices=[NS(message=NS(content=outcome))])


@pytest.fixture
def openai_sdk(monkeypatch):
    sdk = types.ModuleType("openai")
    sdk.made = []

    def OpenAI(**kwargs):
        client = NS(kwargs=kwargs, chat=NS(completions=FakeCompletions(sdk.outcomes)))
        sdk.made.append(client)
        return client

    sdk.OpenAI = OpenAI
    sdk.outcomes = ["ok"]
    monkeypatch.setitem(sys.modules, "openai", sdk)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("time.sleep", lambda s: sdk.__dict__.setdefault("slept", []).append(s))
    return sdk


def _openai(model=None):
    from agora.providers.openai import OpenAIProvider

    return OpenAIProvider(model=model)


def test_openai_without_a_key_says_which_variable_is_missing(openai_sdk, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(EnvironmentError, match="OPENAI_API_KEY not set"):
        _openai()


@pytest.mark.parametrize(
    "model, api_model",
    [(None, "gpt-6.2-sol"), ("astra", "gpt-6.2-astra"), ("LUNA", "gpt-6-luna"), ("gpt4o-mini", "gpt-4o-mini"), ("o1", "o1")],
)
def test_openai_resolves_aliases_and_passes_unknown_names_through(openai_sdk, model, api_model):
    provider = _openai(model)
    assert provider.model == api_model
    assert provider.display_name == (model or "sol")
    assert openai_sdk.made[0].kwargs == {"api_key": "test-key"}


def test_openai_complete_puts_the_system_prompt_first(openai_sdk):
    provider = _openai()
    answer = provider.complete("be brief", [{"role": "user", "content": "hi"}], max_tokens=77)
    assert answer == "ok"
    (call,) = provider.client.chat.completions.calls
    assert call == {
        "model": "gpt-6.2-sol",
        "max_completion_tokens": 77,
        "messages": [{"role": "system", "content": "be brief"}, {"role": "user", "content": "hi"}],
    }


def test_openai_retries_rate_limits_twice_with_backoff(openai_sdk):
    openai_sdk.outcomes = [RateLimited("Rate limit reached"), RateLimited("rate limit"), "third time"]
    provider = _openai()
    assert provider.complete("s", []) == "third time"
    assert len(provider.client.chat.completions.calls) == 3
    assert openai_sdk.slept == [1, 2]


def test_openai_gives_up_after_three_rate_limits(openai_sdk):
    openai_sdk.outcomes = [RateLimited("rate")] * 3
    provider = _openai()
    with pytest.raises(RateLimited):
        provider.complete("s", [])
    assert len(provider.client.chat.completions.calls) == 3


def test_openai_does_not_retry_other_errors(openai_sdk):
    openai_sdk.outcomes = [ValueError("invalid model")]
    provider = _openai()
    with pytest.raises(ValueError, match="invalid model"):
        provider.complete("s", [])
    assert len(provider.client.chat.completions.calls) == 1
    assert not hasattr(openai_sdk, "slept")


def test_openai_stream_yields_text_and_skips_empty_chunks(openai_sdk):
    openai_sdk.outcomes = [["Hel", None, ..., "lo", ""]]
    provider = _openai()
    assert list(provider.stream("s", [{"role": "user", "content": "hi"}])) == ["Hel", "lo"]
    (call,) = provider.client.chat.completions.calls
    assert call["stream"] is True
    assert call["max_completion_tokens"] == 1024 and "max_tokens" not in call
    assert call["messages"][0] == {"role": "system", "content": "s"}


# ── fake google.genai SDK (Google Gen AI SDK) ────────────────────────────────

class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.calls = []

    def _next(self, stream, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config, "stream": stream})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def generate_content(self, *, model, contents, config):
        return NS(text=self._next(False, model, contents, config))

    def generate_content_stream(self, *, model, contents, config):
        return iter(NS(text=t) for t in self._next(True, model, contents, config))


class ApiError(Exception):
    """Shaped like google.genai.errors.APIError: an HTTP status in .code."""

    def __init__(self, code, message):
        super().__init__(f"{code} {message}")
        self.code = code


@pytest.fixture
def genai_sdk(monkeypatch):
    sdk = types.ModuleType("google.genai")
    sdk.outcomes = ["ok"]
    sdk.clients = []

    def client(**kw):
        made = NS(kwargs=kw, models=FakeModels(sdk.outcomes))
        sdk.clients.append(made)
        return made

    sdk.Client = client
    google = types.ModuleType("google")
    google.genai = sdk
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", sdk)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr("time.sleep", lambda s: sdk.__dict__.setdefault("slept", []).append(s))
    return sdk


def _gemini(model=None):
    from agora.providers.gemini import GeminiProvider

    return GeminiProvider(model=model)


def test_gemini_without_a_key_says_which_variable_is_missing(genai_sdk, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY")
    with pytest.raises(EnvironmentError, match="GOOGLE_API_KEY not set"):
        _gemini()
    assert genai_sdk.clients == []


@pytest.mark.parametrize(
    "model, api_model",
    [(None, "gemini-3.8-flash"), ("Pro", "gemini-3.1-pro-preview"), ("gemini-4-neon", "gemini-4-neon")],
)
def test_gemini_passes_the_key_and_resolves_aliases(genai_sdk, model, api_model):
    provider = _gemini(model)
    assert [c.kwargs for c in genai_sdk.clients] == [{"api_key": "test-key"}]
    provider.complete("s", [])
    assert provider.client.models.calls[0]["model"] == api_model


def test_gemini_folds_system_and_messages_into_one_prompt(genai_sdk):
    provider = _gemini()
    answer = provider.complete(
        "be brief",
        [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        max_tokens=50,
    )
    assert answer == "ok"
    (call,) = provider.client.models.calls
    assert call["contents"] == "be brief\n\n\n\nUSER: hi\n\nASSISTANT: hello"
    assert call["config"] == {"max_output_tokens": 50}
    assert call["stream"] is False


@pytest.mark.parametrize(
    "error",
    [
        RateLimited("Resource has been exhausted (quota)"),
        RateLimited("Rate limit"),
        ApiError(429, "RESOURCE_EXHAUSTED"),
    ],
)
def test_gemini_retries_quota_and_rate_errors(genai_sdk, error):
    genai_sdk.outcomes[:] = [error, "later"]
    provider = _gemini()
    assert provider.complete("s", []) == "later"
    assert genai_sdk.slept == [1]


def test_gemini_does_not_retry_other_errors(genai_sdk):
    genai_sdk.outcomes[:] = [ApiError(400, "INVALID_ARGUMENT")]
    provider = _gemini()
    with pytest.raises(ApiError, match="INVALID_ARGUMENT"):
        provider.complete("s", [])
    assert len(provider.client.models.calls) == 1


def test_gemini_without_text_raises_instead_of_returning_none(genai_sdk):
    genai_sdk.outcomes[:] = [None]
    provider = _gemini()
    with pytest.raises(ValueError, match="returned no text"):
        provider.complete("s", [])


def test_gemini_stream_yields_text_and_skips_empty_chunks(genai_sdk):
    genai_sdk.outcomes[:] = [["Hel", "", None, "lo"]]
    provider = _gemini()
    assert list(provider.stream("s", [])) == ["Hel", "lo"]
    assert provider.client.models.calls[0]["stream"] is True


# ── fake anthropic SDK ───────────────────────────────────────────────────────

@pytest.fixture
def anthropic_sdk(monkeypatch):
    sdk = types.ModuleType("anthropic")
    sdk.calls = []

    def create(**kwargs):
        sdk.calls.append(kwargs)
        return NS(content=[NS(text="ok")])

    sdk.Anthropic = lambda **kw: NS(kwargs=kw, messages=NS(create=create))
    monkeypatch.setitem(sys.modules, "anthropic", sdk)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    return sdk


@pytest.mark.parametrize(
    "model, api_model",
    [
        (None, "claude-sonnet-5-5"),
        ("Haiku", "claude-haiku-5-5"),
        ("opus", "claude-opus-5-5"),
        ("claude-fable-5-2", "claude-fable-5-2"),
    ],
)
def test_anthropic_aliases_resolve_to_current_model_ids(anthropic_sdk, model, api_model):
    from agora.providers.anthropic import AnthropicProvider

    provider = AnthropicProvider(model=model)
    assert provider.complete("s", [{"role": "user", "content": "hi"}]) == "ok"
    assert anthropic_sdk.calls[0]["model"] == api_model
