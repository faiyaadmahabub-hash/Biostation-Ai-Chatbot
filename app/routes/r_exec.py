"""
R Execution routes - API for running R code
"""

from flask import Blueprint, request, jsonify, send_file
import os
import logging

logger = logging.getLogger(__name__)

r_exec_bp = Blueprint('r_exec', __name__)


@r_exec_bp.route('/api/run-code', methods=['POST'])
def run_r_code():
    """Execute R code and return results"""
    try:
        from app.r_engine import r_executor, output_parser
        
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
        
        return jsonify({
            'success': result.success,
            'output': result.output,
            'errors': result.errors,
            'warnings': result.warnings,
            'plots': [os.path.basename(p) for p in result.plots],
            'statistics': stats,
            'interpretation': interpretation
        })
    
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
    """Analyze code error and suggest fixes"""
    try:
        from app.debugger import error_parser, code_corrector
        
        data = request.get_json()
        code = data.get('code', '')
        error = data.get('error', '')
        
        if not error:
            return jsonify({
                'success': False,
                'error': 'No error message provided'
            }), 400
        
        # Parse the error
        parsed = error_parser.parse(error, code)
        
        # Get corrections
        correction = code_corrector.analyze_and_correct(code, error)
        
        return jsonify({
            'success': True,
            'error_type': parsed.error_type,
            'likely_cause': parsed.likely_cause,
            'suggestions': parsed.suggestions,
            'corrections': [
                {
                    'original': s.original_line,
                    'corrected': s.corrected_line,
                    'explanation': s.explanation,
                    'confidence': s.confidence
                }
                for s in correction.suggestions
            ],
            'corrected_code': correction.corrected_code,
            'formatted_response': code_corrector.format_correction_response(correction)
        })
    
    except Exception as e:
        logger.error(f"Code debugging error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
