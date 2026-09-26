from enum import Enum
from typing import Any, Callable, List, Optional
from transitions import Machine, MachineError


class ApprovalState(str, Enum):
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    pass


class ApprovalStateMachine:
    """Finite State Machine managing ApprovalRequest lifecycles using the `transitions` library.
    
    Enforces strict transitions:
    - PENDING -> ESCALATED, APPROVED, REJECTED
    - ESCALATED -> ESCALATED (re-escalate to manager), APPROVED, REJECTED
    - APPROVED -> EXECUTED, FAILED
    Terminal/invalid:
    - REJECTED cannot be approved or executed
    - EXECUTED cannot be modified
    - FAILED cannot be executed
    """

    STATES = [s.value for s in ApprovalState]

    TRANSITIONS = [
        # Escalate
        {"trigger": "escalate", "source": [ApprovalState.PENDING.value, ApprovalState.ESCALATED.value], "dest": ApprovalState.ESCALATED.value},
        # Approve
        {"trigger": "approve", "source": [ApprovalState.PENDING.value, ApprovalState.ESCALATED.value], "dest": ApprovalState.APPROVED.value},
        # Reject
        {"trigger": "reject", "source": [ApprovalState.PENDING.value, ApprovalState.ESCALATED.value], "dest": ApprovalState.REJECTED.value},
        # Execute
        {"trigger": "mark_executed", "source": ApprovalState.APPROVED.value, "dest": ApprovalState.EXECUTED.value},
        # Fail
        {"trigger": "mark_failed", "source": ApprovalState.APPROVED.value, "dest": ApprovalState.FAILED.value},
    ]

    def __init__(
        self,
        initial_state: str = ApprovalState.PENDING.value,
        on_transition_callback: Optional[Callable[[str, str], Any]] = None,
    ):
        self.state = initial_state
        self._callback = on_transition_callback
        self.machine = Machine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial=initial_state,
            after_state_change="_on_change",
            send_event=True,
        )

    def _on_change(self, event: Any) -> None:
        if self._callback:
            # event.transition.source -> event.transition.dest
            source = event.transition.source if hasattr(event, "transition") else ""
            dest = self.state
            self._callback(source, dest)

    def transition(self, trigger_name: str) -> str:
        """Attempt a transition by trigger name ('approve', 'reject', 'escalate', 'mark_executed', 'mark_failed')."""
        trigger_fn = getattr(self, trigger_name, None)
        if not trigger_fn or not callable(trigger_fn):
            raise InvalidStateTransitionError(f"Unknown transition trigger: '{trigger_name}'")
        try:
            trigger_fn()
            return self.state
        except MachineError as e:
            raise InvalidStateTransitionError(
                f"Cannot execute '{trigger_name}' from state '{self.state}': {str(e)}"
            ) from e

    def can_transition(self, trigger_name: str) -> bool:
        """Check if transition trigger is valid from current state."""
        check_fn = getattr(self, f"may_{trigger_name}", None)
        if check_fn and callable(check_fn):
            return check_fn()
        return False
