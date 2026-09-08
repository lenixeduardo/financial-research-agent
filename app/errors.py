class AssetNotFoundError(Exception):
    """Raised when the requested ticker is unavailable."""


class ProviderTimeoutError(Exception):
    """Raised when a data provider times out."""

