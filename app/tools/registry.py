from typing import Any, Dict, List, Type
from pydantic import BaseModel

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
)

# Registry mapping tool name -> (Pydantic Model, Tool Description)
TOOL_METADATA: Dict[str, Dict[str, Any]] = {
    "getTransaction": {
        "schema": GetTransactionInput,
        "description": "Retrieve comprehensive details for a transaction including amount, status, timestamp, and failure reasons.",
    },
    "getTransactionHistory": {
        "schema": GetTransactionHistoryInput,
        "description": "Fetch a paginated list of recent transactions for the user, with optional status filtering.",
    },
    "getAccount": {
        "schema": GetAccountInput,
        "description": "Retrieve primary account status (active, frozen, closed), account type, and linked cards.",
    },
    "getAccountBalance": {
        "schema": GetAccountBalanceInput,
        "description": "Retrieve real-time available and ledger balance for the user's active account.",
    },
    "getCustomerProfile": {
        "schema": GetCustomerProfileInput,
        "description": "Retrieve customer profile, KYC verification tier, preferred language, and registration date.",
    },
    "getPaymentStatus": {
        "schema": GetPaymentStatusInput,
        "description": "Check real-time payment gateway processing status, decline codes, and error descriptions.",
    },
    "checkFraudStatus": {
        "schema": CheckFraudStatusInput,
        "description": "Check whether a transaction was flagged by fraud detection filters and retrieve the risk score.",
    },
    "getRefundStatus": {
        "schema": GetRefundStatusInput,
        "description": "Check the status of an existing refund request by refund ID or original transaction ID.",
    },
    "initiateRefund": {
        "schema": InitiateRefundInput,
        "description": "Initiate a refund for a transaction. Amounts exceeding ₹10,000 are automatically routed for supervisor review.",
    },
    "createSupportTicket": {
        "schema": CreateSupportTicketInput,
        "description": "Create a persistent customer support ticket with category, priority, and problem description.",
    },
    "sendNotification": {
        "schema": SendNotificationInput,
        "description": "Send an outbound SMS, email, or in-app push notification to the customer.",
    },
    "searchPolicy": {
        "schema": SearchPolicyInput,
        "description": "Search banking policies, chargeback rules, FAQ articles, and compliance guidelines.",
    },
    "escalateToHumanAgent": {
        "schema": EscalateToHumanAgentInput,
        "description": "Escalate the conversation to a human specialist when automated resolution cannot be achieved.",
    },
}


class ToolRegistry:
    """Manages tool definitions, schemas, and Gemini function calling conversion."""

    @classmethod
    def get_registered_tool_names(cls) -> List[str]:
        return list(TOOL_METADATA.keys())

    @classmethod
    def get_input_schema(cls, tool_name: str) -> Type[BaseModel]:
        if tool_name not in TOOL_METADATA:
            raise KeyError(f"Tool '{tool_name}' is not registered.")
        return TOOL_METADATA[tool_name]["schema"]

    @classmethod
    def get_gemini_function_declarations(cls) -> List[Dict[str, Any]]:
        """Generate Gemini-compatible FunctionDeclaration specifications.
        
        CRITICAL SECURITY RULE:
        The 'user_id' parameter is deliberately stripped from all schemas exposed
        to the LLM. The authenticated user_id is injected server-side by ToolRouter
        from verified session context to prevent prompt injection or user spoofing.
        """
        declarations = []

        for name, meta in TOOL_METADATA.items():
            schema_cls = meta["schema"]
            json_schema = schema_cls.model_json_schema()

            # Deep copy properties to avoid mutating original schema
            properties = dict(json_schema.get("properties", {}))
            required = list(json_schema.get("required", []))

            # Strip user_id from LLM-facing interface
            if "user_id" in properties:
                del properties["user_id"]
            if "user_id" in required:
                required.remove("user_id")

            # Clean properties of schema metadata not needed by Gemini
            cleaned_properties = {}
            for prop_name, prop_val in properties.items():
                cleaned_val = {
                    "type": prop_val.get("type", "string"),
                    "description": prop_val.get("description", ""),
                }
                if "enum" in prop_val:
                    cleaned_val["enum"] = prop_val["enum"]
                cleaned_properties[prop_name] = cleaned_val

            declaration = {
                "name": name,
                "description": meta["description"],
                "parameters": {
                    "type": "object",
                    "properties": cleaned_properties,
                    "required": required,
                },
            }
            declarations.append(declaration)

        return declarations
