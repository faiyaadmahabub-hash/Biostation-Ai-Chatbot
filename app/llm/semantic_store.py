"""
Semantic Intent Store - ChromaDB integration for learning user patterns.
Stores past queries and their resolved intents for semantic matching.
"""

import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
import time

logger = logging.getLogger(__name__)

# Try to import ChromaDB (optional dependency)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available. Semantic search disabled.")

# Try to import sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Semantic search disabled.")


class SemanticIntentStore:
    """
    ChromaDB-backed semantic store for intent learning.
    Stores user queries and their resolved intents for future matching.
    """
    
    COLLECTION_NAME = "user_intent_history"
    # Minimum similarity threshold for semantic matches
    SIMILARITY_THRESHOLD = 0.7
    
    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize semantic store.
        
        Args:
            persist_dir: Directory to persist ChromaDB data. If None, uses in-memory.
        """
        self.enabled = CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE
        self.client = None
        self.collection = None
        self.embedder = None
        
        if not self.enabled:
            logger.info("Semantic store disabled (missing dependencies)")
            return
        
        try:
            # Initialize embedding model (small, fast, good quality)
            logger.info("Loading embedding model...")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize ChromaDB
            if persist_dir:
                persist_path = Path(persist_dir)
                persist_path.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=str(persist_path),
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                self.client = chromadb.Client(
                    settings=Settings(anonymized_telemetry=False)
                )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "User intent history for semantic matching"}
            )
            
            # Pre-seed with common patterns if empty
            if self.collection.count() == 0:
                self._preseed_collection()
            
            logger.info(f"Semantic store initialized. Collection has {self.collection.count()} entries.")
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic store: {e}")
            self.enabled = False
    
    def _preseed_collection(self):
        """Pre-seed collection with common bioscience queries"""
        seed_data = [
            # Compare groups
            ("compare my treatment and control groups", "compare_groups", 1.0),
            ("is there a significant difference between groups", "compare_groups", 1.0),
            ("run anova on my data", "compare_groups", 1.0),
            ("do a t-test for me", "compare_groups", 1.0),
            ("analyze differences between samples", "compare_groups", 0.9),
            
            # Correlation
            ("check if there is a relationship between variables", "correlation", 1.0),
            ("correlate these two columns", "correlation", 1.0),
            ("is there a linear relationship", "correlation", 1.0),
            ("pearson correlation analysis", "correlation", 1.0),
            
            # Regression
            ("predict outcome based on predictors", "regression", 1.0),
            ("fit a linear model", "regression", 1.0),
            ("run regression analysis", "regression", 1.0),
            ("build a predictive model", "regression", 0.9),
            
            # Descriptive stats
            ("calculate mean and standard deviation", "descriptive_stats", 1.0),
            ("summarize my data", "descriptive_stats", 1.0),
            ("get summary statistics", "descriptive_stats", 1.0),
            ("what is the average value", "descriptive_stats", 1.0),
            
            # Explain concept
            ("what is a p-value", "explain_concept", 1.0),
            ("explain statistical significance", "explain_concept", 1.0),
            ("how does anova work", "explain_concept", 1.0),
            ("tell me about regression assumptions", "explain_concept", 1.0),
            
            # Test selection
            ("which test should i use for my data", "test_selection", 1.0),
            ("help me choose the right statistical test", "test_selection", 1.0),
            ("what analysis is appropriate", "test_selection", 1.0),
            
            # Code generation
            ("generate r code for t-test", "code_generation", 1.0),
            ("give me the code to run anova", "code_generation", 1.0),
            ("show me how to code a correlation", "code_generation", 1.0),
            
            # Visualization
            ("create a boxplot of my data", "visualization", 1.0),
            ("plot a histogram", "visualization", 1.0),
            ("make a scatter plot", "visualization", 1.0),
            
            # Debug
            ("i got an error in my r code", "debug_error", 1.0),
            ("help fix this error message", "debug_error", 1.0),
            ("my code is not working", "debug_error", 1.0),
        ]
        
        try:
            ids = [f"seed_{i}" for i in range(len(seed_data))]
            documents = [item[0] for item in seed_data]
            metadatas = [
                {"intent": item[1], "confidence": item[2], "source": "preseed"}
                for item in seed_data
            ]
            
            # Generate embeddings
            embeddings = self.embedder.encode(documents).tolist()
            
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Pre-seeded collection with {len(seed_data)} entries")
            
        except Exception as e:
            logger.error(f"Failed to pre-seed collection: {e}")
    
    def search(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Search for similar past queries.
        
        Returns:
            {
                'found': bool,
                'intent': str or None,
                'confidence': float,
                'similar_queries': list,
                'method': str
            }
        """
        if not self.enabled or not self.collection:
            return {
                'found': False,
                'intent': None,
                'confidence': 0.0,
                'similar_queries': [],
                'method': 'semantic_disabled'
            }
        
        try:
            # Generate embedding for query
            query_embedding = self.embedder.encode([query]).tolist()
            
            # Search collection
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results['documents'] or not results['documents'][0]:
                return {
                    'found': False,
                    'intent': None,
                    'confidence': 0.0,
                    'similar_queries': [],
                    'method': 'semantic_no_match'
                }
            
            # Process results - ChromaDB returns distances (lower = more similar)
            # Convert to similarity score (higher = more similar)
            similar_queries = []
            intent_votes: Dict[str, float] = {}
            
            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity (assuming cosine distance)
                similarity = 1 - (dist / 2)  # Cosine distance ranges 0-2
                
                if similarity >= self.SIMILARITY_THRESHOLD:
                    intent = meta.get('intent', 'general_chat')
                    stored_confidence = meta.get('confidence', 1.0)
                    
                    similar_queries.append({
                        'query': doc,
                        'intent': intent,
                        'similarity': similarity
                    })
                    
                    # Vote for intent weighted by similarity
                    if intent not in intent_votes:
                        intent_votes[intent] = 0
                    intent_votes[intent] += similarity * stored_confidence
            
            if not intent_votes:
                return {
                    'found': False,
                    'intent': None,
                    'confidence': 0.0,
                    'similar_queries': [],
                    'method': 'semantic_below_threshold'
                }
            
            # Find winning intent
            best_intent = max(intent_votes, key=intent_votes.get)
            best_score = intent_votes[best_intent]
            
            # Normalize confidence
            confidence = min(best_score, 1.0)
            
            return {
                'found': True,
                'intent': best_intent,
                'confidence': confidence,
                'similar_queries': similar_queries,
                'method': 'semantic_match'
            }
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {
                'found': False,
                'intent': None,
                'confidence': 0.0,
                'similar_queries': [],
                'method': 'semantic_error'
            }
    
    def store(self, query: str, intent: str, confidence: float, resolved_by: str = "llm"):
        """
        Store a query and its resolved intent for future learning.
        
        Args:
            query: User's original query
            intent: Resolved intent
            confidence: Confidence of resolution
            resolved_by: How it was resolved ('keyword', 'semantic', 'llm')
        """
        if not self.enabled or not self.collection:
            return
        
        try:
            # Generate unique ID
            doc_id = f"user_{int(time.time() * 1000)}"
            
            # Generate embedding
            embedding = self.embedder.encode([query]).tolist()
            
            # Store in collection
            self.collection.add(
                ids=[doc_id],
                documents=[query],
                embeddings=embedding,
                metadatas=[{
                    "intent": intent,
                    "confidence": confidence,
                    "source": "user",
                    "resolved_by": resolved_by,
                    "timestamp": time.time()
                }]
            )
            
            logger.debug(f"Stored query in semantic store: '{query[:50]}...' -> {intent}")
            
        except Exception as e:
            logger.error(f"Failed to store query: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the semantic store"""
        if not self.enabled or not self.collection:
            return {"enabled": False}
        
        try:
            count = self.collection.count()
            return {
                "enabled": True,
                "total_entries": count,
                "collection_name": self.COLLECTION_NAME
            }
        except:
            return {"enabled": False}
    
    def get_common_patterns(self, intent: str, min_count: int = 5) -> List[str]:
        """
        Get commonly used patterns for a specific intent.
        Useful for vocabulary expansion.
        """
        if not self.enabled or not self.collection:
            return []
        
        try:
            # Query all entries for this intent
            results = self.collection.get(
                where={"intent": intent},
                include=["documents"]
            )
            
            return results.get('documents', [])
            
        except Exception as e:
            logger.error(f"Failed to get patterns: {e}")
            return []


# Singleton instance
_store = None

def get_semantic_store(persist_dir: Optional[str] = None) -> SemanticIntentStore:
    """Get or create semantic store singleton"""
    global _store
    if _store is None:
        _store = SemanticIntentStore(persist_dir)
    return _store
