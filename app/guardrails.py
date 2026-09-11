import re

from app.config import settings
from app.errors import UnsupportedDocumentError


_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"developer\s+message", re.IGNORECASE),
    re.compile(r"exfiltrate|reveal\s+secret|api[_ -]?key", re.IGNORECASE),
]


def validate_document_size(data: bytes) -> None:
    if len(data) > settings.max_document_bytes:
        raise UnsupportedDocumentError(
            f"document exceeds maximum size of {settings.max_document_bytes} bytes"
        )


def assess_research_question(question: str) -> tuple[bool, list[str]]:
    """Return whether a research question is safe to process and why.

    This is deliberately deterministic and transparent. It protects the retrieval
    layer from obvious prompt-injection attempts while keeping financial questions
    unaffected.
    """
    reasons = [pattern.pattern for pattern in _PROMPT_INJECTION_PATTERNS if pattern.search(question)]
    return not reasons, reasons
