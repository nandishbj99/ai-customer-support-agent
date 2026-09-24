import pytest

from app.agent.llm.base import LLMProviderBase
from app.agent.llm.factory import LLMProviderFactory
from app.agent.llm.gemini import GeminiProvider
from app.agent.llm.mock import MockLLMProvider
from app.agent.llm.openai import OpenAIProvider
from app.agent.llm.anthropic import AnthropicProvider
from app.agent.llm.ollama import OllamaProvider


def test_factory_creates_gemini_by_default(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    provider = LLMProviderFactory.create("gemini")
    assert isinstance(provider, GeminiProvider)
    assert provider.get_model_name() == "gemini-2.5-flash"


def test_factory_creates_mock():
    provider = LLMProviderFactory.create("mock")
    assert isinstance(provider, MockLLMProvider)
    assert provider.get_model_name() == "mock-model"


def test_factory_creates_stubs():
    openai = LLMProviderFactory.create("openai")
    assert isinstance(openai, OpenAIProvider)

    anthropic = LLMProviderFactory.create("anthropic")
    assert isinstance(anthropic, AnthropicProvider)

    ollama = LLMProviderFactory.create("ollama")
    assert isinstance(ollama, OllamaProvider)


def test_factory_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown LLM provider 'unknown'"):
        LLMProviderFactory.create("unknown")


def test_factory_custom_registration():
    class CustomProvider(LLMProviderBase):
        async def generate(self, *args, **kwargs):
            pass
        async def generate_stream(self, *args, **kwargs):
            pass
        def get_model_name(self) -> str:
            return "custom-v1"
        def get_max_tokens(self) -> int:
            return 4096

    LLMProviderFactory.register_provider("custom", CustomProvider)
    provider = LLMProviderFactory.create("custom")
    assert isinstance(provider, CustomProvider)
    assert provider.get_model_name() == "custom-v1"
