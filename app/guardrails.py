import re

from app.config import settings
from app.errors import UnsupportedDocumentError


_QUESTION_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"override\s+(the\s+)?(system|developer)\s+(prompt|message|instructions?)", re.IGNORECASE),
    re.compile(r"(reveal|show|print|return)\s+(the\s+)?(system\s+prompt|developer\s+message)", re.IGNORECASE),
    re.compile(r"exfiltrate|reveal\s+secret|api[_ -]?key", re.IGNORECASE),
]

_DOCUMENT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"(system|developer)\s+(prompt|message)\s*:", re.IGNORECASE),
    re.compile(r"(reveal|exfiltrate|send)\s+.*(?:secret|api[_ -]?key|credentials?)", re.IGNORECASE),
]


def validate_document_size(data: bytes) -> None:
    if len(data) > settings.max_document_bytes:
        raise UnsupportedDocumentError(
            f"document exceeds maximum size of {settings.max_document_bytes} bytes"
        )


def assess_research_question(question: str) -> tuple[bool, list[str]]:
    """Return whether a research question is safe to process and why."""
    reasons = [
        pattern.pattern for pattern in _QUESTION_INJECTION_PATTERNS if pattern.search(question)
    ]
    return not reasons, reasons


def assess_untrusted_document_text(text: str) -> tuple[bool, list[str]]:
    """Detect high-confidence prompt-injection instructions embedded in uploaded data.

    Uploaded documents are evidence, not instructions. Rejecting obvious control
    phrases prevents a future model-backed synthesis layer from treating retrieved
    text as executable instructions.
    """
    reasons = [
        pattern.pattern for pattern in _DOCUMENT_INJECTION_PATTERNS if pattern.search(text)
    ]
    return not reasons, reasons
