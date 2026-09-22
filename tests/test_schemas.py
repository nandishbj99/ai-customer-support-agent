import pytest
from pydantic import ValidationError

from app.tools.schemas import (
    CheckFraudStatusInput,
    CreateSupportTicketInput,
    EscalateToHumanAgentInput,
    GetAccountBalanceInput,
    GetAccountInput,
    GetCustomerProfileInput,
    GetPaymentStatusInput,
    GetRefundStatusInput,
    GetTransactionHistoryInput,
    GetTransactionInput,
    InitiateRefundInput,
    SearchPolicyInput,
    SendNotificationInput,
    ToolResult,
)


def test_tc01_valid_get_transaction_input():
    """TC-01: Valid getTransaction input validates successfully."""
    inp = GetTransactionInput(txn_id="00000000-0000-0000-0000-000000000201", user_id="user_123")
    assert inp.txn_id == "00000000-0000-0000-0000-000000000201"
    assert inp.user_id == "user_123"


def test_tc02_missing_required_fields():
    """TC-02: Missing required txn_id and user_id raises ValidationError."""
    with pytest.raises(ValidationError):
        GetTransactionInput()  # type: ignore

    with pytest.raises(ValidationError):
        GetTransactionInput(txn_id="", user_id="user_1")


def test_tc03_negative_or_zero_refund_amount():
    """TC-03: Zero or negative refund amount in initiateRefund raises error."""
    with pytest.raises(ValidationError):
        InitiateRefundInput(
            txn_id="txn_123",
            user_id="user_123",
            amount_inr=-50.0,
            reason="Defective item delivered",
        )

    with pytest.raises(ValidationError):
        InitiateRefundInput(
            txn_id="txn_123",
            user_id="user_123",
            amount_inr=0.0,
            reason="Defective item delivered",
        )


def test_tc04_model_json_schema_for_gemini():
    """TC-04: .model_json_schema() generates valid JSON Schema for all tools."""
    schemas = [
        GetTransactionInput.model_json_schema(),
        GetAccountInput.model_json_schema(),
        GetAccountBalanceInput.model_json_schema(),
        GetCustomerProfileInput.model_json_schema(),
        GetPaymentStatusInput.model_json_schema(),
        CheckFraudStatusInput.model_json_schema(),
        GetRefundStatusInput.model_json_schema(),
        GetTransactionHistoryInput.model_json_schema(),
        InitiateRefundInput.model_json_schema(),
        CreateSupportTicketInput.model_json_schema(),
        SendNotificationInput.model_json_schema(),
        SearchPolicyInput.model_json_schema(),
        EscalateToHumanAgentInput.model_json_schema(),
    ]
    for schema in schemas:
        assert "properties" in schema
        assert "type" in schema
        assert schema["type"] == "object"


def test_tool_result_helpers():
    """Verify ToolResult.ok and ToolResult.fail helper constructors."""
    ok_res = ToolResult.ok({"balance_inr": 1500.0})
    assert ok_res.success is True
    assert ok_res.data == {"balance_inr": 1500.0}
    assert ok_res.error is None

    err_res = ToolResult.fail(code="TXN_NOT_FOUND", message="Transaction does not exist")
    assert err_res.success is False
    assert err_res.data is None
    assert err_res.error is not None
    assert err_res.error.code == "TXN_NOT_FOUND"
    assert err_res.error.message == "Transaction does not exist"
