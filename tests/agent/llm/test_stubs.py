import pytest

from app.agent.llm.anthropic import AnthropicProvider
from app.agent.llm.ollama import OllamaProvider
from app.agent.llm.openai import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_stub_raises():
    provider = OpenAIProvider()
    assert provider.get_model_name() == "gpt-4o"
    assert provider.get_max_tokens() == 128_000

    with pytest.raises(NotImplementedError, match="OpenAIProvider is an architectural stub"):
        await provider.generate([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_anthropic_stub_raises():
    provider = AnthropicProvider()
    assert "claude" in provider.get_model_name()
    assert provider.get_max_tokens() == 200_000

    with pytest.raises(NotImplementedError, match="AnthropicProvider is an architectural stub"):
        await provider.generate([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_ollama_stub_raises():
    provider = OllamaProvider()
    assert "llama" in provider.get_model_name()
    assert provider.get_max_tokens() == 32_768

    with pytest.raises(NotImplementedError, match="OllamaProvider is an architectural stub"):
        await provider.generate([{"role": "user", "content": "hi"}])
