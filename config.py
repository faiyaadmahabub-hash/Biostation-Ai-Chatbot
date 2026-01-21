import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Flask configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'biostation-ai-secret-key-change-in-production'
    
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # Application settings
    APP_NAME = "BioStation AI"
    APP_VERSION = "1.0.0"
    
    # Server settings
    HOST = '127.0.0.1'
    PORT = 5000
    
    # File upload settings
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'user_datasets'
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx', 'xls'}
    
    # Session settings
    SESSION_TIMEOUT = 3600  # 1 hour
    PERMANENT_SESSION_LIFETIME = 3600
    
    # LLM settings
    LLM_MODEL = 'phi3:mini'  # Ollama model name
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 2048
    LLM_CONTEXT_WINDOW = 4096
    
    # Ollama settings
    OLLAMA_BASE_URL = 'http://localhost:11434'
    OLLAMA_TIMEOUT = 120  # seconds
    
    # R environment settings
    R_HOME = BASE_DIR / 'R-Portable'  # For bundled version
    R_TIMEOUT = 60  # seconds
    
    # Storage settings
    DATA_DIR = BASE_DIR / 'data'
    SQLITE_DB_PATH = DATA_DIR / 'database' / 'chats.db'
    
    # ChromaDB settings
    CHROMA_DB_PATH = DATA_DIR / 'chroma'
    CHROMA_COLLECTION_NAME = 'statistical_guidebook'
    
    # Embedding model (local, lightweight)
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = DATA_DIR / 'logs' / 'biostation.log'
    
    # Statistical test knowledge base
    KNOWLEDGE_BASE_PATH = BASE_DIR / 'app' / 'advisor' / 'test_knowledge.py'
    
    # R code templates
    R_TEMPLATES_DIR = BASE_DIR / 'app' / 'code_gen' / 'templates'
    
    # Guidebook documents
    GUIDEBOOK_DOCS_DIR = BASE_DIR / 'app' / 'guidebook' / 'documents'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration (for bundled app)"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env='default'):
    """Get configuration based on environment"""
    return config.get(env, config['default'])
