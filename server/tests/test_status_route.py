from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from llmlaunchpad.main import app


client = TestClient(app)


def test_status_reports_llama_not_running_and_litellm_not_running():
    mock_server = Mock()
    mock_server.is_running = False
    mock_server.get_status.return_value = SimpleNamespace(model_name=None)

    with patch("llmlaunchpad.routes.status.get_llama_server", return_value=mock_server), \
         patch("llmlaunchpad.routes.status.get_litellm_status", return_value={"enabled": False, "available": False}):
        response = client.get("/status")

    data = response.json()
    assert response.status_code == 200
    assert data["services"]["llama"]["running"] is False
    assert data["services"]["llama"]["model"] is None
    assert data["services"]["litellm"]["running"] is False


def test_status_reports_llama_running_with_model():
    model_name = "Phi-3-mini-4k-instruct-q4.gguf"
    mock_server = Mock()
    mock_server.is_running = True
    mock_server.get_status.return_value = SimpleNamespace(model_name=model_name)

    with patch("llmlaunchpad.routes.status.get_llama_server", return_value=mock_server), \
         patch("llmlaunchpad.routes.status.get_litellm_status", return_value={"enabled": False, "available": False}):
        response = client.get("/status")

    data = response.json()
    assert response.status_code == 200
    assert data["services"]["llama"]["running"] is True
    assert data["services"]["llama"]["model"] == model_name


def test_status_reports_litellm_not_running_when_enabled_but_unavailable():
    mock_server = Mock()
    mock_server.is_running = False
    mock_server.get_status.return_value = SimpleNamespace(model_name=None)

    with patch("llmlaunchpad.routes.status.get_llama_server", return_value=mock_server), \
         patch("llmlaunchpad.routes.status.get_litellm_status", return_value={"enabled": True, "available": False}):
        response = client.get("/status")

    data = response.json()
    assert response.status_code == 200
    assert data["services"]["litellm"]["running"] is False


def test_status_reports_litellm_running_when_enabled_and_available():
    mock_server = Mock()
    mock_server.is_running = False
    mock_server.get_status.return_value = SimpleNamespace(model_name=None)

    with patch("llmlaunchpad.routes.status.get_llama_server", return_value=mock_server), \
         patch("llmlaunchpad.routes.status.get_litellm_status", return_value={"enabled": True, "available": True}):
        response = client.get("/status")

    data = response.json()
    assert response.status_code == 200
    assert data["services"]["litellm"]["running"] is True
