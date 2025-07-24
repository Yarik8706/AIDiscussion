"""Utility functions for text processing and other helpers."""

import re
from typing import List, Union

__all__ = ["strip_markdown", "format_history"]


def strip_markdown(text: str) -> str:
    """Remove basic Markdown formatting from text.

    Args:
        text: A string potentially containing Markdown markup.

    Returns:
        The text without Markdown syntax.
    """
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"~~([^~]+)~~", r"\1", text)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#+\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    return text


def format_history(prompt: Union[str, List[str]]) -> str:
    """Format discussion history into a single string.

    Args:
        prompt: Either a single prompt or a list of discussion messages.

    Returns:
        Joined discussion history suitable for sending to a model.
    """
    if isinstance(prompt, list):
        return "\n".join(prompt)
    return prompt
