"""
tests/api/test_websocket.py — Real-time Detection WebSocket tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_websocket_connect_and_receive(client):
    with client.websocket_connect("/api/ws/detections") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "detections"
        assert msg["sessionId"] == "sess_01"
        assert "timestamp" in msg
        assert isinstance(msg["detections"], list)
        assert len(msg["detections"]) > 0


def test_websocket_ping_pong_interaction(client):
    with client.websocket_connect("/api/ws/detections") as ws:
        # Discard greeting
        ws.receive_json()

        # Send ping
        ws.send_text("ping")
        reply = ws.receive_json()
        assert reply["type"] == "detections"
        assert reply["status"] == "DEMO_DATA"


def test_websocket_disconnect_graceful(client):
    # Tests that socket connects and closes without raising server-side unhandled exception
    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()
        ws.close()


def test_websocket_frame_inference(client):
    """Verifies that sending a base64 frame triggers real inference and returns detection summary."""
    import base64
    import io
    from PIL import Image

    # Create dummy JPEG image
    img = Image.new("RGB", (64, 64), color=(100, 100, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    with client.websocket_connect("/api/ws/detections") as ws:
        # Discard greeting
        ws.receive_json()

        # Send frame
        ws.send_json({
            "type": "frame",
            "frame": f"data:image/jpeg;base64,{b64_data}",
            "confidenceThreshold": 0.35,
            "detectPose": False,
        })
        reply = ws.receive_json()
        assert reply["type"] == "detections"
        assert reply["status"] == "REAL_PROCESSING"
        assert "processingTimeMs" in reply
        assert "processingFps" in reply
        assert reply["isDemoData"] is False


def test_websocket_pose_inference(client):
    """Verifies that sending a frame with detectPose=True returns real pose detection."""
    import base64
    import io
    from PIL import Image

    img = Image.new("RGB", (64, 64), color=(120, 130, 140))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()
        ws.send_json({
            "type": "frame",
            "frame": b64_data,
            "confidenceThreshold": 0.25,
            "detectPose": True,
        })
        reply = ws.receive_json()
        assert reply["type"] == "detections"
        assert reply["status"] == "REAL_PROCESSING"
        assert reply["isDemoData"] is False


def test_websocket_corrupted_frame_handling(client):
    """Verifies graceful error handling on corrupt base64 payload."""
    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()
        ws.send_json({
            "type": "frame",
            "frame": "not_a_valid_base64_string!@#$%",
        })
        reply = ws.receive_json()
        assert reply["type"] == "error" or reply["status"] == "ERROR"


def test_websocket_rapid_reconnect(client):
    """Verifies rapid connection and disconnection cycles without resource leaks."""
    for _ in range(5):
        with client.websocket_connect("/api/ws/detections") as ws:
            msg = ws.receive_json()
            assert "type" in msg



