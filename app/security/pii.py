import re
from typing import Any, Dict, List, Union

# Compiled Regex Patterns
AADHAAR_PATTERN = re.compile(r"\b(\d{4})[ -]?(\d{4})[ -]?(\d{4})\b")
PAN_PATTERN = re.compile(r"\b([A-Z]{5})(\d{4})([A-Z]{1})\b", re.IGNORECASE)
ACCOUNT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){11,18}\d\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?91[ -]?)?([6-9]\d{9})\b")
EMAIL_PATTERN = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b")

# Sensitive Keys that should be completely masked in payloads/logs
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "pin",
    "upi_pin",
    "cvv",
    "cvv2",
    "otp",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "x-api-key",
}


def mask_aadhaar(text: str) -> str:
    """Mask Indian Aadhaar number to XXXX-XXXX-1234."""
    def repl(m: re.Match) -> str:
        last4 = m.group(3)
        return f"XXXX-XXXX-{last4}"
    return AADHAAR_PATTERN.sub(repl, text)


def mask_pan(text: str) -> str:
    """Mask Indian PAN number to XXXXX1234X."""
    def repl(m: re.Match) -> str:
        num = m.group(2)
        tail = m.group(3).upper()
        return f"XXXXX{num}{tail}"
    return PAN_PATTERN.sub(repl, text)


def mask_account_or_card(text: str) -> str:
    """Mask 12-19 digit account or debit/credit card numbers to ****1234."""
    def repl(m: re.Match) -> str:
        digits_only = re.sub(r"[^\d]", "", m.group(0))
        if len(digits_only) >= 12:
            return f"****{digits_only[-4:]}"
        return m.group(0)
    return ACCOUNT_CARD_PATTERN.sub(repl, text)


def mask_phone(text: str) -> str:
    """Mask 10-digit mobile number to ******1234."""
    def repl(m: re.Match) -> str:
        num = m.group(1)
        return f"******{num[-4:]}"
    return PHONE_PATTERN.sub(repl, text)


def mask_email(text: str) -> str:
    """Mask email to u***r@domain.com."""
    def repl(m: re.Match) -> str:
        user = m.group(1)
        domain = m.group(2)
        if len(user) <= 2:
            masked_user = f"{user[0]}***"
        else:
            masked_user = f"{user[0]}***{user[-1]}"
        return f"{masked_user}@{domain}"
    return EMAIL_PATTERN.sub(repl, text)


def mask_pii_string(value: str) -> str:
    """Run all regex masking filters over an arbitrary text string."""
    if not isinstance(value, str) or not value:
        return value
    text = mask_aadhaar(value)
    text = mask_pan(text)
    text = mask_account_or_card(text)
    text = mask_phone(text)
    text = mask_email(text)
    return text


def redact_pii(data: Any) -> Any:
    """Recursively redacts PII and sensitive secret fields in nested dicts, lists, and primitives."""
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            key_lower = str(k).lower()
            if any(s in key_lower for s in SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED_SECRET]"
            else:
                cleaned[k] = redact_pii(v)
        return cleaned

    elif isinstance(data, list):
        return [redact_pii(item) for item in data]

    elif isinstance(data, tuple):
        return tuple(redact_pii(item) for item in data)

    elif isinstance(data, str):
        return mask_pii_string(data)

    return data
