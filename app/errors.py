class AssetNotFoundError(Exception):
    """Raised when the requested ticker is unavailable."""


class ProviderTimeoutError(Exception):
    """Raised when a data provider times out."""


class DocumentNotFoundError(Exception):
    """Raised when the requested document is unavailable."""


class UnsupportedDocumentError(Exception):
    """Raised when a document format cannot be extracted."""


class InsufficientEvidenceError(Exception):
    """Raised when a research question has no supporting document evidence."""


class SecurityPolicyError(Exception):
    """Raised when an input violates deterministic safety guardrails."""
