"""
Test selection handler for guiding users through statistical test choices.

This handler implements a decision-tree-based workflow that asks users
a series of questions to recommend the most appropriate statistical test
for their analysis needs.
"""

from typing import Any

from app.advisor import decision_tree, get_test_info


def handle_test_selection(message: str, client: Any) -> str:
    """
    Guide user through statistical test selection using a decision tree.

    Manages the state of the decision tree navigation, asking questions
    and presenting options until a terminal node (test recommendation)
    is reached.

    Args:
        message: User's response to the current question.
        client: LLM client (unused, reserved for future extensions).

    Returns:
        Markdown-formatted response with either:
        - The next question and options
        - A test recommendation with next steps
    """
    current_node = decision_tree.get_current_node()

    # At start node, present the initial question
    if decision_tree.current_node_id == "start":
        return _format_question(current_node)

    # Process user's choice and advance through the tree
    next_node = decision_tree.select_option(message)

    if next_node.is_terminal:
        return _format_recommendation(next_node)

    return _format_question(next_node)


def _format_question(node: Any) -> str:
    """
    Format a decision tree node as a question with options.

    Uses chr(10) for newlines in f-string join to maintain compatibility.
    """
    options_text = "".join('- ' + opt + chr(10) for opt in node.options)

    if decision_tree.current_node_id == "start":
        return f"""I'll help you choose the right statistical test. Let me ask a few questions.

{node.question}

**Options:**
{options_text}
Reply with your choice (e.g., "Association" or "Difference")."""

    return f"""{node.question}

**Options:**
{options_text}"""


def _format_recommendation(node: Any) -> str:
    """
    Format a terminal node as a test recommendation.

    Resets the decision tree after presenting the recommendation so
    the user can start fresh if needed.
    """
    test_id = node.recommended_test
    test_info = get_test_info(test_id)

    # Build recommendation response
    use_when = "".join('- ' + item + chr(10) for item in test_info.use_when[:3])
    assumptions = "".join('- ' + item + chr(10) for item in test_info.assumptions[:3])

    response = f"""## Recommended Test: **{test_info.name}**

{node.test_explanation}

**When to use:**
{use_when}
**Assumptions:**
{assumptions}
---

**Next steps:**
1. Say **"Generate code"** to get R code for this test
2. Say **"Explain more"** for detailed information
3. Say **"Start over"** to pick a different test

Or just ask me anything else!"""

    # Reset tree for next query
    decision_tree.reset()

    return response
