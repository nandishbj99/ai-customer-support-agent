import pytest
from app.tools.registry import ToolRegistry


def test_registry_registered_tools_count():
    """All 13 fintech tools are registered in ToolRegistry."""
    tools = ToolRegistry.get_registered_tool_names()
    assert len(tools) == 13
    assert "getTransaction" in tools
    assert "getAccount" in tools
    assert "initiateRefund" in tools
    assert "checkFraudStatus" in tools
    assert "searchPolicy" in tools
    assert "escalateToHumanAgent" in tools


def test_gemini_function_declarations_security():
    """Gemini function declarations are generated and user_id is stripped from all schemas."""
    declarations = ToolRegistry.get_gemini_function_declarations()
    assert len(declarations) == 13

    for decl in declarations:
        assert "name" in decl
        assert "description" in decl
        assert "parameters" in decl
        params = decl["parameters"]
        assert params["type"] == "object"
        assert "properties" in params

        # CRITICAL SECURITY TEST: Ensure user_id is NOT in properties or required
        assert "user_id" not in params["properties"], f"Security violation: 'user_id' exposed in {decl['name']} schema!"
        assert "user_id" not in params.get("required", []), f"Security violation: 'user_id' in required for {decl['name']}!"


def test_unknown_tool_schema_lookup():
    """Querying an unregistered tool name raises KeyError."""
    with pytest.raises(KeyError):
        ToolRegistry.get_input_schema("unknownNonExistentTool")
