"""
Debugging handler for R error diagnosis and resolution.

This handler parses R error messages and provides user-friendly
explanations with suggested fixes.
"""

from typing import Any

from app.debugger import error_parser


def handle_error_debug(message: str, client: Any) -> str:
    """
    Parse and explain R error messages.

    Uses pattern matching to identify common R errors and provide
    actionable advice for resolution.

    Args:
        message: User message containing the R error text.
        client: LLM client (unused, reserved for future LLM-assisted debugging).

    Returns:
        Markdown-formatted error explanation with suggestions.
    """
    # Parse error using pattern-based analyzer
    parsed_error = error_parser.parse(message)

    # Format explanation for user
    response = error_parser.format_for_user(parsed_error)

    # Append help options
    response += """
---

**Need more help?**
- Paste your full code and I'll look for the issue
- Tell me what you were trying to do
- Ask me to explain any specific part"""

    return response
