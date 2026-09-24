
from flask import Blueprint, request, jsonify
from app.guidebook.dynamic_loader import (
    save_custom_concept,
    save_custom_test,
    validate_r_syntax
)
import uuid
import logging

learner_bp = Blueprint('learner', __name__)
logger = logging.getLogger(__name__)


@learner_bp.route('/teach', methods=['POST'])
def teach_bot():
    """
    Endpoint for users to add new statistical tests with R templates.

    Expected JSON:
    {
        "name": str,           # Test name (e.g., "Friedman Test")
        "keywords": list[str], # Trigger keywords
        "purpose": str,        # One-line description
        "explanation": str,    # Full explanation (markdown) - AI interpretation context
        "assumptions": str,    # Assumptions (markdown) - AI assumptions context
        "r_code": str          # R code template with placeholders
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract fields
        name = data.get('name', '').strip()
        keywords_raw = data.get('keywords', [])
        purpose = data.get('purpose', '').strip()
        explanation = data.get('explanation', '').strip()
        assumptions = data.get('assumptions', '').strip()
        r_code = data.get('r_code', '').strip()

        # Validate required fields
        if not name:
            return jsonify({'error': 'Test name is required'}), 400
        if not explanation:
            return jsonify({'error': 'Explanation is required (used for AI interpretation)'}), 400
        if not r_code:
            return jsonify({'error': 'R code template is required'}), 400

        # Process keywords
        if isinstance(keywords_raw, str):
            keywords = [k.strip().lower() for k in keywords_raw.split(',') if k.strip()]
        else:
            keywords = [k.strip().lower() for k in keywords_raw if k.strip()]

        # Add test name to keywords if not present
        name_lower = name.lower()
        if name_lower not in keywords:
            keywords.append(name_lower)

        # Generate unique test ID
        test_id = f"custom_{str(uuid.uuid4())[:8]}"

        # Validate R syntax before saving
        is_valid, error = validate_r_syntax(r_code)
        if not is_valid:
            return jsonify({
                'error': f'R code validation failed: {error}',
                'validation_error': True
            }), 400

        # Save the test
        success, error = save_custom_test(
            test_id=test_id,
            name=name,
            keywords=keywords,
            purpose=purpose or f"Perform {name} analysis",
            explanation=explanation,
            assumptions=assumptions or "No specific assumptions provided.",
            r_template=r_code
        )

        if success:
            # Refresh caches so the new test is immediately available
            _refresh_caches()

            return jsonify({
                'success': True,
                'message': f'Statistical test "{name}" learned successfully!',
                'test_id': test_id,
                'keywords': keywords
            })
        else:
            return jsonify({'error': error or 'Failed to save test'}), 500

    except Exception as e:
        logger.error(f"Error in teach_bot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _refresh_caches():
    """Refresh template and test mapping caches after adding a new test."""
    try:
        from app.code_gen.template_loader import refresh_template_loader
        from app.handlers.base import refresh_test_mapping, clear_code_cache
        refresh_template_loader()
        refresh_test_mapping()
        clear_code_cache()
        logger.info("Refreshed template and test mapping caches")
    except ImportError as e:
        logger.warning(f"Could not refresh caches: {e}")


@learner_bp.route('/teach/tests', methods=['GET'])
def list_custom_tests():
    """
    List all custom tests the user has taught.
    Returns summary info for each test.
    """
    try:
        from app.guidebook.dynamic_loader import load_custom_tests
        tests = load_custom_tests()

        # Return summary list
        test_list = []
        for test_id, test_data in tests.items():
            test_list.append({
                'id': test_id,
                'name': test_data.get('name', 'Unknown'),
                'category': test_data.get('category', 'other'),
                'keywords': test_data.get('keywords', []),
                'purpose': test_data.get('purpose', ''),
                'added_at': test_data.get('added_at', '')
            })

        # Sort by added_at descending (newest first)
        test_list.sort(key=lambda x: x.get('added_at', ''), reverse=True)

        return jsonify({
            'success': True,
            'tests': test_list,
            'count': len(test_list)
        })
    except Exception as e:
        logger.error(f"Error listing custom tests: {e}")
        return jsonify({'error': str(e)}), 500


@learner_bp.route('/teach/tests/<test_id>', methods=['GET'])
def get_custom_test(test_id):
    """
    Get full details of a specific custom test for editing.
    """
    try:
        from app.guidebook.dynamic_loader import load_custom_tests
        tests = load_custom_tests()

        if test_id not in tests:
            return jsonify({'error': 'Test not found'}), 404

        test_data = tests[test_id]
        return jsonify({
            'success': True,
            'test': {
                'id': test_id,
                'name': test_data.get('name', ''),
                'category': test_data.get('category', 'other'),
                'keywords': test_data.get('keywords', []),
                'purpose': test_data.get('purpose', ''),
                'explanation': test_data.get('explanation', ''),
                'assumptions': test_data.get('assumptions', ''),
                'r_template': test_data.get('r_template', ''),
                'r_packages': test_data.get('r_packages', []),
                'added_at': test_data.get('added_at', '')
            }
        })
    except Exception as e:
        logger.error(f"Error getting custom test: {e}")
        return jsonify({'error': str(e)}), 500


@learner_bp.route('/teach/tests/<test_id>', methods=['PUT'])
def update_custom_test(test_id):
    """
    Update an existing custom test.
    """
    try:
        from app.guidebook.dynamic_loader import load_custom_tests, save_custom_test
        tests = load_custom_tests()

        if test_id not in tests:
            return jsonify({'error': 'Test not found'}), 404

        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract fields (use existing values as defaults)
        existing = tests[test_id]
        name = data.get('name', existing.get('name', '')).strip()
        keywords_raw = data.get('keywords', existing.get('keywords', []))
        purpose = data.get('purpose', existing.get('purpose', '')).strip()
        explanation = data.get('explanation', existing.get('explanation', '')).strip()
        assumptions = data.get('assumptions', existing.get('assumptions', '')).strip()
        r_code = data.get('r_code', existing.get('r_template', '')).strip()

        # Validate required fields
        if not name:
            return jsonify({'error': 'Test name is required'}), 400
        if not r_code:
            return jsonify({'error': 'R code template is required'}), 400

        # Process keywords
        if isinstance(keywords_raw, str):
            keywords = [k.strip().lower() for k in keywords_raw.split(',') if k.strip()]
        else:
            keywords = [k.strip().lower() for k in keywords_raw if k.strip()]

        # Validate R syntax
        is_valid, error = validate_r_syntax(r_code)
        if not is_valid:
            return jsonify({
                'error': f'R code validation failed: {error}',
                'validation_error': True
            }), 400

        # Save updated test (reuses existing test_id)
        success, error = save_custom_test(
            test_id=test_id,
            name=name,
            keywords=keywords,
            purpose=purpose or f"Perform {name} analysis",
            explanation=explanation,
            assumptions=assumptions or "No specific assumptions provided.",
            r_template=r_code
        )

        if success:
            _refresh_caches()
            return jsonify({
                'success': True,
                'message': f'Test "{name}" updated successfully!',
                'test_id': test_id
            })
        else:
            return jsonify({'error': error or 'Failed to update test'}), 500

    except Exception as e:
        logger.error(f"Error updating custom test: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@learner_bp.route('/teach/tests/<test_id>', methods=['DELETE'])
def delete_custom_test(test_id):
    """
    Delete a custom test.
    """
    try:
        from app.guidebook.dynamic_loader import delete_custom_test as do_delete

        success, error = do_delete(test_id)

        if success:
            _refresh_caches()
            return jsonify({
                'success': True,
                'message': 'Test deleted successfully'
            })
        else:
            return jsonify({'error': error or 'Failed to delete test'}), 500

    except Exception as e:
        logger.error(f"Error deleting custom test: {e}")
        return jsonify({'error': str(e)}), 500


@learner_bp.route('/teach/refresh-cache', methods=['POST'])
def refresh_cache():
    """
    Manually refresh all caches for custom tests.
    Useful when templates are modified directly in JSON files.
    """
    try:
        _refresh_caches()
        return jsonify({
            'success': True,
            'message': 'All caches refreshed successfully'
        })
    except Exception as e:
        logger.error(f"Error refreshing caches: {e}")
        return jsonify({'error': str(e)}), 500


@learner_bp.route('/teach/validate', methods=['POST'])
def validate_r_code():
    """
    Endpoint to validate R code syntax without saving.
    Useful for live validation in the UI.

    Expected JSON: { "r_code": str }
    """
    try:
        data = request.json
        if not data or 'r_code' not in data:
            return jsonify({'error': 'No R code provided'}), 400

        r_code = data['r_code']
        is_valid, error = validate_r_syntax(r_code)

        return jsonify({
            'valid': is_valid,
            'error': error
        })

    except Exception as e:
        logger.error(f"Error validating R code: {e}")
        return jsonify({'error': str(e)}), 500
