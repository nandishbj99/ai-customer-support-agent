import pytest
from app.hitl.rules_engine import ApprovalRulesEngine


@pytest.mark.asyncio
async def test_refund_under_threshold_no_approval():
    engine = ApprovalRulesEngine()
    res = await engine.evaluate(
        tool_name="initiateRefund",
        arguments={"amount_inr": 5000.0, "txn_id": "txn_123"},
        user_tier="standard",
    )
    assert res.requires_approval is False


@pytest.mark.asyncio
async def test_refund_exactly_threshold_no_approval():
    engine = ApprovalRulesEngine()
    # ₹10,000 exact
    res = await engine.evaluate(
        tool_name="initiateRefund",
        arguments={"amount_inr": 10000.0, "txn_id": "txn_123"},
        user_tier="standard",
    )
    assert res.requires_approval is False


@pytest.mark.asyncio
async def test_refund_above_threshold_agent_approval():
    engine = ApprovalRulesEngine()
    # ₹15,000 > ₹10,000
    res = await engine.evaluate(
        tool_name="initiateRefund",
        arguments={"amount_inr": 15000.0, "txn_id": "txn_123"},
        user_tier="standard",
    )
    assert res.requires_approval is True
    assert res.required_role == "agent"
    assert res.priority == 3
    assert res.rule_name == "HIGH_VALUE_REFUND"


@pytest.mark.asyncio
async def test_refund_above_executive_threshold_manager_approval():
    engine = ApprovalRulesEngine()
    # ₹120,000 > ₹100,000 (FR-08 multi-level)
    res = await engine.evaluate(
        tool_name="initiateRefund",
        arguments={"amount_inr": 120000.0, "txn_id": "txn_123"},
        user_tier="standard",
    )
    assert res.requires_approval is True
    assert res.required_role == "manager"
    assert res.priority == 1
    assert res.rule_name == "SUPER_HIGH_VALUE_REFUND"


@pytest.mark.asyncio
async def test_account_freeze_and_closure():
    engine = ApprovalRulesEngine()
    # Freeze
    freeze_res = await engine.evaluate(
        tool_name="freezeAccount",
        arguments={"reason": "Suspicious activity detected"},
    )
    assert freeze_res.requires_approval is True
    assert freeze_res.required_role == "agent"

    # Close
    close_res = await engine.evaluate(
        tool_name="closeAccount",
        arguments={"reason": "Customer requested account closure"},
    )
    assert close_res.requires_approval is True
    assert close_res.required_role == "manager"


@pytest.mark.asyncio
async def test_large_reversal_requires_manager():
    engine = ApprovalRulesEngine()
    res = await engine.evaluate(
        tool_name="reverseTransaction",
        arguments={"amount_inr": 75000.0, "txn_id": "txn_456"},
    )
    assert res.requires_approval is True
    assert res.required_role == "manager"
    assert res.rule_name == "LARGE_TRANSACTION_REVERSAL"


@pytest.mark.asyncio
async def test_fraud_override_requires_manager():
    engine = ApprovalRulesEngine()
    res = await engine.evaluate(
        tool_name="overrideFraudFlag",
        arguments={"txn_id": "txn_999", "justification": "Verified by phone"},
    )
    assert res.requires_approval is True
    assert res.required_role == "manager"
    assert res.rule_name == "FRAUD_FLAG_OVERRIDE"


@pytest.mark.asyncio
async def test_vip_tier_priority_adjustment():
    engine = ApprovalRulesEngine()
    standard_res = await engine.evaluate(
        tool_name="initiateRefund",
        arguments={"amount_inr": 25000.0},
        user_tier="standard",
    )
    vip_res = await engine.evaluate(
        tool_name="initiateRefund",
        arguments={"amount_inr": 25000.0},
        user_tier="vip",
    )
    # VIP should have lower numerical priority (higher urgency) and tighter SLA
    assert vip_res.priority < standard_res.priority
    assert vip_res.sla_minutes < standard_res.sla_minutes
