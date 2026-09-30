import pytest
from app.security.logging import structlog_pii_masking_processor
from app.security.pii import (
    mask_aadhaar,
    mask_account_or_card,
    mask_email,
    mask_pan,
    mask_phone,
    redact_pii,
)


def test_mask_aadhaar_formats():
    # Hyphenated
    assert mask_aadhaar("Customer Aadhaar is 1234-5678-9012.") == "Customer Aadhaar is XXXX-XXXX-9012."
    # Spaced
    assert mask_aadhaar("Aadhaar 1234 5678 9012 registered") == "Aadhaar XXXX-XXXX-9012 registered"
    # Contiguous
    assert mask_aadhaar("Number 123456789012.") == "Number XXXX-XXXX-9012."


def test_mask_pan_formats():
    assert mask_pan("User PAN is ABCDE1234F verified") == "User PAN is XXXXX1234F verified"
    assert mask_pan("pan: zyxwv9876a") == "pan: XXXXX9876A"


def test_mask_card_and_account_numbers():
    # 16-digit debit card
    assert mask_account_or_card("Paid with card 4111222233334444") == "Paid with card ****4444"
    # 14-digit bank account
    assert mask_account_or_card("Bank account 10020030040055 credited") == "Bank account ****0055 credited"


def test_mask_phone_and_email():
    assert mask_phone("Contact customer at 9876543210") == "Contact customer at ******3210"
    assert mask_email("rahul.sharma@hdfcbank.com") == "r***a@hdfcbank.com"


def test_recursive_pii_and_secrets_redaction():
    payload = {
        "user": {
            "name": "Amit Kumar",
            "aadhaar": "9876-5432-1098",
            "pan": "ABCDE5678K",
            "password": "SuperSecretPassword123!",
            "upi_pin": "1234",
            "cards": [
                {"card_number": "5241888877771234", "cvv": "999"},
            ],
        },
        "metadata": {
            "token": "bearer_jwt_secret_token",
            "notes": "Customer called from 9876543210 asking for refund",
        },
    }

    cleaned = redact_pii(payload)

    # Secrets completely redacted
    assert cleaned["user"]["password"] == "[REDACTED_SECRET]"
    assert cleaned["user"]["upi_pin"] == "[REDACTED_SECRET]"
    assert cleaned["user"]["cards"][0]["cvv"] == "[REDACTED_SECRET]"
    assert cleaned["metadata"]["token"] == "[REDACTED_SECRET]"

    # PII masked with preserved safe tails
    assert "XXXX-XXXX-1098" in cleaned["user"]["aadhaar"]
    assert "XXXXX5678K" in cleaned["user"]["pan"]
    assert "****1234" in cleaned["user"]["cards"][0]["card_number"]
    assert "******3210" in cleaned["metadata"]["notes"]


def test_structlog_processor():
    event = {
        "event": "user_auth_failed",
        "email": "user@example.com",
        "password": "plain_password_leak",
        "aadhaar": "1234-5678-9012",
    }
    processed = structlog_pii_masking_processor(None, "info", event)
    assert processed["password"] == "[REDACTED_SECRET]"
    assert processed["aadhaar"] == "XXXX-XXXX-9012"
