"""
Smart Intent Detector - 3-Tier Intent Detection System

Tier 1: Static keyword matching (instant, ~80% of queries)
Tier 2: ChromaDB semantic search (~0.5s, ~15% of queries)
Tier 3: LLM fallback (~30s, ~5% of queries)

The system learns over time by storing LLM resolutions in ChromaDB.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from .keywords import get_keyword_matcher, StaticKeywordMatcher
from .semantic_store import get_semantic_store, SemanticIntentStore

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result of intent detection"""
    intent: str
    confidence: float
    method: str  # 'keyword', 'semantic', 'llm', 'fallback'
    understood_as: str  # Human-readable description of what was understood
    details: Dict[str, Any] = None
    
    def to_dict(self) -> dict:
        return {
            'intent': self.intent,
            'confidence': self.confidence,
            'method': self.method,
            'understood_as': self.understood_as,
            'details': self.details or {}
        }


# Intent to human-readable descriptions
INTENT_DESCRIPTIONS = {
    'compare_groups': "Comparing groups or testing for differences",
    'correlation': "Analyzing relationship between variables",
    'regression': "Building a predictive model",
    'descriptive_stats': "Calculating summary statistics",
    'categorical_test': "Testing categorical/frequency data",
    'normality_test': "Checking data distribution normality",
    'explain_concept': "Explaining a statistical concept",
    'test_selection': "Helping choose the right test",
    'code_generation': "Generating R code for analysis",
    'debug_error': "Debugging an error or problem",
    'data_operation': "Data loading or manipulation",
    'visualization': "Creating plots or charts",
    'power_analysis': "Sample size or power calculation",
    'post_hoc': "Post-hoc or pairwise comparisons",
    'survival_analysis': "Time-to-event analysis",
    'general_chat': "General question or conversation",
}


