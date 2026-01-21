"""
Chat History Storage - SQLite-based chat persistence
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Single message in a conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str


@dataclass
class Conversation:
    """A conversation with messages"""
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage]


class ChatStorage:
    """SQLite-based chat storage"""
    
    def __init__(self, db_path: str = None):
        # Use absolute path based on project directory
        if db_path is None:
            from config import get_config
            db_path = str(get_config().SQLITE_DB_PATH)
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        logger.info(f"Chat storage database: {self.db_path}")
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_conversation(self, title: str = "New Chat") -> str:
        """Create a new conversation and return its ID"""
        import uuid
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)',
            (conv_id, title, now, now)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Created conversation: {conv_id}")
        return conv_id
    
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to a conversation"""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add message
        cursor.execute(
            'INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
            (conversation_id, role, content, now)
        )
        
        # Update conversation timestamp
        cursor.execute(
            'UPDATE conversations SET updated_at = ? WHERE id = ?',
            (now, conversation_id)
        )
        
        # Auto-generate title from first user message if title is default
        cursor.execute('SELECT title FROM conversations WHERE id = ?', (conversation_id,))
        result = cursor.fetchone()
        if result and result[0] == "New Chat" and role == "user":
            # Generate title from first ~40 chars of message
            new_title = content[:40].strip()
            if len(content) > 40:
                new_title += "..."
            cursor.execute(
                'UPDATE conversations SET title = ? WHERE id = ?',
                (new_title, conversation_id)
            )
        
        conn.commit()
        conn.close()
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation with all its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get conversation
        cursor.execute(
            'SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?',
            (conversation_id,)
        )
        conv_row = cursor.fetchone()
        
        if not conv_row:
            conn.close()
            return None
        
        # Get messages
        cursor.execute(
            'SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY id',
            (conversation_id,)
        )
        messages = [
            ChatMessage(role=row[0], content=row[1], timestamp=row[2])
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return Conversation(
            id=conv_row[0],
            title=conv_row[1],
            created_at=conv_row[2],
            updated_at=conv_row[3],
            messages=messages
        )
    
    def get_all_conversations(self) -> List[Dict]:
        """Get all conversations (metadata only, no messages)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, created_at, updated_at 
            FROM conversations 
            ORDER BY updated_at DESC
        ''')
        
        conversations = []
        now = datetime.now()
        
        for row in cursor.fetchall():
            updated = datetime.fromisoformat(row[3])
            
            # Determine time group
            if updated.date() == now.date():
                time_group = "Today"
            elif updated.date() == (now - timedelta(days=1)).date():
                time_group = "Yesterday"
            elif updated >= now - timedelta(days=7):
                time_group = "Previous 7 Days"
            elif updated >= now - timedelta(days=30):
                time_group = "Previous 30 Days"
            else:
                time_group = updated.strftime("%B %Y")
            
            conversations.append({
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'time_group': time_group
            })
        
        conn.close()
        return conversations
    
    def update_title(self, conversation_id: str, new_title: str) -> bool:
        """Update conversation title"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE conversations SET title = ? WHERE id = ?',
            (new_title, conversation_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete messages first
        cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        
        # Delete conversation
        cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted conversation: {conversation_id}")
        return success
    
    def clear_all(self) -> None:
        """Clear all conversations (for testing)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        cursor.execute('DELETE FROM conversations')
        conn.commit()
        conn.close()


# Singleton instance
chat_storage = ChatStorage()
