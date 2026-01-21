"""
Intent Cache - Speed up repeat queries by caching LLM interpretations
"""

import sqlite3
import json
import hashlib
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join('data', 'chats.db')

def init_cache_db():
    """Initialize intent cache table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create intent_cache table
        c.execute('''
        CREATE TABLE IF NOT EXISTS intent_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_hash TEXT UNIQUE NOT NULL,
            user_input TEXT NOT NULL,
            context_hash TEXT,
            interpretation JSON NOT NULL,
            hit_count INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Index for fast lookups
        c.execute('''
        CREATE INDEX IF NOT EXISTS idx_input_hash 
        ON intent_cache(input_hash, context_hash)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Intent cache initialized")
    except Exception as e:
        logger.error(f"Cache DB initialization error: {e}")

# Initialize on import
init_cache_db()

def _hash_input(user_input: str, context: dict = None) -> tuple:
    """Generate hash for input and context"""
    # Normalize input (lowercase, strip whitespace)
    normalized = user_input.lower().strip()
    input_hash = hashlib.md5(normalized.encode()).hexdigest()
    
    # Hash context (column names mainly)
    context_str = ""
    if context and 'columns' in context:
        context_str = ",".join(sorted(context['columns']))
    context_hash = hashlib.md5(context_str.encode()).hexdigest() if context_str else None
    
    return input_hash, context_hash

def get_cached_intent(user_input: str, context: dict = None) -> dict:
    """
    Retrieve cached interpretation
    
    Returns:
        dict: Cached interpretation or None
    """
    try:
        input_hash, context_hash = _hash_input(user_input, context)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Query with context matching
        if context_hash:
            c.execute('''
            SELECT interpretation, hit_count FROM intent_cache 
            WHERE input_hash = ? AND context_hash = ?
            ''', (input_hash, context_hash))
        else:
            c.execute('''
            SELECT interpretation, hit_count FROM intent_cache 
            WHERE input_hash = ? AND context_hash IS NULL
            ''', (input_hash,))
        
        row = c.fetchone()
        
        if row:
            # Update hit count and last_used_at
            c.execute('''
            UPDATE intent_cache 
            SET hit_count = hit_count + 1, last_used_at = ?
            WHERE input_hash = ? AND context_hash = ?
            ''', (datetime.now(), input_hash, context_hash))
            conn.commit()
            
            interpretation = json.loads(row[0])
            hit_count = row[1]
            
            logger.info(f"Cache HIT for '{user_input[:30]}...' (hits: {hit_count})")
            conn.close()
            return interpretation
        
        conn.close()
        logger.debug(f"Cache MISS for '{user_input[:30]}...'")
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving from cache: {e}")
        return None

def cache_intent(user_input: str, interpretation: dict, context: dict = None):
    """
    Store interpretation in cache
    
    Args:
        user_input: Original user message
        interpretation: LLM interpretation result
        context: Context dict (columns, etc.)
    """
    try:
        input_hash, context_hash = _hash_input(user_input, context)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Insert or update
        c.execute('''
        INSERT INTO intent_cache (input_hash, user_input, context_hash, interpretation)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(input_hash) DO UPDATE SET
            interpretation = excluded.interpretation,
            last_used_at = CURRENT_TIMESTAMP
        ''', (input_hash, user_input, context_hash, json.dumps(interpretation)))
        
        conn.commit()
        conn.close()
        logger.debug(f"Cached intent for '{user_input[:30]}...'")
        
    except Exception as e:
        logger.error(f"Error caching intent: {e}")

def clear_cache():
    """Clear all cached intents (for testing/debugging)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM intent_cache')
        conn.commit()
        conn.close()
        logger.info("Intent cache cleared")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")

def get_cache_stats() -> dict:
    """Get cache statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*), SUM(hit_count) FROM intent_cache')
        row = c.fetchone()
        
        conn.close()
        
        return {
            'total_entries': row[0] or 0,
            'total_hits': row[1] or 0
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {'total_entries': 0, 'total_hits': 0}
