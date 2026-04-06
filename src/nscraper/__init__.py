"""Public package interface for nscraper."""

from importlib.metadata import PackageNotFoundError, version

from .errors import (
    InvalidCookiesError,
    InvalidHeadersError,
    InvalidOutputPathError,
    InvalidUrlError,
    NetworkError,
    NscraperError,
    RequestError,
    UnsupportedContentTypeError,
)
from .logging import DebugLogger, debug_logger
from .models import ScrapeOptions
from .models import NetworkResult, ResultData, ScrapeResult
from .scraper import BaseScraper, HttpScraper, SeleniumBaseScraper, get_scraper
from .utils import (
    DEFAULT_HEADERS,
    apply_pretty_format,
    auto_output_path,
    basic_html_transform,
    classify_response_type,
    fast_html_transform,
    load_cookies_file,
    normalize_headers,
    parse_headers,
    pretty_html,
    pretty_json,
    ResponseType,
    ResponseTypeClassifier,
    response_type_classifier,
    validate_url,
    write_output,
)

CORE_EXPORTS = [
    "BaseScraper",
    "HttpScraper",
    "NetworkResult",
    "ResultData",
    "ScrapeResult",
    "SeleniumBaseScraper",
    "ScrapeOptions",
    "get_scraper",
]

ERROR_EXPORTS = [
    "InvalidCookiesError",
    "InvalidHeadersError",
    "InvalidOutputPathError",
    "InvalidUrlError",
    "NetworkError",
    "NscraperError",
    "RequestError",
    "UnsupportedContentTypeError",
]

UTILITY_EXPORTS = [
    "DEFAULT_HEADERS",
    "ResponseType",
    "ResponseTypeClassifier",
    "apply_pretty_format",
    "auto_output_path",
    "basic_html_transform",
    "classify_response_type",
    "fast_html_transform",
    "load_cookies_file",
    "normalize_headers",
    "parse_headers",
    "pretty_html",
    "pretty_json",
    "response_type_classifier",
    "validate_url",
    "write_output",
]

LOGGING_EXPORTS = [
    "DebugLogger",
    "debug_logger",
]

try:
    __version__ = version("nscraper")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = (
    CORE_EXPORTS
    + ERROR_EXPORTS
    + LOGGING_EXPORTS
    + UTILITY_EXPORTS
    + ["__version__"]
)
