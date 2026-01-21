"""
File handler routes - Handle dataset uploads
"""

from flask import Blueprint, request, jsonify, current_app, session
import pandas as pd
import os
from pathlib import Path
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

# Create blueprint
file_bp = Blueprint('file', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@file_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'success': False}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'success': False}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type. Please upload CSV or Excel file.',
                'success': False
            }), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Save file to persistent storage
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Read file to get info
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
            
            # Get basic info
            rows, cols = df.shape
            column_names = df.columns.tolist()
            
            # === SAVE TO PERSISTENT STORAGE ===
            from app.chat_storage_manager import dataset_storage
            dataset_storage.save_dataset(filename, filepath, column_names, rows)
            
            session['current_dataset'] = {
                'filename': filename,
                'filepath': filepath,
                'rows': rows,
                'columns': cols,
                'column_names': column_names
            }
            session.modified = True
            
            # Save upload event to chat history
            conversation_id = request.form.get('conversation_id')
            if conversation_id:
                from app.chat_storage_manager import chat_storage
                chat_storage.add_message(conversation_id, 'user', f"Uploaded file: {filename}")
                chat_storage.add_message(conversation_id, 'assistant', f"I have received the file {filename} with {rows} rows and {cols} columns.")
            
            return jsonify({
                'success': True,
                'filename': filename,
                'rows': rows,
                'columns': cols,
                'column_names': column_names,
                'message': 'File saved securely.'
            })
        
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            # Clean up file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'error': f'Could not read file: {str(e)}',
                'success': False
            }), 400
    
    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@file_bp.route('/api/dataset-info', methods=['GET'])
def get_dataset_info():
    """Get information about currently loaded dataset"""
    if 'current_dataset' in session:
        return jsonify({
            'success': True,
            'dataset': session['current_dataset']
        })
    
    # Check persistent storage if session is empty
    from app.chat_storage_manager import dataset_storage
    active = dataset_storage.get_active_dataset()
    if active:
        session['current_dataset'] = active
        return jsonify({
            'success': True,
            'dataset': active
        })
        
    else:
        return jsonify({
            'success': False,
            'message': 'No dataset loaded'
        })
