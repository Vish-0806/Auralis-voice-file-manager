from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_listener_status_stopped():
    """Verify GET /listener/status when stopped."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = False
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.get("/listener/status")
        assert response.status_code == 200
        assert response.json() == {"running": False, "status": "stopped"}


def test_get_listener_status_running():
    """Verify GET /listener/status when running."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = True
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.get("/listener/status")
        assert response.status_code == 200
        assert response.json() == {"running": True, "status": "running"}


def test_start_listener_success():
    """Verify starting the listener when it is stopped."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = False
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.post("/listener/start")
        assert response.status_code == 200
        assert response.json() == {
            "status": "started",
            "message": "Listener started successfully"
        }
        mock_listener.start.assert_called_once_with(run_in_thread=True)


def test_start_listener_already_running():
    """Verify starting the listener when it is already running."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = True
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.post("/listener/start")
        assert response.status_code == 200
        assert response.json() == {
            "status": "already_running",
            "message": "Listener is already running"
        }
        mock_listener.start.assert_not_called()


def test_start_listener_failure():
    """Verify failure response if starting raises an exception."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = False
        mock_listener.start.side_effect = RuntimeError("Microphone in use")
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.post("/listener/start")
        assert response.status_code == 500
        assert "Failed to start listener: Microphone in use" in response.json()["detail"]


def test_stop_listener_success():
    """Verify stopping the listener when it is running."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = True
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.post("/listener/stop")
        assert response.status_code == 200
        assert response.json() == {
            "status": "stopped",
            "message": "Listener stopped successfully"
        }
        mock_listener.stop.assert_called_once()


def test_stop_listener_not_running():
    """Verify stopping the listener when it is already stopped."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = False
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.post("/listener/stop")
        assert response.status_code == 200
        assert response.json() == {
            "status": "not_running",
            "message": "Listener is not running"
        }
        mock_listener.stop.assert_not_called()


def test_stop_listener_failure():
    """Verify failure response if stopping raises an exception."""
    with patch("api.listener_routes.get_assistant") as mock_get_assistant:
        mock_assistant = MagicMock()
        mock_listener = MagicMock()
        mock_listener.is_running = True
        mock_listener.stop.side_effect = RuntimeError("Lock failure")
        mock_assistant.get_voice_listener.return_value = mock_listener
        mock_get_assistant.return_value = mock_assistant

        response = client.post("/listener/stop")
        assert response.status_code == 500
        assert "Failed to stop listener: Lock failure" in response.json()["detail"]
