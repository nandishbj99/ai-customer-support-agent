import html
import re
from typing import Any, Dict, List, Tuple

# Patterns that indicate blatant malicious injection attempts
SQLI_PATTERNS = [
    re.compile(r"(\bunion\b\s+\bselect\b)", re.IGNORECASE),
    re.compile(r"(\bdrop\b\s+\btable\b)", re.IGNORECASE),
    re.compile(r"(\binsert\b\s+\binto\b)", re.IGNORECASE),
    re.compile(r"(\bselect\b\s+.*\s+\bfrom\b)", re.IGNORECASE),
    re.compile(r"(\bor\b\s+['\"]?1['\"]?\s*=\s*['\"]?1)", re.IGNORECASE),
    re.compile(r"(--|/\*|\*/|;\s*$)", re.IGNORECASE),
]

XSS_PATTERNS = [
    re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe.*?>", re.IGNORECASE),
]


class SanitizationResult:
    def __init__(self, sanitized_text: str, is_suspicious: bool = False, flags: List[str] = None):
        self.sanitized_text = sanitized_text
        self.is_suspicious = is_suspicious
        self.flags = flags or []


def sanitize_input_text(text: str) -> SanitizationResult:
    """Sanitize user text input by stripping control characters and escaping dangerous HTML."""
    if not isinstance(text, str):
        return SanitizationResult(str(text))

    flags = []

    # Strip NULL bytes and dangerous non-printable control characters
    cleaned = text.replace("\x00", "")

    # Check for SQLi patterns
    for p in SQLI_PATTERNS:
        if p.search(cleaned):
            flags.append("POTENTIAL_SQLI")
            break

    # Check for XSS patterns
    for p in XSS_PATTERNS:
        if p.search(cleaned):
            flags.append("POTENTIAL_XSS")
            break

    # Escape HTML entities to prevent reflective injection
    escaped = html.escape(cleaned)

    return SanitizationResult(
        sanitized_text=escaped,
        is_suspicious=len(flags) > 0,
        flags=flags,
    )
