"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_csv_path():
    """Path to sample CSV file for testing"""
    return Path(__file__).parent / "fixtures" / "sample_datasets" / "iris.csv"


@pytest.fixture
def app_config():
    """Test configuration"""
    return {
        'TESTING': True,
        'DATA_DIR': 'data',
        'UPLOAD_FOLDER': 'data/user_datasets',
        'PLOTS_FOLDER': 'data/plots',
        'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing without Ollama"""
    class MockOllamaClient:
        def generate(self, prompt, **kwargs):
            return "Mock LLM response"

        def chat(self, messages, **kwargs):
            return "Mock chat response"

    return MockOllamaClient()