class SmartIntentDetector:
    """
    3-tier intelligent intent detection system.
    
    Flow:
    1. Try static keyword matching (instant)
    2. If no match, try semantic search in ChromaDB (~0.5s)
    3. If still no match, fall back to LLM (~30s)
    4. Store LLM result in ChromaDB for future learning
    """
    
    # Confidence thresholds
    KEYWORD_CONFIDENCE_THRESHOLD = 0.5  # Minimum for keyword match
    SEMANTIC_CONFIDENCE_THRESHOLD = 0.6  # Minimum for semantic match
    
    def __init__(self, 
                 chromadb_path: Optional[str] = None,
                 llm_client = None):
        """
        Initialize smart intent detector.
        
        Args:
            chromadb_path: Path to persist ChromaDB data
            llm_client: OllamaClient for Tier 3 fallback
        """
        self.keyword_matcher = get_keyword_matcher()
        self.semantic_store = get_semantic_store(chromadb_path)
        self.llm_client = llm_client
        
        logger.info("SmartIntentDetector initialized")
        logger.info(f"  Keyword matcher: Ready ({len(self.keyword_matcher.get_all_keywords())} keywords)")
        logger.info(f"  Semantic store: {'Enabled' if self.semantic_store.enabled else 'Disabled'}")
        logger.info(f"  LLM fallback: {'Available' if llm_client else 'Not configured'}")
    
    def detect(self, query: str, use_llm_fallback: bool = True) -> IntentResult:
        """
        Detect intent using 3-tier cascade.
        
        Args:
            query: User's message
            use_llm_fallback: Whether to use LLM if other methods fail
            
        Returns:
            IntentResult with intent, confidence, and method used
        """
        query = query.strip()
        if not query:
            return IntentResult(
                intent='general_chat',
                confidence=0.0,
                method='empty',
                understood_as="Empty message"
            )
        
        # ===== TIER 1: Static Keyword Matching =====
        logger.debug(f"Tier 1: Keyword matching for '{query[:50]}...'")
        keyword_result = self.keyword_matcher.match(query)
        
        if keyword_result['intent'] and keyword_result['confidence'] >= self.KEYWORD_CONFIDENCE_THRESHOLD:
            intent = keyword_result['intent']
            logger.info(f"Tier 1 HIT: '{query[:30]}...' -> {intent} (conf: {keyword_result['confidence']:.2f})")
            
            return IntentResult(
                intent=intent,
                confidence=keyword_result['confidence'],
                method='keyword',
                understood_as=INTENT_DESCRIPTIONS.get(intent, "Request understood"),
                details={'matches': keyword_result['matches']}
            )
        
        # ===== TIER 2: Semantic Search =====
        if self.semantic_store.enabled:
            logger.debug(f"Tier 2: Semantic search for '{query[:50]}...'")
            semantic_result = self.semantic_store.search(query)
            
            if semantic_result['found'] and semantic_result['confidence'] >= self.SEMANTIC_CONFIDENCE_THRESHOLD:
                intent = semantic_result['intent']
                logger.info(f"Tier 2 HIT: '{query[:30]}...' -> {intent} (conf: {semantic_result['confidence']:.2f})")
                
                return IntentResult(
                    intent=intent,
                    confidence=semantic_result['confidence'],
                    method='semantic',
                    understood_as=INTENT_DESCRIPTIONS.get(intent, "Similar to past queries"),
                    details={'similar_queries': semantic_result['similar_queries']}
                )
        
        # ===== TIER 3: LLM Fallback =====
        if use_llm_fallback and self.llm_client:
            logger.debug(f"Tier 3: LLM fallback for '{query[:50]}...'")
            llm_result = self._llm_interpret(query)
            
            if llm_result['intent']:
                intent = llm_result['intent']
                confidence = llm_result.get('confidence', 0.8)
                
                logger.info(f"Tier 3 HIT: '{query[:30]}...' -> {intent} (conf: {confidence:.2f})")
                
                # Store in semantic store for future learning
                if self.semantic_store.enabled:
                    self.semantic_store.store(
                        query=query,
                        intent=intent,
                        confidence=confidence,
                        resolved_by='llm'
                    )
                
                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    method='llm',
                    understood_as=llm_result.get('understood_as', INTENT_DESCRIPTIONS.get(intent, "Request analyzed")),
                    details=llm_result
                )
        
        # ===== FALLBACK: General chat =====
        logger.info(f"No match found for '{query[:30]}...', falling back to general_chat")
        return IntentResult(
            intent='general_chat',
            confidence=0.3,
            method='fallback',
            understood_as="General question or conversation"
        )
    
    def _llm_interpret(self, query: str) -> Dict[str, Any]:
        """Use LLM to interpret intent (slowest but smartest)"""
        if not self.llm_client:
            return {'intent': None}
        
        try:
            # Import the prompt interpreter for LLM-based detection
            from .prompt_interpreter import PromptInterpreter
            
            interpreter = PromptInterpreter(self.llm_client)
            result = interpreter.interpret(query)
            
            return {
                'intent': result.get('action', 'general_chat'),
                'confidence': result.get('confidence', 0.8),
                'understood_as': result.get('understood_as', ''),
                'parameters': result.get('parameters', {})
            }
            
        except Exception as e:
            logger.error(f"LLM interpretation failed: {e}")
            return {'intent': None}
    
    def set_llm_client(self, client):
        """Set or update the LLM client"""
        self.llm_client = client
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the detector"""
        return {
            'keyword_count': len(self.keyword_matcher.get_all_keywords()),
            'semantic_store': self.semantic_store.get_stats(),
            'llm_available': self.llm_client is not None
        }
    
    def learn_from_feedback(self, query: str, correct_intent: str, confidence: float = 1.0):
        """
        Learn from user feedback (e.g., when user corrects the system).
        Stores the correct mapping for future use.
        """
        if self.semantic_store.enabled:
            self.semantic_store.store(
                query=query,
                intent=correct_intent,
                confidence=confidence,
                resolved_by='user_feedback'
            )
            logger.info(f"Learned from feedback: '{query[:30]}...' -> {correct_intent}")


# Singleton instance
_detector = None

def get_intent_detector(chromadb_path: Optional[str] = None, llm_client = None) -> SmartIntentDetector:
    """Get or create smart intent detector singleton"""
    global _detector
    if _detector is None:
        _detector = SmartIntentDetector(chromadb_path, llm_client)
    elif llm_client and not _detector.llm_client:
        _detector.set_llm_client(llm_client)
    return _detector


def detect_intent(query: str, llm_client = None, use_llm_fallback: bool = True) -> IntentResult:
    """
    Convenience function for detecting intent.
    
    Args:
        query: User message
        llm_client: Optional LLM client for fallback
        use_llm_fallback: Whether to use LLM if other methods fail
        
    Returns:
        IntentResult
    """
    detector = get_intent_detector(llm_client=llm_client)
    return detector.detect(query, use_llm_fallback=use_llm_fallback)
