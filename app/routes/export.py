"""
Export routes - Download R scripts and results
"""

from flask import Blueprint, request, jsonify, Response
from app.code_gen import code_generator
from app.advisor import get_test_info
import logging

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)


@export_bp.route('/api/export/r-code/<test_id>', methods=['GET'])
def export_r_code(test_id):
    """Export R code as downloadable file"""
    try:
        test_info = get_test_info(test_id)
        if not test_info:
            return jsonify({'success': False, 'error': 'Unknown test'}), 404
        
        code = code_generator.generate_code(test_id)
        
        # Create filename
        filename = f"{test_id.replace('_', '-')}_analysis.R"
        
        # Return as downloadable file
        return Response(
            code,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
    except Exception as e:
        logger.error(f"Error exporting R code: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/api/export/code', methods=['POST'])
def export_custom_code():
    """Export custom R code from chat"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        filename = data.get('filename', 'analysis.R')
        
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400
        
        return Response(
            code,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
    except Exception as e:
        logger.error(f"Error exporting custom code: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@export_bp.route('/api/available-tests', methods=['GET'])
def get_available_tests():
    """Get list of available tests for code generation"""
    from app.advisor import STATISTICAL_TESTS
    
    tests = [
        {
            'id': test_id,
            'name': test.name,
            'category': test.category,
            'purpose': test.purpose
        }
        for test_id, test in STATISTICAL_TESTS.items()
    ]
    
    return jsonify({
        'success': True,
        'tests': tests
    })


@export_bp.route('/api/guidebook/topics', methods=['GET'])
def get_guidebook_topics():
    """Get list of available guidebook topics"""
    from app.guidebook import get_all_topics
    
    topics = get_all_topics()
    
    return jsonify({
        'success': True,
        'topics': topics
    })
