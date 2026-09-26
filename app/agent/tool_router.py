import hashlib
from typing import Any, Dict, Optional
from pydantic import ValidationError

from app.tools.registry import ToolRegistry
from app.tools.schemas import ToolResult


class ToolRouter:
    """Dispatches tool calls, enforces session-injected user_id, handles idempotency and HITL interception."""

    def __init__(
        self,
        services: Dict[str, Any],
        approval_service: Optional[Any] = None,
        rules_engine: Optional[Any] = None,
    ):
        self.services = services
        self.approval_service = approval_service
        self.rules_engine = rules_engine

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_user_id: str,
        session_id: Optional[str] = None,
        bypass_hitl: bool = False,
    ) -> ToolResult:
        # Check unknown tool (TC-18)
        if tool_name not in ToolRegistry.get_registered_tool_names():
            return ToolResult.fail(
                "UNKNOWN_TOOL",
                f"Tool '{tool_name}' is not recognized by the agent orchestrator.",
            )

        # SECURITY RULE: Invalidate/override any LLM-provided user_id with verified session_user_id
        args = dict(arguments or {})
        args["user_id"] = session_user_id

        # HITL INTERCEPTION: Check if operation requires human operator authorization
        if not bypass_hitl and (self.approval_service or self.rules_engine):
            from app.hitl.rules_engine import ApprovalRulesEngine
            engine = self.rules_engine or (self.approval_service.rules_engine if hasattr(self.approval_service, "rules_engine") else ApprovalRulesEngine())
            eval_res = await engine.evaluate(
                tool_name=tool_name,
                arguments=args,
                context={"session_id": session_id},
            )
            if eval_res.requires_approval:
                approval_id = None
                if self.approval_service:
                    req = await self.approval_service.create_request(
                        session_id=session_id or "default_session",
                        user_id=session_user_id,
                        tool_name=tool_name,
                        tool_arguments=args,
                        context={"reasoning": eval_res.reason},
                        evaluation=eval_res,
                    )
                    approval_id = str(req.id)
                else:
                    import uuid
                    approval_id = f"appr_{uuid.uuid4().hex[:12]}"

                return ToolResult.ok(
                    {
                        "status": "pending_approval",
                        "requires_hitl": True,
                        "approval_id": approval_id,
                        "tool_name": tool_name,
                        "required_role": eval_res.required_role,
                        "priority": eval_res.priority,
                        "message": eval_res.reason or f"Operation '{tool_name}' requires supervisor authorization.",
                    }
                )

        # Auto-generate idempotency key for mutations if omitted
        if tool_name == "initiateRefund" and not args.get("idempotency_key"):
            s_id = session_id or "default_session"
            t_id = args.get("txn_id", "")
            amt = args.get("amount_inr", 0)
            raw = f"{s_id}_{t_id}_{amt}"
            args["idempotency_key"] = f"idem_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

        # Validate arguments against Pydantic schema
        schema_cls = ToolRegistry.get_input_schema(tool_name)
        try:
            parsed = schema_cls(**args)
        except ValidationError as e:
            return ToolResult.fail(
                "INVALID_ARGUMENTS",
                f"Arguments for tool '{tool_name}' failed validation: {str(e)}",
                {"validation_errors": e.errors()},
            )

        # Dispatch to respective service handler (TC-17)
        try:
            if tool_name == "getTransaction":
                return await self.services["transaction"].get_transaction(
                    txn_id=parsed.txn_id, user_id=parsed.user_id
                )
            elif tool_name == "getTransactionHistory":
                return await self.services["transaction"].get_transaction_history(
                    user_id=parsed.user_id,
                    limit=parsed.limit,
                    offset=parsed.offset,
                    status=parsed.status,
                )
            elif tool_name == "getAccount":
                return await self.services["account"].get_account(user_id=parsed.user_id)
            elif tool_name == "getAccountBalance":
                return await self.services["account"].get_account_balance(user_id=parsed.user_id)
            elif tool_name == "getCustomerProfile":
                return await self.services["account"].get_customer_profile(user_id=parsed.user_id)
            elif tool_name == "getPaymentStatus":
                return await self.services["payment"].get_payment_status(
                    user_id=parsed.user_id,
                    payment_id=parsed.payment_id,
                    txn_id=parsed.txn_id,
                )
            elif tool_name == "checkFraudStatus":
                return await self.services["fraud"].check_fraud_status(
                    txn_id=parsed.txn_id, user_id=parsed.user_id
                )
            elif tool_name == "getRefundStatus":
                return await self.services["refund"].get_refund_status(
                    user_id=parsed.user_id,
                    refund_id=parsed.refund_id,
                    txn_id=parsed.txn_id,
                )
            elif tool_name == "initiateRefund":
                return await self.services["refund"].initiate_refund(
                    txn_id=parsed.txn_id,
                    user_id=parsed.user_id,
                    amount_inr=parsed.amount_inr,
                    reason=parsed.reason,
                    idempotency_key=parsed.idempotency_key,
                )
            elif tool_name == "createSupportTicket":
                return await self.services["ticket"].create_support_ticket(
                    user_id=parsed.user_id,
                    category=parsed.category,
                    description=parsed.description,
                    priority=parsed.priority,
                )
            elif tool_name == "sendNotification":
                return await self.services["notification"].send_notification(
                    user_id=parsed.user_id,
                    channel=parsed.channel,
                    message=parsed.message,
                )
            elif tool_name == "escalateToHumanAgent":
                return await self.services["escalation"].escalate_to_human_agent(
                    user_id=parsed.user_id,
                    reason=parsed.reason,
                    conversation_summary=parsed.conversation_summary,
                    priority=parsed.priority,
                )
            elif tool_name == "searchPolicy":
                if "policy" in self.services:
                    return await self.services["policy"].search_policy(
                        query=parsed.query,
                        category=parsed.category,
                    )
                return ToolResult.ok({
                    "query": parsed.query,
                    "category": parsed.category,
                    "results": [],
                })
            else:
                return ToolResult.fail("UNHANDLED_TOOL", f"No execution handler configured for '{tool_name}'.")

        except Exception as e:
            return ToolResult.fail(
                "EXECUTION_ERROR",
                f"Unexpected error executing tool '{tool_name}': {str(e)}",
            )
