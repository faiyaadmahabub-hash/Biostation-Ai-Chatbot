"""
Prompt Interpreter - LLM-powered intent detection for natural language input

Handles: typos, broken English, vague requests, slang.
Returns structured JSON for deterministic routing.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


class PromptInterpreter:
    """
    Translates ANY user input into a structured command.
    No keyword matching - uses LLM understanding.
    """
    
    SYSTEM_PROMPT = '''You are a smart assistant that interprets what a bioscience student wants to do.

The student may write in broken English, use typos, or be vague. Your job is to understand their GOAL.

Available actions:
- "descriptive_stats": Calculate mean, variance, summary statistics, averages
- "compare_groups": Compare two or more groups (t-test, ANOVA, Mann-Whitney, etc.)
- "correlation": Find relationship between variables (Pearson, Spearman)
- "regression": Predict one variable from others (linear regression, GLM)
- "test_selection": Help choose the right statistical test
- "explain_concept": Explain a statistical concept or method
- "debug_error": Fix an R error or code problem
- "general_chat": General conversation, greetings, or unclear requests

Context:
- Current dataset columns: {columns}
- Recent conversation: {history}

Given the user's message, output ONLY valid JSON (no markdown, no explanation):
{{
  "understood_as": "<what you think they meant, in clear English>",
  "action": "<one of the actions above>",
  "parameters": {{
    "test_type": "<specific test if mentioned, else null>",
    "columns": ["<relevant column names if mentioned>"],
    "details": "<any other relevant extracted info>"
  }},
  "confidence": <0.0 to 1.0>
}}

Examples:
User: "do mean" -> {{"understood_as": "Calculate mean and summary statistics for the dataset", "action": "descriptive_stats", "parameters": {{"test_type": null, "columns": [], "details": "mean requested"}}, "confidence": 0.9}}
User: "compre my grops" -> {{"understood_as": "Compare groups in my data", "action": "compare_groups", "parameters": {{"test_type": null, "columns": [], "details": "group comparison"}}, "confidence": 0.85}}
User: "whats the averge of hight" -> {{"understood_as": "Calculate average of the height column", "action": "descriptive_stats", "parameters": {{"test_type": null, "columns": ["height"], "details": "average/mean"}}, "confidence": 0.9}}
User: "is there corelation" -> {{"understood_as": "Check for correlation between variables", "action": "correlation", "parameters": {{"test_type": null, "columns": [], "details": "correlation analysis"}}, "confidence": 0.85}}
User: "what test should I use" -> {{"understood_as": "Help choose the right statistical test", "action": "test_selection", "parameters": {{"test_type": null, "columns": [], "details": null}}, "confidence": 0.9}}
User: "t test plz" -> {{"understood_as": "Perform a t-test", "action": "compare_groups", "parameters": {{"test_type": "t-test", "columns": [], "details": null}}, "confidence": 0.95}}
User: "hello" -> {{"understood_as": "Greeting", "action": "general_chat", "parameters": {{"test_type": null, "columns": [], "details": null}}, "confidence": 1.0}}

IMPORTANT: Output ONLY the JSON object, nothing else.'''

    def __init__(self, llm_client):
        self.client = llm_client
    
    def interpret(self, user_message: str, context: dict = None) -> dict:
        """
        Interpret user message with caching support
        
        Args:
            user_message: Raw user input
            context: Optional context (columns, history, etc.)
        
        Returns:
            dict: Structured interpretation with action, parameters, confidence
        """
        msg_lower = user_message.lower().strip()
        
        # === QUICK-PATH: Handle common patterns instantly without LLM ===
        # Greetings
        if msg_lower in ['hi', 'hello', 'hey', 'help', 'start']:
            return {"action": "general_chat", "understood_as": "Greeting", "parameters": {}, "confidence": 1.0}
        
        # Descriptive stats keywords
        if any(kw in msg_lower for kw in ['mean', 'average', 'variance', 'summary', 'statistics', 'describe']):
            return {"action": "descriptive_stats", "understood_as": "Calculate descriptive statistics", "parameters": {}, "confidence": 0.9}
        
        # T-test keywords
        if 't-test' in msg_lower or 'ttest' in msg_lower or 't test' in msg_lower:
            return {"action": "compare_groups", "understood_as": "Perform t-test", "parameters": {"test_type": "t-test"}, "confidence": 0.95}
        
        # Correlation keywords
        if 'correlation' in msg_lower or 'correlate' in msg_lower:
            return {"action": "correlation", "understood_as": "Correlation analysis", "parameters": {}, "confidence": 0.9}
        
        # Two-Way ANOVA keywords
        if 'two way' in msg_lower or '2-way' in msg_lower or 'factorial' in msg_lower or 'interaction' in msg_lower:
             return {"action": "compare_groups", "understood_as": "Perform Two-Way ANOVA", "parameters": {"test_type": "two_way_anova"}, "confidence": 0.95}

        # ANOVA keywords
        if 'anova' in msg_lower:
            return {"action": "compare_groups", "understood_as": "Perform ANOVA", "parameters": {"test_type": "anova"}, "confidence": 0.95}
        
        # Error/debug keywords
        if any(kw in msg_lower for kw in ['error', 'error:', 'bug', 'fix', 'debug', 'not working']):
            return {"action": "debug_error", "understood_as": "Debug code error", "parameters": {}, "confidence": 0.85}
        
        # === CHECK CACHE ===
        from app.chat_storage_manager import intent_cache
        
        cached = intent_cache.get_cached_intent(user_message, context)
        if cached:
            logger.info(f"⚡ Cache hit! Skipping LLM for '{user_message[:30]}...'")
            return cached
        
        # === CACHE MISS: Call LLM ===
        logger.info(f"🔄 Cache miss. Calling LLM for '{user_message[:30]}...'")
        
        # Build context-aware prompt
        context = context or {}
        cols = context.get('column_names', context.get('columns', []))
        # Ensure cols is a list, not an integer
        if cols is None or isinstance(cols, int):
            cols = []
        columns_str = ", ".join(cols) if cols else "No dataset loaded"
        history_str = context.get('history', 'No history')
        
        strict_prompt = f"""User request: "{user_message}"
