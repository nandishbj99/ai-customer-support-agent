import pytest
from app.hitl.state_machine import (
    ApprovalState,
    ApprovalStateMachine,
    InvalidStateTransitionError,
)


def test_initial_state_pending():
    sm = ApprovalStateMachine()
    assert sm.state == ApprovalState.PENDING.value
    assert sm.can_transition("approve") is True
    assert sm.can_transition("reject") is True
    assert sm.can_transition("escalate") is True
    assert sm.can_transition("mark_executed") is False


def test_valid_approval_and_execution_flow():
    sm = ApprovalStateMachine()
    assert sm.transition("approve") == ApprovalState.APPROVED.value
    assert sm.can_transition("mark_executed") is True
    assert sm.can_transition("mark_failed") is True
    assert sm.transition("mark_executed") == ApprovalState.EXECUTED.value
    # Executed is terminal
    assert sm.can_transition("approve") is False
    assert sm.can_transition("reject") is False


def test_valid_approval_and_failure_flow():
    sm = ApprovalStateMachine()
    sm.transition("approve")
    assert sm.transition("mark_failed") == ApprovalState.FAILED.value
    # Failed is terminal
    assert sm.can_transition("mark_executed") is False


def test_valid_rejection_flow():
    sm = ApprovalStateMachine()
    assert sm.transition("reject") == ApprovalState.REJECTED.value
    # Rejected is terminal
    assert sm.can_transition("approve") is False
    assert sm.can_transition("mark_executed") is False
    with pytest.raises(InvalidStateTransitionError):
        sm.transition("approve")


def test_valid_escalation_then_approval():
    sm = ApprovalStateMachine()
    assert sm.transition("escalate") == ApprovalState.ESCALATED.value
    # Escalated can be re-escalated (e.g. tier 1 to tier 2)
    assert sm.transition("escalate") == ApprovalState.ESCALATED.value
    # Escalated can be approved
    assert sm.transition("approve") == ApprovalState.APPROVED.value
    assert sm.transition("mark_executed") == ApprovalState.EXECUTED.value


def test_invalid_direct_execution_from_pending():
    sm = ApprovalStateMachine()
    with pytest.raises(InvalidStateTransitionError):
        sm.transition("mark_executed")


def test_transition_callback():
    changes = []

    def callback(source, dest):
        changes.append((source, dest))

    sm = ApprovalStateMachine(on_transition_callback=callback)
    sm.transition("approve")
    sm.transition("mark_executed")

    assert len(changes) == 2
    assert changes[0] == (ApprovalState.PENDING.value, ApprovalState.APPROVED.value)
    assert changes[1] == (ApprovalState.APPROVED.value, ApprovalState.EXECUTED.value)
