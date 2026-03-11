"""
Input Sanitization Utilities for Prompt Injection Protection

This module provides functions to detect and neutralize prompt injection attacks
before user input is sent to LLM prompts.
"""

import re
import logging
from typing import Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SanitizationResult:
    """Result of input sanitization"""
    sanitized_text: str
    is_suspicious: bool
    detected_patterns: List[str]
    risk_score: float  # 0.0 to 1.0


# Patterns that indicate potential prompt injection attempts
INJECTION_PATTERNS = [
    # Direct instruction override attempts
    (r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)", "instruction_override"),
    (r"disregard\s+(all\s+)?(previous|prior|above|earlier)", "instruction_override"),
    (r"forget\s+(everything|all|what)\s+(you|i)\s+(said|told|wrote)", "instruction_override"),

    # Role manipulation
    (r"you\s+are\s+now\s+(a|an)", "role_manipulation"),
    (r"pretend\s+(to\s+be|you\s+are)", "role_manipulation"),
    (r"act\s+as\s+(if|though|a|an)", "role_manipulation"),
    (r"from\s+now\s+on\s+(you|act|be)", "role_manipulation"),
    (r"switch\s+(to|into)\s+(a\s+)?(new\s+)?(role|mode|persona)", "role_manipulation"),

    # System prompt extraction
    (r"(what|show|reveal|display|tell|give)\s+(is|me|us)?\s*(your|the)?\s*(system|initial|original)\s*(prompt|instruction)", "prompt_extraction"),
    (r"repeat\s+(your|the)\s+(system|initial|original)\s*(prompt|instruction|message)", "prompt_extraction"),
    (r"(print|output|echo)\s+(your|the)?\s*(system|initial)", "prompt_extraction"),

    # Delimiter injection
    (r"```\s*(system|assistant|user)\s*:", "delimiter_injection"),
    (r"\[INST\]|\[/INST\]", "delimiter_injection"),
    (r"<\|?(system|assistant|user|im_start|im_end)\|?>", "delimiter_injection"),
    (r"###\s*(system|instruction|human|assistant)", "delimiter_injection"),

    # Jailbreak phrases
    (r"(dan|dude|devil)\s*(mode|prompt)", "jailbreak_attempt"),
    (r"jailbreak", "jailbreak_attempt"),
    (r"bypass\s+(safety|filter|restriction|guardrail)", "jailbreak_attempt"),
    (r"(remove|disable|turn\s+off)\s+(your|the)?\s*(safety|filter|restriction)", "jailbreak_attempt"),

    # Hidden instruction markers
    (r"\[\s*hidden\s*\]", "hidden_instruction"),
    (r"\[\s*secret\s*\]", "hidden_instruction"),
    (r"<!--.*instruction.*-->", "hidden_instruction"),
]

# Words/phrases to escape/neutralize (not block entirely)
NEUTRALIZATION_PATTERNS = [
    (r"<\|", "&lt;|"),
    (r"\|>", "|&gt;"),
    (r"```(system|user|assistant)", "``` \\1"),  # Add space to break delimiter
]


def detect_injection_patterns(text: str) -> Tuple[bool, List[str], float]:
    """
    Detect potential prompt injection patterns in text.

    Returns:
        Tuple of (is_suspicious, detected_patterns, risk_score)
    """
    text_lower = text.lower()
    detected = []

    for pattern, pattern_name in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            detected.append(pattern_name)

    # Calculate risk score
    unique_patterns = set(detected)
    risk_score = min(len(unique_patterns) * 0.25, 1.0)

    # High-risk patterns get extra weight
    if "instruction_override" in unique_patterns:
        risk_score = min(risk_score + 0.3, 1.0)
    if "prompt_extraction" in unique_patterns:
        risk_score = min(risk_score + 0.2, 1.0)
    if "jailbreak_attempt" in unique_patterns:
        risk_score = min(risk_score + 0.3, 1.0)

    is_suspicious = len(detected) > 0

    return is_suspicious, detected, risk_score


def neutralize_delimiters(text: str) -> str:
    """
    Neutralize common LLM delimiter patterns that could be used for injection.
    """
    result = text
    for pattern, replacement in NEUTRALIZATION_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def sanitize_for_prompt(text: str, max_length: int = 10000) -> SanitizationResult:
    """
    Sanitize user input before including in LLM prompts.

    This function:
    1. Truncates to max_length
    2. Detects injection patterns
    3. Neutralizes dangerous delimiters
    4. Returns sanitization result with risk assessment

    Args:
        text: User input text
        max_length: Maximum allowed length (default 10000)

    Returns:
        SanitizationResult with sanitized text and risk assessment
    """
    if not text:
        return SanitizationResult(
            sanitized_text="",
            is_suspicious=False,
            detected_patterns=[],
            risk_score=0.0
        )

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Input truncated from {len(text)} to {max_length} characters")

    # Detect injection patterns
    is_suspicious, detected_patterns, risk_score = detect_injection_patterns(text)

    if is_suspicious:
        logger.warning(
            f"Potential prompt injection detected. Patterns: {detected_patterns}, "
            f"Risk score: {risk_score:.2f}"
        )

    # Neutralize delimiters
    sanitized = neutralize_delimiters(text)

    return SanitizationResult(
        sanitized_text=sanitized,
        is_suspicious=is_suspicious,
        detected_patterns=detected_patterns,
        risk_score=risk_score
    )


def wrap_user_input(text: str, delimiter: str = "---") -> str:
    """
    Wrap user input with clear delimiters to help the model distinguish
    user content from instructions.

    Args:
        text: Sanitized user input
        delimiter: Delimiter string to use

    Returns:
        Wrapped text with clear boundaries
    """
    return f"""
{delimiter} BEGIN USER INPUT {delimiter}
{text}
{delimiter} END USER INPUT {delimiter}
""".strip()


def safe_format_prompt(
    template: str,
    user_input: str,
    max_input_length: int = 5000,
    **kwargs
) -> Tuple[str, SanitizationResult]:
    """
    Safely format a prompt template with user input.

    This function sanitizes user input and wraps it with delimiters
    before inserting into the template.

    Args:
        template: Prompt template with {user_input} placeholder
        user_input: Raw user input
        max_input_length: Maximum allowed user input length
        **kwargs: Additional template variables

    Returns:
        Tuple of (formatted_prompt, sanitization_result)
    """
    # Sanitize user input
    result = sanitize_for_prompt(user_input, max_length=max_input_length)

    # Wrap with delimiters
    wrapped_input = wrap_user_input(result.sanitized_text)

    # Format template
    formatted = template.format(user_input=wrapped_input, **kwargs)

    return formatted, result
