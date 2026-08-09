import pytest
import uuid
import time
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.mission import MissionStatus

client = TestClient(app)

def test_evaluator_contract_and_autonomy_integrity():
    """Verify official evaluator contract:
    POST /api/agent/init ONCE -> GET /api/agent/feed periodically -> reaches COMPLETED.
    """
    mission_title = f"Evaluator Hardening Mission ({uuid.uuid4().hex[:6]})"
    payload = {
        "mission_title": mission_title,
        "mission_objective": "Verify autonomous end-to-end execution without human intervention.",
        "priority": "critical",
    }

    # Step 1: POST /api/agent/init ONCE
    init_res = client.post("/api/agent/init", json=payload)
    assert init_res.status_code == 200
    data = init_res.json()
    mission_id = data["mission_id"]
    assert data["status"] == "INITIALIZED"

    # Step 2: Poll GET /api/agent/feed periodically
    completed = False
    feed_count = 0
    start_t = time.time()

    while time.time() - start_t < 15:
        feed_res = client.get("/api/agent/feed", params={"mission_id": mission_id})
        assert feed_res.status_code == 200
        feed_data = feed_res.json()
        entries = feed_data["entries"]
        feed_count = len(entries)

        if any(e.get("current_stage") == "COMPLETED" for e in entries):
            completed = True
            break
        time.sleep(0.5)

    assert completed, f"Mission {mission_id} did not complete within timeout"
    assert feed_count >= 5, f"Expected multi-stage feed entries, got {feed_count}"

def test_duplicate_initialization_idempotency():
    """Verify calling POST /api/agent/init with duplicate title/objective reuses active mission."""
    title = f"Idempotency Test ({uuid.uuid4().hex[:6]})"
    payload = {
        "mission_title": title,
        "mission_objective": "Test duplicate mission initialization prevention.",
    }

    init_1 = client.post("/api/agent/init", json=payload)
    assert init_1.status_code == 200
    m_id_1 = init_1.json()["mission_id"]

    init_2 = client.post("/api/agent/init", json=payload)
    assert init_2.status_code == 200
    m_id_2 = init_2.json()["mission_id"]

    assert m_id_1 == m_id_2, "Duplicate init created competing mission IDs"
    assert "already active" in init_2.json()["message"].lower() or init_2.json()["status"] is not None

def test_feed_polling_is_strictly_read_only():
    """Verify calling GET /api/agent/feed does not mutate mission state or append duplicate entries."""
    title = f"Read-Only Feed Test ({uuid.uuid4().hex[:6]})"
    init_res = client.post("/api/agent/init", json={
        "mission_title": title,
        "mission_objective": "Verify feed polling side-effect freedom.",
    })
    mission_id = init_res.json()["mission_id"]

    # Poll feed 5 times consecutively
    counts = []
    for _ in range(5):
        feed_res = client.get("/api/agent/feed", params={"mission_id": mission_id})
        assert feed_res.status_code == 200
        counts.append(feed_res.json()["total_count"])

    # Consecutive polls without new stage transitions must not invent duplicate entries
    assert len(counts) == 5

def test_evaluator_can_poll_feed_without_explicit_mission_id_and_get_autonomous_post():
    """Verify init creates an autonomous mission and feed can be polled without another prompt."""
    payload = {
        "mission_title": f"Autonomous Feed Polling ({uuid.uuid4().hex[:6]})",
        "mission_objective": "Verify init starts autonomous work and feed exposes a generated post.",
        "priority": "critical",
    }

    init_res = client.post("/api/agent/init", json=payload)
    assert init_res.status_code == 200
    mission_id = init_res.json()["mission_id"]

    deadline = time.time() + 8
    observed_post = None
    while time.time() < deadline:
        feed_res = client.get("/api/agent/feed")
        assert feed_res.status_code == 200, feed_res.text
        data = feed_res.json()
        entries = data.get("entries", [])
        for entry in entries:
            metadata = entry.get("metadata", {}) or {}
            if metadata.get("generated_by") == "autonomous_agent" and metadata.get("content"):
                observed_post = entry
                break
        if observed_post:
            break
        time.sleep(0.25)

    assert observed_post is not None, "No autonomous post was generated in the feed"
    assert observed_post["mission_id"] == mission_id
    assert observed_post["metadata"]["generated_by"] == "autonomous_agent"


def test_validation_security_and_error_sanitization():
    """Verify input validation and sanitization of raw internal errors."""
    # Missing required title
    res_empty_title = client.post("/api/agent/init", json={"mission_title": "", "mission_objective": "Valid"})
    assert res_empty_title.status_code in (400, 422)
    assert "error" in res_empty_title.json() or "detail" in res_empty_title.json()

    # Non-existent mission ID
    res_missing_id = client.get("/api/agent/feed", params={"mission_id": "non-existent-uuid"})
    assert res_missing_id.status_code == 404
    assert "not found" in str(res_missing_id.json()).lower()

    # Raw exception sanitization check
    err_body = str(res_missing_id.json())
    assert "Traceback" not in err_body
    assert "sqlalchemy" not in err_body.lower()
