"""
Chat routes - Handle chat interactions with intelligent routing
to different components (advisor, code gen, debugger, guidebook)
"""

from flask import Blueprint, render_template, request, jsonify, current_app, session
from app.llm import OllamaClient, PromptTemplates
from app.advisor import decision_tree, get_test_info, get_brief_explanation, get_full_explanation
from app.code_gen import code_generator
from app.debugger import error_parser
from app.r_engine import r_executor, output_parser
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

logger = logging.getLogger(__name__)

# Thread pool for background R execution (3 workers)
_r_executor_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="r_exec")

# Create blueprint
chat_bp = Blueprint('chat', __name__)

# Shared test name to ID mapping (used by code generation and explanation handlers)
TEST_MAPPING = {
    't-test': 'unpaired_ttest',
    'ttest': 'unpaired_ttest',
    'paired t': 'paired_ttest',
    'one sample': 'one_sample_ttest',
    'one sample t': 'one_sample_ttest',
    'anova': 'anova',
    'mann-whitney': 'mann_whitney',
    'mann whitney': 'mann_whitney',
    'wilcoxon': 'wilcoxon_signed_rank',
    'kruskal': 'kruskal_wallis',
    'pearson': 'pearson_correlation',
    'spearman': 'spearman_correlation',
    'chi-squared': 'chi_squared',
    'chi squared': 'chi_squared',
    'fisher': 'fisher_exact',
    'regression': 'linear_regression',
    'linear regression': 'linear_regression',
    'glm': 'glm',
    'logistic': 'glm',
    'glmm': 'glmm',
    'gam': 'gam',
    'mean': 'descriptive',
    'variance': 'descriptive',
    'summary': 'descriptive',
}

# Initialize LLM client (will be created once)
llm_client = None


def get_llm_client():
    """Get or create LLM client"""
    global llm_client
    if llm_client is None:
        llm_client = OllamaClient(
            model=current_app.config['LLM_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL']
        )
    return llm_client


@lru_cache(maxsize=128)
def get_cached_code(test_id: str, data_source: str, columns_tuple: tuple) -> str:
    """
    Generate R code with caching.
    Uses LRU cache to avoid regenerating same code.
    columns_tuple must be a tuple for hashability.
    """
    return code_generator.generate_code(
        test_id,
        data_source=data_source,
        column_context=list(columns_tuple)
    )



def handle_test_selection(message: str, client: OllamaClient) -> str:
    """Handle test selection using decision tree + LLM"""
    
    # Check if we're in the middle of the flowchart
    current_node = decision_tree.get_current_node()
    
    # If at start, begin the guided process
    if decision_tree.current_node_id == "start":
        # Check if user's message contains enough info to skip steps
        response = f"""I'll help you choose the right statistical test! Let me ask a few questions.

{current_node.question}

**Options:**
{"".join('• ' + opt + chr(10) for opt in current_node.options)}

Just reply with your choice (e.g., "Association" or "Difference")."""
        return response
    
    # Try to match user's response to an option
    next_node = decision_tree.select_option(message)
    
    if next_node.is_terminal:
        # We have a recommendation!
        test_id = next_node.recommended_test
        test_info = get_test_info(test_id)
        
        response = f"""## ✅ Recommended Test: **{test_info.name}**

{next_node.test_explanation}

**When to use:**
{"".join('• ' + item + chr(10) for item in test_info.use_when[:3])}

**Assumptions:**
{"".join('• ' + item + chr(10) for item in test_info.assumptions[:3])}

---

**Next steps:**
1. Say **"Generate code"** to get R code for this test
2. Say **"Explain more"** for detailed information
3. Say **"Start over"** to pick a different test

Or just ask me anything else!"""
        
        # Reset tree for next query
        decision_tree.reset()
        return response
    else:
        # Continue with next question
        response = f"""{next_node.question}

**Options:**
{"".join('• ' + opt + chr(10) for opt in next_node.options)}"""
        return response


# === NEW ACTION HANDLERS ===

