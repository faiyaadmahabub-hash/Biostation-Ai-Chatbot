"""
Dataset Storage - Manage persistent dataset metadata and previews
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

        # Add preview_data column if it doesn't exist (migration)
        try:
            c.execute('ALTER TABLE datasets ADD COLUMN preview_data JSON')
        except sqlite3.OperationalError:
            # Column already exists
            pass

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

# Initialize on import
init_db()

def save_dataset(filename, filepath, columns, row_count, preview_data=None):
    """Save dataset metadata to DB and mark as active (latest)

    Args:
        filename: Name of the uploaded file
        filepath: Path to the saved file
        columns: List of column names
        row_count: Number of rows in dataset
        preview_data: Optional dict containing preview information
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Deactivate all previous datasets
        c.execute('UPDATE datasets SET is_active = 0')

        # Insert new active dataset with preview
        c.execute('''
        INSERT INTO datasets (filename, filepath, columns, row_count, uploaded_at, is_active, preview_data)
        VALUES (?, ?, ?, ?, ?, 1, ?)
        ''', (filename, filepath, json.dumps(columns), row_count, datetime.now(),
              json.dumps(preview_data) if preview_data else None))

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


def get_dataset_preview():
    """Get the preview data for the currently active dataset"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('''
        SELECT filename, filepath, preview_data
        FROM datasets
        WHERE is_active = 1
        ORDER BY uploaded_at DESC
        LIMIT 1
        ''')

        row = c.fetchone()
        conn.close()

        if row:
            preview_data = json.loads(row[2]) if row[2] else None
            return {
                'success': True,
                'filename': row[0],
                'filepath': row[1],
                'preview': preview_data
            }
        return {
            'success': False,
            'error': 'No active dataset found'
        }
    except Exception as e:
        logger.error(f"Error getting dataset preview: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def update_dataset_preview(preview_data):
    """Update the preview data for the currently active dataset"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('''
        UPDATE datasets
        SET preview_data = ?
        WHERE is_active = 1
        ''', (json.dumps(preview_data),))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating dataset preview: {e}")
        return False
