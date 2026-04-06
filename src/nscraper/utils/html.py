"""HTML transform and formatting helpers."""

from __future__ import annotations

import re

from justhtml import JustHTML

BASIC_HTML_CLEANUP_SELECTORS = (
    "script",
    "style",
    "noscript",
    "iframe",
    "source",
    "svg",
    "template",
    "[aria-hidden='true']",
    "[hidden]",
    ".ads",
    ".advertisement",
    ".banner",
    ".social-share",
    ".newsletter",
)
FAST_HTML_CLEANUP_SELECTORS = (
    "script",
    "style",
    "noscript",
    "iframe",
    "template",
)

_HIDDEN_RE = re.compile(
    r"<(?P<tag>[a-zA-Z][\w:-]*)(?=[^>]*\bhidden(?:\s|>|=))[^>]*>.*?</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)


def basic_html_transform(content: str) -> str:
    cleaned_input = _HIDDEN_RE.sub("", content)
    doc = JustHTML(cleaned_input, fragment=False)
    for selector in BASIC_HTML_CLEANUP_SELECTORS:
        for node in doc.query(selector):
            if node.parent:
                node.parent.remove_child(node)
    for head in doc.query("head"):
        while head.has_child_nodes():
            head.remove_child(head.children[0])
    return doc.to_html(pretty=False)


def fast_html_transform(content: str) -> str:
    doc = JustHTML(content, fragment=False)
    for selector in FAST_HTML_CLEANUP_SELECTORS:
        for node in doc.query(selector):
            if node.parent:
                node.parent.remove_child(node)
    return doc.to_html(pretty=False)


def pretty_html(content: str) -> str:
    doc = JustHTML(content, fragment=False)
    return doc.to_html(pretty=True)
