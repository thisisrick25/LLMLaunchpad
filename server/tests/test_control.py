"""Tests for service control API routes."""

import pytest
from unittest.mock import Mock, patch, PropertyMock
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.llmlaunchpad.routes.control import PerformanceMode
from src.llmlaunchpad.offload import OffloadRecommendation
from src.llmlaunchpad.llama import LlamaServerState
from src.llmlaunchpad.config import _config

# Import the app correctly
from src.llmlaunchpad.main import app

client = TestClient(app)


def test_get_mode():
    """Test getting current performance mode."""
    with patch('src.llmlaunchpad.routes.control.get_config') as mock_get_config:
        mock_config = Mock()
        mock_config.mode = 'auto'
        mock_get_config.return_value = mock_config
        
        response = client.get("/control/mode")
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "auto"
        assert "available_modes" in data


def test_set_mode_valid():
    """Test setting a valid performance mode."""
    with patch('server.src.llmlaunchpad.routes.control.get_config') as mock_get_config, \
         patch('server.src.llmlaunchpad.routes.control.save_config') as mock_save_config:
        mock_config = Mock()
        mock_config.mode = 'auto'
        mock_get_config.return_value = mock_config
        
        response = client.post("/control/mode", json={"mode": "gpu-heavy"})
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "gpu-heavy"
        assert "requires_restart" in data
        assert "can_apply_dynamically" in data
        assert "message" in data


def test_set_mode_invalid():
    """Test setting an invalid performance mode."""
    response = client.post("/control/mode", json={"mode": "invalid-mode"})
    assert response.status_code == 400
    assert "Invalid mode" in response.json()["detail"]


def test_optimize_performance_not_running():
    """Test optimization when server is not running."""
    with patch('server.src.llmlaunchpad.routes.control.get_llama_server') as mock_get_server:
        mock_server = Mock()
        mock_server.state = Mock()
        mock_server.state != "running"  # Not running
        mock_get_server.return_value = mock_server
        
        response = client.post("/control/optimize", json={"model": "test-model"})
        assert response.status_code == 400
        assert "Server is not running" in response.json()["detail"]


def test_optimize_performance_success():
    """Test successful optimization."""
    with patch('src.llmlaunchpad.routes.control.get_llama_server') as mock_get_server, \
         patch('src.llmlaunchpad.routes.control.find_model_by_name') as mock_find_model, \
         patch('src.llmlaunchpad.routes.control.get_config') as mock_get_config, \
         patch('src.llmlaunchpad.routes.control.calculate_offload') as mock_calculate_offload:

        # Mock server as running
        mock_server = Mock()
        mock_server.state = LlamaServerState.RUNNING
        mock_server.get_status.return_value.gpu_layers = 10
        mock_get_server.return_value = mock_server

        # Mock model found
        mock_model = Mock()
        mock_model.path = "/path/to/model.gguf"
        mock_find_model.return_value = mock_model

        # Mock config
        mock_config = Mock()
        mock_config.mode = "auto"
        mock_get_config.return_value = mock_config

        # Mock offload calculation
        mock_recommendation = Mock()
        mock_recommendation.gpu_layers = 15
        mock_recommendation.to_dict.return_value = {
            "gpu_layers": 15,
            "total_layers": 32,
            "estimated_vram_mb": 4096,
            "mode": "auto",
            "reason": "Test recommendation"
        }
        mock_calculate_offload.return_value = mock_recommendation

        response = client.post("/control/optimize", json={
            "model": "test-model",
            "context_size": 4096
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["current_gpu_layers"] == 10
        assert data["recommended_gpu_layers"] == 15
        assert data["requires_restart"] is True
        assert "recommendation" in data
        assert "message" in data


def test_update_server_config():
    """Test updating server configuration."""
    from src.llmlaunchpad.config import Config
    # Store the original config
    original_config = _config
    
    # Create a real config object with initial values
    real_config = Config()
    real_config.mode = "auto"
    real_config.context_size = 4096
    real_config.gpu_layers = 0
    
    # Set the global config to our test object
    import src.llmlaunchpad.config as config_module
    config_module._config = real_config
    
    try:
        with patch('src.llmlaunchpad.routes.control.save_config') as mock_save_config:
            response = client.post("/control/config", json={
                "mode": "gpu-heavy",
                "context_size": 8192,
                "gpu_layers": 20
            })
            
            # Check that the real config object was updated
            assert real_config.mode == "gpu-heavy"
            assert real_config.context_size == 8192
            assert real_config.gpu_layers == 20
            
            # Verify that save_config was called with the real config object
            mock_save_config.assert_called_once_with(real_config)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Configuration updated"
            assert data["mode"] == "gpu-heavy"
            assert data["context_size"] == 8192
            assert data["gpu_layers"] == 20
    finally:
        # Restore original config
        config_module._config = original_config


def test_update_server_config_invalid_mode():
    """Test updating server config with invalid mode."""
    response = client.post("/control/config", json={"mode": "invalid-mode"})
    assert response.status_code == 400
    assert "Invalid mode" in response.json()["detail"]


def test_update_server_config_invalid_context_size():
    """Test updating server config with invalid context size."""
    response = client.post("/control/config", json={"context_size": 64})  # Too small
    assert response.status_code == 400
    assert "Context size must be between 128 and 131072" in response.json()["detail"]
    
    response = client.post("/control/config", json={"context_size": 200000})  # Too large
    assert response.status_code == 400
    assert "Context size must be between 128 and 131072" in response.json()["detail"]


def test_update_server_config_invalid_gpu_layers():
    """Test updating server config with invalid GPU layers."""
    response = client.post("/control/config", json={"gpu_layers": -1})  # Negative
    assert response.status_code == 400
    assert "GPU layers must be >= 0" in response.json()["detail"]