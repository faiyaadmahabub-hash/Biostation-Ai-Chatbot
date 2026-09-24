"""
R Execution routes - API for running R code and code explanation
"""

import json
from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context, current_app
import os
import logging

logger = logging.getLogger(__name__)

r_exec_bp = Blueprint('r_exec', __name__)


@r_exec_bp.route('/api/run-code', methods=['POST'])
def run_r_code():
    """Execute R code and return results"""
    try:
        from app.r_engine import r_executor, output_parser, analyze_r_error
        from flask import session

        data = request.get_json()
        code = data.get('code', '')

        if not code.strip():
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400

        # Check if R is available
        if not r_executor.available:
            return jsonify({
                'success': False,
                'error': 'R execution not available. rpy2 is not installed or R is not configured.',
                'output': '',
                'warnings': ''
            })

        # Execute the code
        result = r_executor.execute(code, capture_plots=True)

        # Extract statistics if present
        stats = output_parser.extract_statistics(result.output)
        interpretation = ""
        if 'p_value' in stats:
            interpretation = output_parser.interpret_p_value(stats['p_value'])

        # Build response
        response_data = {
            'success': result.success,
            'output': result.output,
            'errors': result.errors,
            'warnings': result.warnings,
            'plots': [os.path.basename(p) for p in result.plots],
            'statistics': stats,
            'interpretation': interpretation
        }

        # If execution failed, add error analysis with fix suggestions
        if not result.success and result.errors:
            # Get dataset info from session for context
            dataset_info = {
                'column_names': session.get('column_names', []),
                'filename': session.get('uploaded_filename', 'data'),
                'file_path': session.get('uploaded_file_path', '')
            }

            # Analyze the error and get suggestions
            error_analysis = analyze_r_error(
                error=result.errors,
                code=code,
                dataset_info=dataset_info
            )
            response_data['analysis'] = error_analysis
            logger.info(f"Error analysis: {error_analysis.get('error_type', 'unknown')}")

        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"R execution error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@r_exec_bp.route('/api/plot/<filename>')
def get_plot(filename):
    """Serve a generated plot image"""
    try:
        from app.r_engine import r_executor
        
        plot_path = os.path.join(r_executor.plot_dir, filename)
        
        if not os.path.exists(plot_path):
            return jsonify({'error': 'Plot not found'}), 404
        
        mimetype = 'image/jpeg' if filename.endswith('.jpg') else 'image/png'
        return send_file(plot_path, mimetype=mimetype)
    
    except Exception as e:
        logger.error(f"Error serving plot: {e}")
        return jsonify({'error': str(e)}), 500


