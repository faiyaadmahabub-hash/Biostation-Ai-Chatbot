"""
Chat routes for the BioStation AI chatbot.

This module handles HTTP routing for chat interactions. It uses a 3-tier
intent detection system (Keywords -> Semantic -> LLM) to classify user
messages and routes them to specialized handlers.

All business logic has been extracted to app/handlers/ for maintainability.
This module focuses solely on request/response handling and routing.
"""

import inspect
import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Union

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
    session,
    stream_with_context,
)

from app.advisor import decision_tree
from app.llm import OllamaClient, PromptTemplates

from app.handlers import (
    handle_code_generation,
    handle_comparison,
    handle_correlation,
    handle_correlation_matrix,
    handle_descriptive_stats,
    handle_error_debug,
    handle_explanation,
    handle_general,
    handle_post_hoc,
    handle_test_selection,
)


logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

# Singleton LLM client instance
_llm_client: Optional[OllamaClient] = None


def get_llm_client() -> OllamaClient:
    """
    Get or create the LLM client singleton.

    Uses lazy initialization to defer client creation until first use,
    ensuring Flask app context is available for config access.
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = OllamaClient(
            model=current_app.config['LLM_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL']
        )
    return _llm_client


@chat_bp.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle chat messages with intent detection and handler routing.

    Uses 3-tier intent detection (Keywords -> Semantic -> LLM) to classify
    the user's message and routes to the appropriate handler.

    Returns:
        JSON response with 'response', 'action', 'understood_as',
        'confidence', and 'success' fields.
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_message:
            return jsonify({'error': 'Empty message', 'success': False}), 400

        from app.chat_storage_manager import chat_storage

        if conversation_id:
            chat_storage.add_message(conversation_id, 'user', user_message)

        client = get_llm_client()
        dataset_info = _get_dataset_context()
        intent_result = _detect_intent(user_message, client)

        interpretation = _build_interpretation(intent_result)
        response = _route_to_handler(
            intent_result.intent,
            user_message,
            interpretation,
            client,
            dataset_info
        )

        # Consume generator for non-streaming endpoint
        if inspect.isgenerator(response):
            response = "".join(response)

        if conversation_id:
            chat_storage.add_message(conversation_id, 'assistant', response)

        return jsonify({
            'response': response,
            'action': intent_result.intent,
            'understood_as': intent_result.understood_as,
            'confidence': intent_result.confidence,
            'success': True
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'response': 'Sorry, I encountered an error. Please try again.',
            'success': False
        }), 500


@chat_bp.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    Streaming chat endpoint for real-time response delivery.

    Uses Server-Sent Events (SSE) to stream responses token by token
    for a more responsive user experience.

    Returns:
        SSE stream with 'content', 'done', or 'error' event types.
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_message:
            return jsonify({'error': 'Empty message', 'success': False}), 400

        from app.chat_storage_manager import chat_storage

        if conversation_id:
            chat_storage.add_message(conversation_id, 'user', user_message)

        client = get_llm_client()
        dataset_info = _get_dataset_context()
        intent_result = _detect_intent(user_message, client)
        interpretation = _build_interpretation(intent_result)

        def generate():
            """SSE generator for streaming responses."""
            try:
                action = intent_result.intent

                # Actions that use the execute_and_interpret pipeline
                pipeline_actions = {
                    'descriptive_stats', 'compare_groups', 'correlation',
                    'correlation_matrix', 'regression', 'debug_error', 'post_hoc'
                }

                # Check if message matches a custom test keyword
                use_pipeline = action in pipeline_actions
                if not use_pipeline:
                    from app.handlers.base import get_test_mapping
                    from app.code_gen.template_loader import get_template_loader
                    message_lower = user_message.lower()
                    test_mapping = get_test_mapping()
                    loader = get_template_loader()
                    for keyword, test_id in test_mapping.items():
                        if keyword in message_lower and loader.template_exists(test_id):
                            use_pipeline = True
                            break

                if use_pipeline:
                    full_response = yield from _stream_pipeline_response(
                        action, user_message, interpretation, client, dataset_info
                    )
                else:
                    full_response = yield from _stream_llm_response(
                        user_message, dataset_info, client
                    )

                yield _sse_event('done', {'action': action})

                if conversation_id:
                    chat_storage.add_message(conversation_id, 'assistant', full_response)

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield _sse_event('error', {'content': str(e)})

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.error(f"Error in streaming endpoint: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@chat_bp.route('/api/reset', methods=['POST'])
def reset():
    """Reset the decision tree state and clear session data."""
    decision_tree.reset()
    session.clear()
    return jsonify({'success': True, 'message': 'Reset complete'})


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _get_dataset_context() -> Dict[str, Any]:
    """
    Retrieve the current dataset context from session or persistent storage.

    Checks session first, then falls back to persistent storage for cases
    where the session was lost but dataset remains active.
    """
    dataset_info = session.get('current_dataset', {})

    if not dataset_info:
        from app.chat_storage_manager import dataset_storage
        active = dataset_storage.get_active_dataset()
        if active:
            dataset_info = active
            session['current_dataset'] = active
            logger.info(f"Recovered active dataset: {active['filename']}")

    return dataset_info


def _detect_intent(message: str, client: OllamaClient) -> Any:
    """
    Detect user intent using the 3-tier cascade system.

    Tries keyword matching first, then semantic similarity, then LLM
    classification as a fallback.
    """
    from app.llm import get_intent_detector

    chromadb_path = str(
        Path(current_app.config.get('DATA_DIR', 'data')) / 'intent_store'
    )
    detector = get_intent_detector(chromadb_path=chromadb_path, llm_client=client)

    result = detector.detect(message, use_llm_fallback=True)

    logger.info(
        f"Intent: '{message[:30]}...' -> {result.intent} "
        f"(conf={result.confidence:.2f}, method={result.method})"
    )

    return result


def _build_interpretation(intent_result: Any) -> Dict[str, Any]:
    """Convert intent detection result to handler-compatible dict format."""
    return {
        'action': intent_result.intent,
        'understood_as': intent_result.understood_as,
        'confidence': intent_result.confidence,
        'parameters': intent_result.details or {}
    }


def _route_to_handler(
    action: str,
    message: str,
    interpretation: Dict[str, Any],
    client: OllamaClient,
    dataset_info: Dict[str, Any]
) -> Union[str, Generator[str, None, None]]:
    """
    Route to the appropriate handler based on detected action.

    Maps action strings to handler functions and invokes with the
    appropriate arguments for each handler type.
    """
    # FIRST: Check for custom test keywords before standard routing
    # This ensures user-taught tests take priority
    from app.handlers.base import get_test_mapping
    from app.code_gen.template_loader import get_template_loader

    message_lower = message.lower()
    test_mapping = get_test_mapping()
    loader = get_template_loader()

    # Check if message contains a custom test keyword
    for keyword, test_id in test_mapping.items():
        if keyword in message_lower and test_id.startswith('custom_'):
            # This is a custom user-taught test
            if loader.template_exists(test_id):
                logger.info(f"Routing to custom test: {test_id}")
                return handle_code_generation(message, client)

    if action == 'descriptive_stats':
        return handle_descriptive_stats(interpretation, client)

    if action == 'compare_groups':
        return handle_comparison(interpretation, client)

    if action == 'correlation':
        return handle_correlation(interpretation, client)

    if action == 'correlation_matrix':
        return handle_correlation_matrix(interpretation, client)

    if action == 'regression':
        return handle_code_generation("regression", client)

    if action == 'test_selection':
        return handle_test_selection(message, client)

    if action == 'explain_concept':
        return handle_explanation(message, client)

    if action == 'debug_error':
        return handle_error_debug(message, client)

    if action == 'post_hoc':
        return handle_post_hoc(message, client)

    # Default fallback to general LLM handler
    return handle_general(message, client, dataset_info)


def _stream_pipeline_response(
    action: str,
    message: str,
    interpretation: Dict[str, Any],
    client: OllamaClient,
    dataset_info: Dict[str, Any]
) -> Generator[str, None, str]:
    """
    Stream response from pipeline-based handlers.

    These handlers may return generators for streaming or strings for
    immediate response. Yields SSE events and returns the full response.

    NOTE: Code explanation is now ON-DEMAND only (via Explain button).
    This eliminates automatic parallel LLM calls for 50% faster responses.
    """
    response = _route_to_handler(action, message, interpretation, client, dataset_info)

    full_response = ""

    # Signal that interpretation is starting
    yield _sse_event('thinking', {'process': 'interpretation', 'status': 'start'})

    if inspect.isgenerator(response):
        for chunk in response:
            yield _sse_event('content', {'content': chunk})
            full_response += chunk
    else:
        yield _sse_event('content', {'content': response})
        full_response = response

    # Signal interpretation is done
    yield _sse_event('thinking', {'process': 'interpretation', 'status': 'done'})

    return full_response


def _stream_llm_response(
    message: str,
    dataset_info: Dict[str, Any],
    client: OllamaClient
) -> Generator[str, None, str]:
    """
    Stream response directly from LLM for general queries.

    Builds context-aware system prompt and streams tokens from Ollama.
    """
    system_prompt = _build_context_prompt(dataset_info)

    stream = client.generate(
        prompt=message,
        system_prompt=system_prompt,
        temperature=current_app.config['LLM_TEMPERATURE'],
        stream=True
    )

    response_parts = []
    for chunk in stream:
        response_parts.append(chunk)
        yield _sse_event('content', {'content': chunk})

    return ''.join(response_parts)


def _build_context_prompt(dataset_info: Dict[str, Any]) -> str:
    """Build system prompt with optional dataset context."""
    system_prompt = PromptTemplates.GENERAL_ASSISTANT

    if dataset_info and dataset_info.get('column_names'):
        cols_str = ", ".join(dataset_info.get('column_names', []))
        fname = dataset_info.get('filename', 'uploaded file')
        system_prompt += f"""

CURRENT DATASET CONTEXT:
You have a dataset loaded named "{fname}".
Columns: {cols_str}

If the user asks to analyze this data, acknowledge the columns and ask what specific analysis they want (e.g., compare groups, correlation).
Do NOT assume dummy data. Use the column names provided above."""

    return system_prompt


def _sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """Format a Server-Sent Event message."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"