def handle_descriptive_stats(interpretation: dict, client: OllamaClient) -> str:
    """Handle descriptive statistics requests"""
    dataset_info = session.get('current_dataset', {})
    column_names = dataset_info.get('column_names', [])
    filename = dataset_info.get('filename', 'your_data.csv')
    filepath = dataset_info.get('filepath', filename).replace('\\', '/') # Ensure R-compatible path
    
    if not column_names:
        return """📎 **Please upload a dataset first!**

Then I can calculate statistics for your data."""

    # Use the cached code generator for descriptive stats
    code = get_cached_code('descriptive', filepath, tuple(sorted(column_names)))
    
    # Use the same execution helper as Pearson correlation
    return execute_and_interpret_result('descriptive', code, client, dataset_info)


def execute_and_interpret_result(test_id, code, client, dataset_info, retry_count: int = 0):
    """
    Execute R code, get results, and generate LLM interpretation.
    Returns formatted markdown response.
    """
    # 1. Concept Explanation
    # Import for cleaner info
    from app.advisor.test_knowledge import get_test_info
    test_info = get_test_info(test_id)
    
    test_name = test_info.name if test_info else test_id.replace('_', ' ').title()
    purpose = test_info.purpose if test_info else "statistical analysis"
    
    # Stream Conversational Intro immediately
    intro_part = f"Okay, I'm running a **{test_name}** for you.\n\n**What it does**: {purpose}.\n\n"
    yield intro_part
    
    # Stream Code
    code_part = f"## 📝 R Code\n```r\n{code}\n```\n\n"
    yield code_part
    
    # 2. Execute Code (in background thread for better performance)
    logger.info(f"Executing R code for {test_id} (Attempt {retry_count+1})")
    # Submit R execution to thread pool, then wait for result
    future = _r_executor_pool.submit(r_executor.execute, code, True)  # capture_plots=True
    result = future.result()  # Wait for completion
    
    # === Auto-Debugging Loop ===
    if not result.success and retry_count < 2:
        logger.info(f"Execution failed. Attempting auto-debug (Retry {retry_count+1}/2). Error: {result.errors}")
        
        col_list = dataset_info.get('column_names', [])
        
        debug_prompt = f"""
You are an expert R debugger.
The following R code failed to execute on the user's dataset.

Code:
```r
{code}
```

Error Message:
{result.errors}

Dataset Info:
Columns: {col_list}

Task: Fix the R code to resolve the error.
Specific Fixes:
- If error is "grouping factor must have exactly 2 levels" (T-test error): Modify the code to filter the data. Select only the first two unique values of the grouping variable.
  Example fix: `data <- subset(data, GroupVar %in% unique(data$GroupVar)[1:2])`
- If columns are missing/wrong: Use the provided column list to guess the correct ones.
- Preserve the file path in read.csv.

Output: Return ONLY the corrected R code block (inside ```r ... ```).
"""
        # Ask LLM for fix
        fix_response = client.generate(debug_prompt, temperature=0.2)
        
        # Extract code
        import re
        match = re.search(r"```r\n(.*?)\n```", fix_response, re.DOTALL)
        if match:
            corrected_code = match.group(1)
            # Recursive Yield from generator
            yield from execute_and_interpret_result(test_id, corrected_code, client, dataset_info, retry_count=retry_count+1)
            return

    # 3. Interpret Results
    interpretation = ""
    execution_status = ""
    
    if result.success:
        execution_status = "✅ **Analysis Ran Successfully**"
        
        # If this was a retry, add a note
        if retry_count > 0:
            execution_status += f" (Auto-Fixed after {retry_count} attempt{'s' if retry_count>1 else ''})"

        # Extract numeric stats for potential highlighting
        stats = output_parser.extract_statistics(result.output)
        
        # Generate LLM interpretation of the output
        safe_output = result.output[:2000] # Truncate for token limit
        
        sys_prompt = "You are a helpful statistician. Interpret the R output clearly for a user."
        user_prompt = f"""Analyze this R output for a '{test_id}'.
        
Output:
{safe_output}

Provide a clear, non-technical interpretation.
1. State the conclusion (Significant or not?).
2. Explain what it means for the data.
3. Mention key values (p-value, means, etc.).
Keep it concise."""

        interpretation = client.generate(user_prompt, system_prompt=sys_prompt, temperature=0.3)
        
    else:
        execution_status = "❌ **Analysis Failed**"
        interpretation = f"The code could not be executed after {retry_count} attempts. Error:\n`{result.errors}`"

    # 4. Format Output with Sections
    # Format Plots
    plot_section = ""
    if result.plots:
        for p in result.plots:
            # We assume frontend can serve /api/plot/<filename>
            import os
            fname = os.path.basename(p)
            plot_section += f"\n\n![Result Plot](/api/plot/{fname})\n"

    # Stream Results and Interpretation
    final_part = f"""## ⚙️ Execution Results
{execution_status}

```text
{result.output[:1000] + ('...' if len(result.output)>1000 else '')}
```
{plot_section}

## 💡 Interpretation
{interpretation}
"""
    yield final_part