@r_exec_bp.route('/api/validate-data', methods=['POST'])
def validate_data():
    """Validate uploaded data for statistical analysis"""
    try:
        from app.r_engine import data_validator
        import pandas as pd
        from flask import session
        
        # Get data from session or request
        file_path = session.get('uploaded_file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'No data file uploaded. Please upload a file first.'
            }), 400
        
        # Load and validate
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        result = data_validator.validate(df)
        
        return jsonify({
            'success': True,
            'valid': result.valid,
            'issues': result.issues,
            'warnings': result.warnings,
            'summary': result.summary
        })
    
    except Exception as e:
        logger.error(f"Data validation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@r_exec_bp.route('/api/suggest-tests', methods=['POST'])
def suggest_tests():
    """Suggest appropriate statistical tests based on data"""
    try:
        from app.r_engine import data_validator
        import pandas as pd
        from flask import session
        
        data = request.get_json() or {}
        outcome_col = data.get('outcome')
        group_col = data.get('group')
        
        file_path = session.get('uploaded_file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'No data file uploaded.'
            }), 400
        
        # Load data
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        suggestions = data_validator.suggest_tests(df, outcome_col, group_col)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    
    except Exception as e:
        logger.error(f"Test suggestion error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@r_exec_bp.route('/api/debug-code', methods=['POST'])
def debug_code():
    """Analyze code error and suggest fixes using AI"""
    try:
        from app.r_engine import analyze_r_error
        from flask import session

        data = request.get_json()
        code = data.get('code', '')
        error = data.get('error', '')
        columns = data.get('columns', [])

        if not error:
            return jsonify({
                'success': False,
                'error': 'No error message provided'
            }), 400

        # Get dataset info from session or request
        dataset_info = {
            'column_names': columns or session.get('column_names', []),
            'filename': session.get('uploaded_filename', 'data'),
            'file_path': session.get('uploaded_file_path', '')
        }

        # Analyze the error
        analysis = analyze_r_error(
            error=error,
            code=code,
            dataset_info=dataset_info
        )

        return jsonify({
            'success': True,
            'error_type': analysis.get('error_type', 'unknown'),
            'explanation': analysis.get('explanation', 'An error occurred in your R code.'),
            'suggestion': analysis.get('suggestion', 'Check your code for syntax errors.'),
            'fix_available': analysis.get('fix_available', False),
            'fixed_code': analysis.get('fix_code'),
            'code_snippet': analysis.get('code_snippet'),
            'alternatives': analysis.get('alternatives'),
            'dataset_columns': analysis.get('dataset_columns', [])
        })

    except Exception as e:
        logger.error(f"Code debugging error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@r_exec_bp.route('/api/explain-code', methods=['POST'])
def explain_code():
    """Generate an LLM-powered explanation of R code"""
    try:
        from app.handlers import handle_code_explanation, get_quick_code_summary
        from app.llm import OllamaClient

        data = request.get_json()
        code = data.get('code', '')
        test_type = data.get('test_type')

        if not code.strip():
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400

        # Get quick summary first (no LLM needed)
        summary = get_quick_code_summary(code)

        # Initialize LLM client
        client = OllamaClient(
            model=current_app.config['LLM_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL']
        )

        # Use detected test type if not provided
        if not test_type:
            test_type = summary.get('detected_test')

        # Generate explanation (non-streaming for simple endpoint)
        explanation_parts = []
        for chunk in handle_code_explanation(code, client, test_type, stream=False):
            explanation_parts.append(chunk)

        explanation = ''.join(explanation_parts)

        return jsonify({
            'success': True,
            'explanation': explanation,
            'summary': summary
        })

    except Exception as e:
        logger.error(f"Code explanation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@r_exec_bp.route('/api/explain-code/stream', methods=['POST'])
def explain_code_stream():
    """Stream an LLM-powered explanation of R code"""
    try:
        from app.handlers import handle_code_explanation, get_quick_code_summary
        from app.llm import OllamaClient

        data = request.get_json()
        code = data.get('code', '')
        test_type = data.get('test_type')

        if not code.strip():
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400

        # Get quick summary first
        summary = get_quick_code_summary(code)

        # Initialize LLM client
        client = OllamaClient(
            model=current_app.config['LLM_MODEL'],
            base_url=current_app.config['OLLAMA_BASE_URL']
        )

        # Use detected test type if not provided
        if not test_type:
            test_type = summary.get('detected_test')

        def generate():
            """SSE generator for streaming explanation"""
            try:
                # Send summary first
                yield f"data: {json.dumps({'type': 'summary', 'content': summary})}\n\n"

                # Stream explanation
                for chunk in handle_code_explanation(code, client, test_type, stream=True):
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                logger.error(f"Streaming explanation error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.error(f"Code explanation stream error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@r_exec_bp.route('/api/code-summary', methods=['POST'])
def code_summary():
    """Get a quick summary of R code without LLM"""
    try:
        from app.handlers import get_quick_code_summary

        data = request.get_json()
        code = data.get('code', '')

        if not code.strip():
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400

        summary = get_quick_code_summary(code)

        return jsonify({
            'success': True,
            'summary': summary
        })

    except Exception as e:
        logger.error(f"Code summary error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
