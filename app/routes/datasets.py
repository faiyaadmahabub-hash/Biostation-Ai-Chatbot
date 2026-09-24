"""
Dataset routes - API for built-in dataset library

Provides endpoints to:
- List available datasets
- Get dataset details
- Load datasets for analysis
- Search datasets
"""

from flask import Blueprint, request, jsonify, session
import logging

logger = logging.getLogger(__name__)

datasets_bp = Blueprint('datasets', __name__)


@datasets_bp.route('/api/datasets', methods=['GET'])
def list_datasets():
    """
    List all available built-in datasets.

    Query params:
        tags: Comma-separated list of tags to filter by
        difficulty: Filter by difficulty level (beginner, intermediate, advanced)

    Returns:
        List of dataset summaries
    """
    try:
        from app.datasets import get_dataset_registry
        registry = get_dataset_registry()

        # Parse query params
        tags = request.args.get('tags')
        tags_list = tags.split(',') if tags else None
        difficulty = request.args.get('difficulty')

        datasets = registry.list_datasets(tags=tags_list, difficulty=difficulty)

        return jsonify({
            'success': True,
            'datasets': datasets,
            'count': len(datasets)
        })

    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@datasets_bp.route('/api/datasets/<dataset_id>', methods=['GET'])
def get_dataset_details(dataset_id):
    """
    Get detailed information about a specific dataset.

    Returns:
        Dataset details including variables and suggested analyses
    """
    try:
        from app.datasets import get_dataset_registry
        registry = get_dataset_registry()

        details = registry.get_dataset_details(dataset_id)

        if not details:
            return jsonify({
                'success': False,
                'error': f'Dataset not found: {dataset_id}'
            }), 404

        return jsonify({
            'success': True,
            'dataset': details
        })

    except Exception as e:
        logger.error(f"Error getting dataset details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@datasets_bp.route('/api/datasets/<dataset_id>/load', methods=['POST'])
def load_dataset(dataset_id):
    """
    Load a built-in dataset for analysis.

    This saves the dataset to the user's data directory and sets it as
    the active dataset for analysis.

    Returns:
        Dataset info and preview data
    """
    try:
        from app.datasets import get_dataset_loader, get_dataset_registry
        from app.chat_storage_manager import dataset_storage
        from app.preview import DataPreviewGenerator

        loader = get_dataset_loader()
        registry = get_dataset_registry()

        # Get dataset info
        info = registry.get_dataset_info(dataset_id)
        if not info:
            return jsonify({
                'success': False,
                'error': f'Dataset not found: {dataset_id}'
            }), 404

        # Load and save the dataset
        filepath = loader.save_as_user_dataset(dataset_id)
        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Failed to load dataset'
            }), 500

        # Load DataFrame for preview
        df = loader.load_dataset(dataset_id)
        if df is None:
            return jsonify({
                'success': False,
                'error': 'Failed to load dataset'
            }), 500

        # Generate preview
        preview_generator = DataPreviewGenerator(df)
        preview_data = preview_generator.generate_preview(n_rows=10)

        # Get column names
        column_names = df.columns.tolist()
        rows, cols = df.shape

        # Save to persistent storage
        filename = f"{dataset_id}.csv"
        dataset_storage.save_dataset(filename, filepath, column_names, rows, preview_data)

        # Update session
        session['current_dataset'] = {
            'filename': filename,
            'filepath': filepath,
            'rows': rows,
            'columns': cols,
            'column_names': column_names
        }
        session.modified = True

        return jsonify({
            'success': True,
            'message': f'Loaded {info.name}',
            'dataset': {
                'id': dataset_id,
                'name': info.name,
                'filename': filename,
                'filepath': filepath,
                'rows': rows,
                'columns': cols,
                'column_names': column_names
            },
            'preview': preview_data,
            'suggested_analyses': [
                {
                    'type': a.type.value,
                    'title': a.title,
                    'description': a.description,
                    'query_example': a.query_example,
                }
                for a in info.suggested_analyses
            ]
        })

    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@datasets_bp.route('/api/datasets/<dataset_id>/preview', methods=['GET'])
def get_dataset_preview(dataset_id):
    """
    Get a preview of a built-in dataset without loading it.

    Returns:
        Preview data including first rows and column info
    """
    try:
        from app.datasets import get_dataset_loader

        loader = get_dataset_loader()
        preview = loader.get_dataset_preview(dataset_id, n_rows=10)

        if not preview:
            return jsonify({
                'success': False,
                'error': f'Dataset not found: {dataset_id}'
            }), 404

        return jsonify({
            'success': True,
            'preview': preview
        })

    except Exception as e:
        logger.error(f"Error getting dataset preview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@datasets_bp.route('/api/datasets/search', methods=['GET'])
def search_datasets():
    """
    Search datasets by query string.

    Query params:
        q: Search query

    Returns:
        List of matching datasets sorted by relevance
    """
    try:
        from app.datasets import get_dataset_registry
        registry = get_dataset_registry()

        query = request.args.get('q', '')
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query required'
            }), 400

        results = registry.search_datasets(query)

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        logger.error(f"Error searching datasets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@datasets_bp.route('/api/datasets/tags', methods=['GET'])
def get_dataset_tags():
    """
    Get all available dataset tags.

    Returns:
        List of unique tags across all datasets
    """
    try:
        from app.datasets import get_dataset_registry
        registry = get_dataset_registry()

        all_tags = set()
        for dataset in registry.list_datasets():
            all_tags.update(dataset.get('tags', []))

        return jsonify({
            'success': True,
            'tags': sorted(list(all_tags))
        })

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
