"""
General query handler for LLM-based responses with dataset context.

This handler serves as the fallback for queries that don't match specific
intent categories. It provides context-aware responses by injecting
dataset information into the LLM system prompt.
"""

from typing import Any, Optional

from flask import current_app

from app.advisor import decision_tree
from app.llm import PromptTemplates


# Phrases that trigger a conversation reset
_RESET_PHRASES = ('start over', 'reset', 'new question', 'begin again')


def handle_general(
    message: str,
    client: Any,
    context: Optional[dict] = None
) -> str:
    """
    Handle general queries using LLM with optional dataset context.

    Provides two main behaviors:
    1. Reset commands - clears decision tree state and shows menu
    2. General queries - forwards to LLM with dataset context injected

    Args:
        message: User's query text.
        client: LLM client for generating responses.
        context: Optional dict containing 'columns' and 'filename' keys
                 for the currently loaded dataset.

    Returns:
        LLM-generated response or reset confirmation message.
    """
    if _is_reset_request(message):
        return _handle_reset()

    system_prompt = _build_system_prompt(context)

    return client.generate(
        prompt=message,
        system_prompt=system_prompt,
        temperature=current_app.config['LLM_TEMPERATURE']
    )


def _is_reset_request(message: str) -> bool:
    """Check if the message is a request to reset/start over."""
    message_lower = message.lower()
    return any(phrase in message_lower for phrase in _RESET_PHRASES)


def _handle_reset() -> str:
    """
    Reset the decision tree and return the welcome menu.

    Clears any in-progress test selection so users can start fresh.
    """
    decision_tree.reset()

    return """I've reset the test selection process.

How can I help you?
- **"Which test should I use?"** - I'll guide you through test selection
- **"Generate code for [test name]"** - Get R code
- **"Explain [concept]"** - Learn about statistical methods
- **Upload a file** - Analyze your dataset"""


def _build_system_prompt(context: Optional[dict]) -> str:
    """
    Build the LLM system prompt, optionally with dataset context.

    When a dataset is loaded, appends column information so the LLM
    can reference actual column names instead of using placeholders.
    """
    system_prompt = PromptTemplates.GENERAL_ASSISTANT

    if not context or not context.get('column_names'):
        return system_prompt

    columns_str = ", ".join(context.get('column_names', []))
    filename = context.get('filename', 'uploaded file')

    # Append dataset context to help LLM provide relevant suggestions
    system_prompt += f"""

CURRENT DATASET CONTEXT:
You have a dataset loaded named "{filename}".
Columns: {columns_str}

If the user asks to analyze this data, acknowledge the columns and ask what specific analysis they want (e.g., compare groups, correlation).
Do NOT assume dummy data. Use the column names provided above."""

    return system_prompt
