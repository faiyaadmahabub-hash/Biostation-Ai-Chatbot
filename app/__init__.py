from flask import Flask
from pathlib import Path
import logging
import os

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    from config import get_config
    app.config.from_object(get_config(config_name))
    
    # Ensure required directories exist
    create_directories(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize extensions/services
    # (Will add later: ChromaDB, Ollama client, etc.)
    
    return app


def create_directories(app):
    """Create necessary directories if they don't exist"""
    directories = [
        app.config['UPLOAD_FOLDER'],
        Path(app.config['LOG_FILE']).parent,
        app.config['CHROMA_DB_PATH'],
        Path(app.config['SQLITE_DB_PATH']).parent,
        # app.root_path / 'data' / 'sample_datasets',  <-- Removed unused path
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def setup_logging(app):
    """Configure application logging"""
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    
    # File handler
    file_handler = logging.FileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )
    
    # Add handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    config_name = 'development' if app.config['DEBUG'] else 'production'
    app.logger.info(f"BioStation AI starting in {config_name} mode")


def register_blueprints(app):
    """Register Flask blueprints (routes)"""
    from app.routes import chat_bp, file_bp, history_bp, export_bp, r_exec_bp, learner_bp
    
    app.register_blueprint(chat_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(r_exec_bp)
    app.register_blueprint(learner_bp)
    
    app.logger.info("Blueprints registered")
