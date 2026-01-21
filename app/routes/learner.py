
from flask import Blueprint, request, jsonify
from app.guidebook.dynamic_loader import save_custom_concept
import uuid
import logging

learner_bp = Blueprint('learner', __name__)
logger = logging.getLogger(__name__)

@learner_bp.route('/teach', methods=['POST'])
def teach_bot():
    """
    Endpoint for users to add new knowledge to the chatbot.
    Expected JSON: { "title": str, "content": str, "keywords": list[str] }
    """
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Missing title or content'}), 400
            
        title = data['title']
        content = data['content']
        keywords = data.get('keywords', [])
        
        # Generate a unique ID for this concept
        concept_id = f"custom_{str(uuid.uuid4())[:8]}"
        
        # Add title to keywords if not present
        if title.lower() not in [k.lower() for k in keywords]:
            keywords.append(title.lower())
            
        # Save the concept
        if save_custom_concept(concept_id, title, content, keywords):
            return jsonify({
                'success': True,
                'message': f'Concept "{title}" learned successfully!',
                'concept_id': concept_id
            })
        else:
            return jsonify({'error': 'Failed to save concept'}), 500
            
    except Exception as e:
        logger.error(f"Error in teach_bot: {e}")
        return jsonify({'error': str(e)}), 500
