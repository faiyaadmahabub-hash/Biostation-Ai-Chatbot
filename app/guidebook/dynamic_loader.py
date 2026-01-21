
import json
import os
import logging
from typing import Dict
from .knowledge_base import STATISTICAL_CONCEPTS as STATIC_CONCEPTS

logger = logging.getLogger(__name__)

# Path to custom concepts file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CUSTOM_CONCEPTS_PATH = os.path.join(BASE_DIR, "data", "knowledge", "custom_concepts.json")

def load_knowledge_base() -> Dict:
    """
    Load the full knowledge base by merging static concepts with user-defined ones.
    User-defined concepts take precedence (override static ones).
    """
    # Start with static concepts
    knowledge_base = STATIC_CONCEPTS.copy()
    
    # Load custom concepts if file exists
    if os.path.exists(CUSTOM_CONCEPTS_PATH):
        try:
            with open(CUSTOM_CONCEPTS_PATH, 'r', encoding='utf-8') as f:
                custom_concepts = json.load(f)
                
            # Merge custom concepts
            # Using update() means custom concepts with same ID will overwrite static ones
            knowledge_base.update(custom_concepts)
            logger.info(f"Loaded {len(custom_concepts)} custom concepts")
        except Exception as e:
            logger.error(f"Failed to load custom concepts: {e}")
    
    return knowledge_base

def save_custom_concept(concept_id: str, title: str, content: str, keywords: list):
    """Save a new concept or update an existing one"""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(CUSTOM_CONCEPTS_PATH), exist_ok=True)
    
    # Load existing
    custom_concepts = {}
    if os.path.exists(CUSTOM_CONCEPTS_PATH):
        try:
            with open(CUSTOM_CONCEPTS_PATH, 'r', encoding='utf-8') as f:
                custom_concepts = json.load(f)
        except:
            custom_concepts = {}
            
    # Update/Add
    from datetime import datetime
    custom_concepts[concept_id] = {
        "title": title,
        "content": content,
        "keywords": keywords,
        "added_at": datetime.now().isoformat(),
        "source": "user_teach_mode"
    }
    
    # Save back
    with open(CUSTOM_CONCEPTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(custom_concepts, f, indent=2)
        
    logger.info(f"Saved custom concept: {concept_id}")
    return True
