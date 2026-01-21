"""
History routes - API for chat history management
"""

from flask import Blueprint, request, jsonify
from app.chat_storage_manager import chat_storage
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)

history_bp = Blueprint('history', __name__)


@history_bp.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for sidebar"""
    try:
        conversations = chat_storage.get_all_conversations()
        return jsonify({
            'success': True,
            'conversations': conversations
        })
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json() or {}
        title = data.get('title', 'New Chat')
        
        conv_id = chat_storage.create_conversation(title)
        
        return jsonify({
            'success': True,
            'conversation_id': conv_id
        })
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/conversations/<conv_id>', methods=['GET'])
def get_conversation(conv_id):
    """Get a specific conversation with messages"""
    try:
        conversation = chat_storage.get_conversation(conv_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at,
                'updated_at': conversation.updated_at,
                'messages': [
                    {'role': m.role, 'content': m.content, 'timestamp': m.timestamp}
                    for m in conversation.messages
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error getting conversation {conv_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/conversations/<conv_id>', methods=['PUT'])
def update_conversation(conv_id):
    """Update conversation title"""
    try:
        data = request.get_json()
        new_title = data.get('title')
        
        if not new_title:
            return jsonify({'success': False, 'error': 'Title required'}), 400
        
        success = chat_storage.update_title(conv_id, new_title)
        
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error updating conversation {conv_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/api/conversations/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    """Delete a conversation"""
    try:
        success = chat_storage.delete_conversation(conv_id)
        
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error deleting conversation {conv_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
