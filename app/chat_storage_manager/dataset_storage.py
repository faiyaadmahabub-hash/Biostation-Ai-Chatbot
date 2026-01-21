"""
Dataset Storage - Manage persistent dataset metadata
"""

import sqlite3
import json
import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join('data', 'chats.db')

def init_db():
    """Initialize dataset table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create datasets table
        c.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            columns JSON,
            row_count INTEGER,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

# Initialize on import
init_db()

def save_dataset(filename, filepath, columns, row_count):
    """Save dataset metadata to DB and mark as active (latest)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Deactivate all previous datasets
        c.execute('UPDATE datasets SET is_active = 0')
        
        # Insert new active dataset
        c.execute('''
        INSERT INTO datasets (filename, filepath, columns, row_count, uploaded_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        ''', (filename, filepath, json.dumps(columns), row_count, datetime.now()))
        
        dataset_id = c.lastrowid
        conn.commit()
        conn.close()
        return dataset_id
    except Exception as e:
        logger.error(f"Error saving dataset: {e}")
        return None

def get_active_dataset():
    """Get the currently active dataset"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
        SELECT filename, filepath, columns, row_count
        FROM datasets
        WHERE is_active = 1
        ORDER BY uploaded_at DESC
        LIMIT 1
        ''')
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'filename': row[0],
                'filepath': row[1],
                'column_names': json.loads(row[2]),
                'rows': row[3]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting active dataset: {e}")
        return None