def handle_comparison(interpretation: dict, client: OllamaClient) -> str:
    """Handle group comparison requests"""
    dataset_info = session.get('current_dataset', {})
    column_names = dataset_info.get('column_names', [])
    filename = dataset_info.get('filename', 'your_data.csv')
    filepath = dataset_info.get('filepath', filename).replace('\\', '/')
    
    params = interpretation.get('parameters', {})
    test_type = params.get('test_type')
    
    if not column_names:
        return """📎 **Please upload a dataset first!**"""

    # Determine test
    test_id = 'unpaired_ttest' # Default
    if test_type:
        if 'anova' in test_type.lower(): test_id = 'anova'
        elif 'mann' in test_type.lower(): test_id = 'mann_whitney'
        elif 'paired' in test_type.lower(): test_id = 'paired_ttest'
    
    code = get_cached_code(test_id, filepath, tuple(sorted(column_names)))
    
    # Use the new execution helper
    return execute_and_interpret_result(test_id, code, client, dataset_info)


def handle_correlation(interpretation: dict, client: OllamaClient) -> str:
    """Handle correlation requests"""
    dataset_info = session.get('current_dataset', {})
    column_names = dataset_info.get('column_names', [])
    filename = dataset_info.get('filename', 'your_data.csv')
    filepath = dataset_info.get('filepath', filename).replace('\\', '/')
    
    if not column_names:
        return """📎 **Please upload a dataset first!**"""

    code = get_cached_code('pearson_correlation', filepath, tuple(sorted(column_names)))
    
    # Use the new execution helper
    return execute_and_interpret_result('pearson_correlation', code, client, dataset_info)


