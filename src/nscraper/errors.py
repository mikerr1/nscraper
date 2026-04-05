"""Project-specific exceptions for nscraper."""


class NscraperError(Exception):
    """Base exception for nscraper failures."""


class InvalidUrlError(NscraperError):
    """Raised when a URL argument is missing or invalid."""


class InvalidHeadersError(NscraperError):
    """Raised when headers are missing or malformed."""


class InvalidCookiesError(NscraperError):
    """Raised when cookies are missing or malformed."""


class RequestError(NscraperError):
    """Raised when an HTTP request fails with a non-success response."""


class NetworkError(NscraperError):
    """Raised when the request cannot be completed due to network issues."""
