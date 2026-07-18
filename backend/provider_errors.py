class ProviderError(RuntimeError):
    """Base error for an external sponsor integration."""


class ProviderConfigurationError(ProviderError):
    """Raised when a required provider credential is missing."""


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an unusable response."""


class UnsafeGuidanceError(ProviderError):
    """Raised when the safety validator rejects generated guidance."""