def handle_code_generation(message: str, client: OllamaClient) -> str:
    """Handle R code generation requests"""
    
    message_lower = message.lower()
    test_id = None
    
    # Use shared TEST_MAPPING constant
    for keyword, tid in TEST_MAPPING.items():
        if keyword in message_lower:
            test_id = tid
            break
    
    # Get current dataset info from session
    dataset_info = session.get('current_dataset', {})
    column_names = dataset_info.get('column_names', [])
    filename = dataset_info.get('filename', 'your_data.csv')
    filepath = dataset_info.get('filepath', filename).replace('\\', '/')
    
    # Handle descriptive statistics request (mean, variance, etc.)
    if test_id == 'descriptive' or any(word in message_lower for word in ['mean', 'variance', 'summary', 'statistics']):
        if column_names:
            # Generate context-aware code
            col_list = ', '.join([f'"{c}"' for c in column_names])
            code = f'''# Load your data
data <- read.csv("{filepath}")

# View column names
names(data)

# Summary statistics for all columns
summary(data)

# Your columns: {', '.join(column_names)}

# Calculate mean and variance for each numeric column
library(dplyr)

# If you want to group by a column (e.g., by tree):
# Replace 'GroupColumn' and 'ValueColumn' with your actual column names
# Your available columns are: {', '.join(column_names)}

stats_by_group <- data %>%
  group_by({column_names[0] if column_names else 'GroupColumn'}) %>%
  summarise(
    Mean = mean({column_names[-1] if len(column_names) > 1 else 'ValueColumn'}, na.rm = TRUE),
    Variance = var({column_names[-1] if len(column_names) > 1 else 'ValueColumn'}, na.rm = TRUE),
    SD = sd({column_names[-1] if len(column_names) > 1 else 'ValueColumn'}, na.rm = TRUE),
    N = n()
  )

print(stats_by_group)
'''
            return f"""## 📊 Descriptive Statistics Code

Your uploaded file **{filename}** has these columns:
`{', '.join(column_names)}`

```r
{code}
```

**Tip**: Modify the `group_by()` and column names to match your analysis needs!"""
        else:
            return """Please upload a dataset first! Then I can generate code with your actual column names.

Just click the 📎 attach button to upload a CSV or Excel file."""
    
    if not test_id:
        # Check if they have data and want general help
        if column_names:
            return f"""I see you have uploaded **{filename}** with columns:
`{', '.join(column_names)}`

**Which statistical test would you like code for?**

• **T-tests**: one-sample, paired, unpaired (independent samples)
• **ANOVA**: one-way ANOVA with Tukey post-hoc
• **Non-parametric**: Mann-Whitney, Wilcoxon, Kruskal-Wallis
• **Correlation**: Pearson, Spearman
• **Categorical**: Chi-squared, Fisher's exact
• **Regression**: Linear, GLM (logistic/Poisson)
• **Descriptive**: Mean, variance, summary statistics

Just say something like "Generate code for mean and variance" or "t-test code"."""
        else:
            return """Which statistical test would you like code for?

**Available tests:**
• **T-tests**: one-sample, paired, unpaired (independent samples)
• **ANOVA**: one-way ANOVA with Tukey post-hoc
• **Non-parametric**: Mann-Whitney, Wilcoxon, Kruskal-Wallis
• **Correlation**: Pearson, Spearman
• **Categorical**: Chi-squared, Fisher's exact
• **Regression**: Linear, GLM (logistic/Poisson)

Just say something like "Generate code for Mann-Whitney test"."""
    
    # Generate the code (cached)
    code = get_cached_code(test_id, filepath, tuple(sorted(column_names)))
    
    # Use execution pipeline
    return execute_and_interpret_result(test_id, code, client, dataset_info)


def handle_error_debug(message: str, client: OllamaClient) -> str:
    """Handle R error debugging"""
    
    # Extract the error message from user's input
    error_text = message
    
    # Try to parse the error
    parsed = error_parser.parse(error_text)
    
    # Format the response
    response = error_parser.format_for_user(parsed)
    
    # Add offer for more help
    response += """
---

**Need more help?**
• Paste your full code and I'll look for the issue
• Tell me what you were trying to do
• Ask me to explain any specific part"""
    
    return response


def handle_explanation(message: str, client: OllamaClient) -> str:
    """Handle explanation/education requests"""
    
    message_lower = message.lower()
    test_id = None
    
    # Use shared TEST_MAPPING constant
    for keyword, tid in TEST_MAPPING.items():
        if keyword in message_lower:
            test_id = tid
            break
    
    if test_id:
        # Check if they want brief or detailed
        if any(word in message_lower for word in ['detail', 'more', 'full', 'everything']):
            return get_full_explanation(test_id)
        else:
            brief = get_brief_explanation(test_id)
            return f"""{brief}

*Say "explain more" for detailed information, or "generate code" for R code.*"""
    
    # Second, check guidebook knowledge base for concepts
    from app.guidebook import search_concepts
    
    concept_matches = search_concepts(message)
    if concept_matches:
        # Return the best matching concept
        best_match = concept_matches[0]
        return f"""## 📚 {best_match['title']}

{best_match['content']}

---
*Want to learn about a different topic? Just ask!*"""
    
    # If no specific test or concept, use LLM for general explanation
    response = client.generate(
        prompt=message,
        system_prompt=PromptTemplates.GUIDEBOOK_SYNTHESIZER,
        temperature=current_app.config['LLM_TEMPERATURE']
    )
    
    return response


