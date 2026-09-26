import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.core.models import ApprovalRule

logger = structlog.get_logger()


@dataclass
class RuleEvaluationResult:
    """Result of evaluating an operation against approval rules."""
    requires_approval: bool
    rule_name: Optional[str] = None
    required_role: str = "agent"  # "agent", "manager", "admin"
    priority: int = 5  # 1 (highest/critical) to 10 (lowest)
    sla_minutes: int = 30
    reason: Optional[str] = None
    amount_paise: Optional[int] = None

    @property
    def sla_expires_at(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(minutes=self.sla_minutes)


class ApprovalRulesEngine:
    """Evaluates proposed tool operations against business safety rules and threshold policies."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    async def evaluate(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_tier: str = "standard",
        context: Optional[Dict[str, Any]] = None,
    ) -> RuleEvaluationResult:
        """Evaluate a tool invocation against both dynamic DB rules and default hardcoded safety policies."""
        args = arguments or {}

        # 1. First check dynamic DB rules if session is available
        if self.db is not None:
            try:
                db_result = await self._evaluate_db_rules(tool_name, args, user_tier)
                if db_result and db_result.requires_approval:
                    return self._adjust_priority_for_tier(db_result, user_tier)
            except Exception as e:
                logger.warn("db_rules_evaluation_failed_falling_back_to_defaults", error=str(e))

        # 2. Evaluate built-in compliance policies (FR-02, FR-08)
        default_result = self._evaluate_default_rules(tool_name, args, user_tier)
        return self._adjust_priority_for_tier(default_result, user_tier)

    def _evaluate_default_rules(
        self,
        tool_name: str,
        args: Dict[str, Any],
        user_tier: str,
    ) -> RuleEvaluationResult:
        """Standard hardcoded fintech safety thresholds."""

        # Rule 1: High-value refunds
        if tool_name == "initiateRefund":
            amount_inr = float(args.get("amount_inr", 0.0) or 0.0)
            amount_paise = int(round(amount_inr * 100))

            # Tier 2: Multi-level / Manager approval for refunds > ₹1,00,000 (FR-08)
            if amount_paise > 10_000_000:  # ₹100,000
                return RuleEvaluationResult(
                    requires_approval=True,
                    rule_name="SUPER_HIGH_VALUE_REFUND",
                    required_role="manager",
                    priority=1,
                    sla_minutes=15,
                    reason=f"Refund of ₹{amount_inr:,.2f} exceeds executive threshold (₹100,000) and requires Manager sign-off.",
                    amount_paise=amount_paise,
                )

            # Tier 1: Agent / Supervisor approval for refunds > ₹10,000 (FR-02)
            if amount_paise > 1_000_000:  # ₹10,000
                return RuleEvaluationResult(
                    requires_approval=True,
                    rule_name="HIGH_VALUE_REFUND",
                    required_role="agent",
                    priority=3,
                    sla_minutes=30,
                    reason=f"Refund of ₹{amount_inr:,.2f} exceeds automated threshold (₹10,000) and requires human review.",
                    amount_paise=amount_paise,
                )

        # Rule 2: Account Freeze / Closure Operations
        if tool_name in ("freezeAccount", "closeAccount", "updateAccountStatus"):
            new_status = str(args.get("status", "")).lower()
            if tool_name in ("freezeAccount", "closeAccount") or new_status in ("frozen", "closed"):
                return RuleEvaluationResult(
                    requires_approval=True,
                    rule_name="ACCOUNT_FREEZE_OR_CLOSURE",
                    required_role="manager" if tool_name == "closeAccount" or new_status == "closed" else "agent",
                    priority=2,
                    sla_minutes=20,
                    reason=f"Account status change to '{tool_name}' requires operational approval.",
                )

        # Rule 3: Large Transaction Reversals (> ₹50,000)
        if tool_name in ("reverseTransaction", "initiateReversal"):
            amount_inr = float(args.get("amount_inr", 0.0) or 0.0)
            amount_paise = int(round(amount_inr * 100))
            if amount_paise > 5_000_000 or amount_inr > 50_000.0:  # ₹50,000
                return RuleEvaluationResult(
                    requires_approval=True,
                    rule_name="LARGE_TRANSACTION_REVERSAL",
                    required_role="manager",
                    priority=2,
                    sla_minutes=20,
                    reason=f"Reversal of ₹{amount_inr:,.2f} exceeds ₹50,000 threshold and requires Manager approval.",
                    amount_paise=amount_paise,
                )

        # Rule 4: Fraud Flag Override
        if tool_name in ("overrideFraudFlag", "clearFraudAlert"):
            return RuleEvaluationResult(
                requires_approval=True,
                rule_name="FRAUD_FLAG_OVERRIDE",
                required_role="manager",
                priority=1,
                sla_minutes=15,
                reason="Overriding an active automated fraud flag requires Senior Fraud Manager authorization.",
            )

        # Rule 5: Bulk operations
        if tool_name in ("bulkRefund", "bulkAccountUpdate"):
            return RuleEvaluationResult(
                requires_approval=True,
                rule_name="BULK_OPERATION",
                required_role="manager",
                priority=2,
                sla_minutes=30,
                reason="Bulk operational actions affecting multiple accounts require supervisory approval.",
            )

        # No approval required for safe read/standard operations
        return RuleEvaluationResult(requires_approval=False)

    async def _evaluate_db_rules(
        self,
        tool_name: str,
        args: Dict[str, Any],
        user_tier: str,
    ) -> Optional[RuleEvaluationResult]:
        """Check active DB rules ordered by priority."""
        if not self.db:
            return None

        stmt = (
            select(ApprovalRule)
            .where(ApprovalRule.is_active == True)
            .where((ApprovalRule.tool_name == tool_name) | (ApprovalRule.tool_name == "*"))
            .order_by(ApprovalRule.priority.asc())
        )
        result = await self.db.execute(stmt)
        rules = result.scalars().all()

        for rule in rules:
            if rule.condition_type == "always":
                return RuleEvaluationResult(
                    requires_approval=True,
                    rule_name=rule.rule_name,
                    required_role=rule.required_role,
                    priority=int(rule.priority),
                    reason=f"Triggered rule '{rule.rule_name}' (always requires approval).",
                )

            elif rule.condition_type == "amount_threshold":
                amount_inr = float(args.get("amount_inr", 0.0) or 0.0)
                amount_paise = int(round(amount_inr * 100))
                if rule.threshold_amount_paise and amount_paise > rule.threshold_amount_paise:
                    return RuleEvaluationResult(
                        requires_approval=True,
                        rule_name=rule.rule_name,
                        required_role=rule.required_role,
                        priority=int(rule.priority),
                        amount_paise=amount_paise,
                        reason=f"Amount ₹{amount_inr:,.2f} exceeds threshold ₹{rule.threshold_amount_paise / 100:,.2f} for rule '{rule.rule_name}'.",
                    )

        return None

    def _adjust_priority_for_tier(
        self, result: RuleEvaluationResult, user_tier: str
    ) -> RuleEvaluationResult:
        """Bump priority and tighten SLA for VIP or premium customers."""
        if not result.requires_approval:
            return result

        tier = (user_tier or "").lower()
        if tier == "vip":
            # VIP customers get +2 priority bump (lower number = higher priority, min 1)
            result.priority = max(1, result.priority - 2)
            result.sla_minutes = max(10, result.sla_minutes // 2)
        elif tier == "premium":
            result.priority = max(1, result.priority - 1)
            result.sla_minutes = max(15, int(result.sla_minutes * 0.75))

        return result
