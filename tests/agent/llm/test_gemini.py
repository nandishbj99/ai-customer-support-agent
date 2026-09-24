from unittest.mock import AsyncMock, MagicMock
import pytest
from google.genai import types

from app.agent.llm.gemini import GeminiProvider
from app.agent.llm.types import ToolCall
from app.tools.registry import ToolRegistry


def test_gemini_provider_init():
    provider = GeminiProvider(model="gemini-2.5-flash", api_key="test-key")
    assert provider.get_model_name() == "gemini-2.5-flash"
    assert provider.get_max_tokens() == 1_048_576


def test_gemini_message_conversion():
    provider = GeminiProvider(api_key="test-key")

    messages = [
        {"role": "user", "content": "What is my balance?"},
        {
            "role": "model",
            "content": "Checking your balance...",
            "tool_calls": [ToolCall(id="c1", name="getAccountBalance", arguments={"account_id": "acc_001"})],
        },
        {
            "role": "tool",
            "name": "getAccountBalance",
            "content": {"status": "SUCCESS", "balance_inr": 25000.5},
        },
    ]

    contents = provider._convert_messages(messages)
    assert len(contents) == 3

    # User message
    assert contents[0].role == "user"
    assert contents[0].parts[0].text == "What is my balance?"

    # Model message with text + tool call
    assert contents[1].role == "model"
    assert len(contents[1].parts) == 2
    assert contents[1].parts[0].text == "Checking your balance..."
    assert contents[1].parts[1].function_call.name == "getAccountBalance"

    # Tool response
    assert contents[2].role == "user"
    assert contents[2].parts[0].function_response.name == "getAccountBalance"
    assert contents[2].parts[0].function_response.response == {"status": "SUCCESS", "balance_inr": 25000.5}


def test_gemini_tools_conversion():
    provider = GeminiProvider(api_key="test-key")
    decls = ToolRegistry.get_gemini_function_declarations()
    tools = provider._convert_tools(decls)

    assert tools is not None
    assert len(tools) == 1
    assert len(tools[0].function_declarations) == 13


def test_gemini_normalize_response_text():
    provider = GeminiProvider(api_key="test-key")

    mock_resp = MagicMock(spec=types.GenerateContentResponse)
    mock_resp.text = "Here is your transaction receipt."
    mock_resp.function_calls = None
    mock_resp.candidates = [MagicMock(finish_reason="STOP")]
    mock_resp.usage_metadata = MagicMock(
        prompt_token_count=50, candidates_token_count=20, total_token_count=70
    )

    norm = provider._normalize_response(mock_resp)
    assert norm.text == "Here is your transaction receipt."
    assert not norm.has_tool_calls
    assert norm.finish_reason == "stop"
    assert norm.usage.total_tokens == 70


def test_gemini_normalize_response_function_call():
    provider = GeminiProvider(api_key="test-key")

    fc = MagicMock()
    fc.name = "getTransaction"
    fc.args = {"transaction_id": "tx_001"}
    fc.id = "call_gemini_1"

    mock_resp = MagicMock(spec=types.GenerateContentResponse)
    mock_resp.text = None
    mock_resp.function_calls = [fc]
    mock_resp.candidates = [MagicMock(finish_reason="STOP")]
    mock_resp.usage_metadata = MagicMock(
        prompt_token_count=40, candidates_token_count=15, total_token_count=55
    )

    norm = provider._normalize_response(mock_resp)
    assert norm.has_tool_calls
    assert len(norm.tool_calls) == 1
    assert norm.tool_calls[0].name == "getTransaction"
    assert norm.tool_calls[0].arguments == {"transaction_id": "tx_001"}
    assert norm.finish_reason == "tool_call"


@pytest.mark.asyncio
async def test_gemini_generate_mock_client():
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock()

    mock_resp = MagicMock(spec=types.GenerateContentResponse)
    mock_resp.text = "Hello! How can I help you today?"
    mock_resp.function_calls = None
    mock_resp.candidates = [MagicMock(finish_reason="STOP")]
    mock_resp.usage_metadata = None
    mock_client.aio.models.generate_content.return_value = mock_resp

    provider = GeminiProvider(client=mock_client)
    res = await provider.generate(
        messages=[{"role": "user", "content": "hello"}],
        system_instruction="Be helpful.",
    )

    assert res.text == "Hello! How can I help you today?"
    assert res.finish_reason == "stop"
    mock_client.aio.models.generate_content.assert_called_once()