def handle_general(message: str, client: OllamaClient, context: dict = None) -> str:
    """Handle general queries using LLM with dataset context"""
    
    # Check for "start over" or reset commands
    if any(phrase in message.lower() for phrase in ['start over', 'reset', 'new question', 'begin again']):
        decision_tree.reset()
        return """I've reset the test selection process. 
        
How can I help you?
• **"Which test should I use?"** - I'll guide you through test selection
• **"Generate code for [test name]"** - Get R code
• **"Explain [concept]"** - Learn about statistical methods
• **Upload a file** - Analyze your dataset"""

    # Build system prompt with context
    system_prompt = PromptTemplates.GENERAL_ASSISTANT
    
    if context and context.get('columns'):
        columns_str = ", ".join(context.get('columns', []))
        filename = context.get('filename', 'uploaded file')
        
        system_prompt += f"""

CURRENT DATASET CONTEXT:
You have a dataset loaded named "{filename}".
Columns: {columns_str}

If the user asks to analyze this data, acknowledge the columns and ask what specific analysis they want (e.g., compare groups, correlation).
Do NOT assume dummy data. Use the column names provided above."""

    # Use LLM for general response
    response = client.generate(
        prompt=message,
        system_prompt=system_prompt,
        temperature=current_app.config['LLM_TEMPERATURE']
    )
    
    return response


@chat_bp.route('/')
def index():
    """Render main chat interface"""
    return render_template('index.html')


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with LLM-powered intent interpretation"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return jsonify({'error': 'Empty message', 'success': False}), 400
        
        # Import storage
        from app.chat_storage_manager import chat_storage
        
        # Save user message to storage if conversation exists
        if conversation_id:
            chat_storage.add_message(conversation_id, 'user', user_message)
        
        # Get LLM client
        client = get_llm_client()
        
        # Get dataset context (with recovery from DB if needed)
        dataset_info = session.get('current_dataset', {})
        
        # If no dataset in session, check persistent storage
        if not dataset_info:
            from app.chat_storage_manager import dataset_storage
            active = dataset_storage.get_active_dataset()
            if active:
                dataset_info = active
                session['current_dataset'] = active
                logger.info(f"Recovered active dataset: {active['filename']}")

        column_names = dataset_info.get('column_names', [])

        
        # === Use Smart Intent Detector (3-tier: Keywords -> Semantic -> LLM) ===
        from app.llm import get_intent_detector
        from pathlib import Path
        
        # Initialize detector with ChromaDB persistence
        chromadb_path = str(Path(current_app.config.get('DATA_DIR', 'data')) / 'intent_store')
        detector = get_intent_detector(chromadb_path=chromadb_path, llm_client=client)
        
        # Detect intent using 3-tier cascade
        intent_result = detector.detect(user_message, use_llm_fallback=True)
        
        action = intent_result.intent
        understood_as = intent_result.understood_as
        confidence = intent_result.confidence
        method = intent_result.method  # 'keyword', 'semantic', or 'llm'
        
        logger.info(f"Intent: '{user_message[:30]}...' -> {action} (conf={confidence:.2f}, method={method})")
        
        # Create interpretation dict for handler compatibility
        interpretation = {
            'action': action,
            'understood_as': understood_as,
            'confidence': confidence,
            'parameters': intent_result.details or {}
        }
        
        # Route based on structured action
        if action == 'descriptive_stats':
            response = handle_descriptive_stats(interpretation, client)
        elif action == 'compare_groups':
            response = handle_comparison(interpretation, client)
        elif action == 'correlation':
            response = handle_correlation(interpretation, client)
        elif action == 'regression':
            response = handle_code_generation("regression", client)
        elif action == 'test_selection':
            response = handle_test_selection(user_message, client)
        elif action == 'explain_concept':
            response = handle_explanation(user_message, client)
        elif action == 'debug_error':
            response = handle_error_debug(user_message, client)
        else:
            response = handle_general(user_message, client, dataset_info)
        
        # Consume generator if needed (for non-streaming endpoint)
        import inspect
        if inspect.isgenerator(response):
            response = "".join(response)
        
        # Save assistant response to storage
        if conversation_id:
            chat_storage.add_message(conversation_id, 'assistant', response)
        
        return jsonify({
            'response': response,
            'action': action,
            'understood_as': understood_as,
            'confidence': confidence,
            'success': True
        })
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'response': 'Sorry, I encountered an error. Please try again.',
            'success': False
        }), 500


