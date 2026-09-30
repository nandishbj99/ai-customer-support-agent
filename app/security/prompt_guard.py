import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class InjectionRiskLevel(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    BLOCKED = "BLOCKED"


@dataclass
class PromptSecurityAssessment:
    risk_level: InjectionRiskLevel
    matched_patterns: List[str]
    clean_prompt: str
    rejection_message: Optional[str] = None


# Patterns indicating deliberate jailbreak or prompt extraction attempts
BLOCKED_PATTERNS = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE), "INSTRUCTION_OVERRIDE"),
    (re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE), "INSTRUCTION_OVERRIDE"),
    (re.compile(r"forget\s+(everything|all\s+prior\s+rules)", re.IGNORECASE), "INSTRUCTION_OVERRIDE"),
    (re.compile(r"reveal\s+(your\s+)?(system\s+prompt|initial\s+prompt|developer\s+mode|instructions)", re.IGNORECASE), "SYSTEM_PROMPT_LEAK"),
    (re.compile(r"print\s+(your\s+)?(system\s+prompt|initial\s+instructions|system\s+instructions)", re.IGNORECASE), "SYSTEM_PROMPT_LEAK"),
    (re.compile(r"(act\s+as\s+an?\s+unrestricted|you\s+are\s+now\s+in\s+dan\s+mode|jailbreak)", re.IGNORECASE), "JAILBREAK_ATTEMPT"),
    (re.compile(r"(bypass|override)\s+(hitl|approval|threshold|safety\s+filter)", re.IGNORECASE), "TOOL_SAFETY_OVERRIDE"),
    (re.compile(r"show\s+(all\s+)?(api_keys|secrets|passwords|env\s+vars)", re.IGNORECASE), "SECRET_EXFILTRATION"),
]

# Patterns that warrant elevated scrutiny
SUSPICIOUS_PATTERNS = [
    (re.compile(r"\b(system\s*:\s*|assistant\s*:\s*|human\s*:\s*)", re.IGNORECASE), "ROLE_PLAY_DELIMITER"),
    (re.compile(r"(\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>)", re.IGNORECASE), "SPECIAL_TOKEN_INJECTION"),
    (re.compile(r"repeat\s+the\s+words\s+above", re.IGNORECASE), "PROMPT_EXTRACTION_HEURISTIC"),
]


class PromptGuard:
    """Multi-layer heuristic and regex guardrail detecting prompt injections and jailbreaks."""

    def evaluate(self, user_message: str) -> PromptSecurityAssessment:
        if not user_message or not isinstance(user_message, str):
            return PromptSecurityAssessment(
                risk_level=InjectionRiskLevel.SAFE,
                matched_patterns=[],
                clean_prompt="",
            )

        text = user_message.strip()
        matched_blocked = []

        # Check critical blocked patterns
        for pattern, label in BLOCKED_PATTERNS:
            if pattern.search(text):
                matched_blocked.append(label)

        if matched_blocked:
            return PromptSecurityAssessment(
                risk_level=InjectionRiskLevel.BLOCKED,
                matched_patterns=matched_blocked,
                clean_prompt=text,
                rejection_message=(
                    "I am unable to process this request as it contains phrasing or instructions "
                    "that violate our security and safety policies. Please rephrase your banking question."
                ),
            )

        # Check suspicious patterns
        matched_suspicious = []
        for pattern, label in SUSPICIOUS_PATTERNS:
            if pattern.search(text):
                matched_suspicious.append(label)

        if matched_suspicious:
            return PromptSecurityAssessment(
                risk_level=InjectionRiskLevel.SUSPICIOUS,
                matched_patterns=matched_suspicious,
                clean_prompt=text,
            )

        return PromptSecurityAssessment(
            risk_level=InjectionRiskLevel.SAFE,
            matched_patterns=[],
            clean_prompt=text,
        )


prompt_guard = PromptGuard()
