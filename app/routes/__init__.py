"""Routes module initialization"""
from .chat import chat_bp
from .file_handler import file_bp
from .history import history_bp
from .export import export_bp
from .r_exec import r_exec_bp
from .learner import learner_bp

__all__ = ['chat_bp', 'file_bp', 'history_bp', 'export_bp', 'r_exec_bp', 'learner_bp']