@chat_bp.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint - returns responses token by token"""
    from flask import Response, stream_with_context
    import json
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return jsonify({'error': 'Empty message', 'success': False}), 400
        
        # Import storage
        from app.chat_storage_manager import chat_storage
        
        # Save user message
        if conversation_id:
            chat_storage.add_message(conversation_id, 'user', user_message)
        
        # Get LLM client
        client = get_llm_client()
        
        # Get dataset context
        dataset_info = session.get('current_dataset', {})
        if not dataset_info:
            from app.chat_storage_manager import dataset_storage
            active = dataset_storage.get_active_dataset()
            if active:
                dataset_info = active
                session['current_dataset'] = active
        
        column_names = dataset_info.get('column_names', [])
        
        # === Use Smart Intent Detector (3-tier: Keywords -> Semantic -> LLM) ===
        from app.llm import get_intent_detector
        from pathlib import Path
        
        chromadb_path = str(Path(current_app.config.get('DATA_DIR', 'data')) / 'intent_store')
        detector = get_intent_detector(chromadb_path=chromadb_path, llm_client=client)
        intent_result = detector.detect(user_message, use_llm_fallback=True)
        
        action = intent_result.intent
        understood_as = intent_result.understood_as
        
        # Create interpretation dict for handler compatibility
        interpretation = {
            'action': action,
            'understood_as': understood_as,
            'confidence': intent_result.confidence,
            'parameters': intent_result.details or {}
        }
        
        def generate():
            """Generator function for streaming"""
            try:
                # Route to appropriate handler
                # For now, only stream general_chat and handle_general responses
                # Code generation responses are sent as complete blocks
                if action in ['descriptive_stats', 'compare_groups', 'correlation', 'regression', 'debug_error']:
                    if action == 'descriptive_stats':
                        response = handle_descriptive_stats(interpretation, client)
                    elif action == 'compare_groups':
                        response = handle_comparison(interpretation, client)
                    elif action == 'correlation':
                        response = handle_correlation(interpretation, client)
                    elif action == 'regression':
                        response = handle_code_generation("regression", client)
                    elif action == 'debug_error':
                        response = handle_error_debug(user_message, client)
                    
                    # Handle generator (streaming mode) or string
                    full_response = ""
                    import inspect
                    if inspect.isgenerator(response):
                        for chunk in response:
                            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                            full_response += chunk
                    else:
                        yield f"data: {json.dumps({'type': 'content', 'content': response})}\n\n"
                        full_response = response
                    
                    yield f"data: {json.dumps({'type': 'done', 'action': action})}\n\n"
                    
                    # Save to storage
                    if conversation_id:
                        chat_storage.add_message(conversation_id, 'assistant', full_response)
                
                else:
                    # For general chat, stream token by token
                    response_parts = []
                    understanding_prefix = ""
                    
                    # Build system prompt with context
                    system_prompt = PromptTemplates.GENERAL_ASSISTANT
                    if dataset_info and dataset_info.get('columns'):
                        cols_str = ", ".join(dataset_info.get('columns', []))
                        fname = dataset_info.get('filename', 'uploaded file')
                        system_prompt += f"""

CURRENT DATASET CONTEXT:
You have a dataset loaded named "{fname}".
Columns: {cols_str}

If the user asks to analyze this data, acknowledge the columns and ask what specific analysis they want (e.g., compare groups, correlation).
Do NOT assume dummy data. Use the column names provided above."""

                    # Use streaming from Ollama
                    stream = client.generate(
                        prompt=user_message,
                        system_prompt=system_prompt,
                        temperature=current_app.config['LLM_TEMPERATURE'],
                        stream=True  # Enable streaming
                    )
                    
                    for chunk in stream:
                        response_parts.append(chunk)
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'done', 'action': action})}\n\n"
                    
                    # Save complete response
                    full_response = ''.join(response_parts)
                    if understanding_prefix:
                        full_response = understanding_prefix + full_response
                    
                    if conversation_id:
                        chat_storage.add_message(conversation_id, 'assistant', full_response)
                        
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        
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
    """Reset decision tree and conversation"""
    decision_tree.reset()
    session.clear()
    return jsonify({'success': True, 'message': 'Reset complete'})
