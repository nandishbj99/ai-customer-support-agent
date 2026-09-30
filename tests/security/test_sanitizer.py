import pytest
from app.security.sanitizer import sanitize_input_text


def test_sanitize_normal_text():
    res = sanitize_input_text("Hello, I need help checking my account balance.")
    assert res.is_suspicious is False
    assert res.flags == []
    assert res.sanitized_text == "Hello, I need help checking my account balance."


def test_sanitize_sqli_patterns():
    sqli_text = "test_user' UNION SELECT id, password FROM users --"
    res = sanitize_input_text(sqli_text)
    assert res.is_suspicious is True
    assert "POTENTIAL_SQLI" in res.flags


def test_sanitize_xss_patterns():
    xss_text = "Check this <script>alert('xss')</script> out"
    res = sanitize_input_text(xss_text)
    assert res.is_suspicious is True
    assert "POTENTIAL_XSS" in res.flags
    # Script tag escaped
    assert "&lt;script&gt;" in res.sanitized_text
    assert "<script>" not in res.sanitized_text


def test_sanitize_null_bytes():
    null_byte_text = "user\x00_test"
    res = sanitize_input_text(null_byte_text)
    assert "\x00" not in res.sanitized_text
    assert res.sanitized_text == "user_test"
