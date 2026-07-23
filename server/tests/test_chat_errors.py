import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from llmlaunchpad.main import app
from llmlaunchpad.llama import LlamaServerState

client = TestClient(app)


def test_chat_timeout_handling():
    """Test that chat API handles timeouts gracefully."""
    with patch('llmlaunchpad.routes.chat.get_local_completion') as mock_completion, \
         patch('llmlaunchpad.routes.chat.get_llama_server') as mock_get_server, \
         patch('llmlaunchpad.routes.chat.save_message'):
        # Mock the server to be running
        mock_server = MagicMock()
        mock_server.state = LlamaServerState.RUNNING
        mock_get_server.return_value = mock_server
        
        # Simulate a timeout
        mock_completion.side_effect = TimeoutError("Request timeout")
        
        response = client.post(
            "/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            }
        )
        
        # Should return 500 with timeout error message
        assert response.status_code == 500
        assert "timeout" in response.json()["detail"].lower()


def test_chat_connection_error_handling():
    """Test that chat API handles connection errors gracefully."""
    with patch('llmlaunchpad.routes.chat.get_local_completion') as mock_completion, \
         patch('llmlaunchpad.routes.chat.get_llama_server') as mock_get_server, \
         patch('llmlaunchpad.routes.chat.save_message'):
        # Mock the server to be running
        mock_server = MagicMock()
        mock_server.state = LlamaServerState.RUNNING
        mock_get_server.return_value = mock_server
        
        # Simulate a connection error
        mock_completion.side_effect = ConnectionError("Failed to connect")
        
        response = client.post(
            "/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            }
        )
        
        # Should return 500 with connection error message
        assert response.status_code == 500
        assert "connect" in response.json()["detail"].lower() or "failed" in response.json()["detail"].lower()


def test_chat_invalid_response_handling():
    """Test that chat API handles invalid responses from llama-server."""
    with patch('llmlaunchpad.routes.chat.get_local_completion') as mock_completion, \
         patch('llmlaunchpad.routes.chat.get_llama_server') as mock_get_server, \
         patch('llmlaunchpad.routes.chat.save_message'):
        # Mock the server to be running
        mock_server = MagicMock()
        mock_server.state = LlamaServerState.RUNNING
        mock_get_server.return_value = mock_server
        
        # Simulate an invalid response
        mock_completion.return_value = {"invalid": "format"}
        
        response = client.post(
            "/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            }
        )
        
        # Should return 500 with invalid response error
        assert response.status_code == 500
        assert "invalid" in response.json()["detail"].lower() or "format" in response.json()["detail"].lower()


def test_chat_request_validation():
    """Test that chat API validates request parameters."""
    # Test with missing required fields
    response = client.post(
        "/chat/completions",
        json={}  # Missing messages
    )
    
    # Should return 422 for validation error
    assert response.status_code == 422


def test_chat_streaming_timeout_handling():
    """Test that streaming chat handles timeouts."""
    with patch('llmlaunchpad.routes.chat.stream_local_completion') as mock_stream, \
         patch('llmlaunchpad.routes.chat.get_llama_server') as mock_get_server, \
         patch('llmlaunchpad.routes.chat.save_message'):
        # Mock the server to be running
        mock_server = MagicMock()
        mock_server.state = LlamaServerState.RUNNING
        mock_get_server.return_value = mock_server
        
        # Simulate a timeout in streaming
        async def error_generator():
            raise TimeoutError("Stream timeout")
            yield  # Make it a generator
        
        mock_stream.return_value = error_generator()
        
        response = client.post(
            "/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            }
        )
        
        # For streaming responses, errors are communicated through the stream itself
        # rather than HTTP status codes, since the HTTP connection is already established
        # when streaming begins. We accept either:
        # 1. 500 status code (if error is detected before streaming starts)
        # 2. 200 status code with error message in the stream (if error occurs during streaming)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            # Check that the stream contains an error message
            assert b'"error"' in response.content or b'"error":' in response.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