Available columns: {columns_str}
Recent Conversation:
{history_str}

Interpret this request and output ONLY JSON in this exact format:
{{
  "understood_as": "brief description",
  "action": "descriptive_stats|compare_groups|correlation|regression|test_selection|explain_concept|debug_error|general_chat",
  "parameters": {{}},
  "confidence": 0.0-1.0
}}"""
        
        response = "" # Initialize response for potential error logging
        try:
            response = self.client.generate(
                prompt=strict_prompt,
                system_prompt="You are a JSON-only API. Output ONLY valid JSON. No text.",
                temperature=0.1
            )
            
            # Robust JSON extraction
            cleaned = response.strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)
            
            result = json.loads(cleaned)
            logger.info(f"Interpreted as: {result.get('action')} (confidence: {result.get('confidence')})")
            
            # === CACHE THE RESULT ===
            intent_cache.cache_intent(user_message, result, context)
            
            return result
            
        except Exception as e:
            logger.warning(f"Interpreter failed: {e}. Response was: {response[:100]}...")
            # Fallback based on simple keywords if LLM fails
            msg_lower = user_message.lower()
            if 'mean' in msg_lower or 'variance' in msg_lower:
                return {"action": "descriptive_stats", "understood_as": "Calculated statistics", "confidence": 0.5}
            
            return {
                "understood_as": user_message,
                "action": "general_chat",
                "parameters": {},
                "confidence": 0.0
            }


def create_interpreter(llm_client) -> PromptInterpreter:
    """Factory function to create interpreter instance"""
    return PromptInterpreter(llm_client)
