"""
Integration tests for chat workflow
"""
import pytest
from app import create_app
from app.llm import get_intent_detector


class TestChatWorkflow:
    """Test end-to-end chat workflows"""

    @pytest.fixture
    def app(self, app_config):
        """Create test Flask app"""
        app = create_app(config=app_config)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    def test_intent_detection_compare_groups(self, mock_llm_client):
        """Test intent detection for group comparison"""
        detector = get_intent_detector(llm_client=mock_llm_client)

        result = detector.detect("compare groups A and B", use_llm_fallback=False)

        assert result.intent == "compare_groups"
        assert result.confidence > 0.5

    def test_intent_detection_correlation(self, mock_llm_client):
        """Test intent detection for correlation"""
        detector = get_intent_detector(llm_client=mock_llm_client)

        result = detector.detect("correlation between X and Y", use_llm_fallback=False)

        assert result.intent == "correlation"
        assert result.confidence > 0.5

    def test_chat_endpoint_basic(self, client):
        """Test basic chat endpoint"""
        response = client.post('/api/chat', json={
            'message': 'What is a t-test?',
            'conversation_id': 'test-123'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'response' in data
        assert data['success'] is True
