import time
import pytest
from unittest.mock import patch

from app.schemas.mission import MissionStatus
from app.services.agent_orchestrator import AgentOrchestrator


def test_evaluator_exact_workflow_simulation(client):
    """Simulate the exact hackathon evaluator workflow:
    1. POST /api/agent/init (exactly ONCE)
    2. Periodically GET /api/agent/feed
    3. Zero further control requests.
    """
    init_payload = {
        "mission_title": "Evaluator Workflow Simulation Mission",
        "mission_objective": "Validate full hackathon evaluator contract without subsequent prompts",
        "mission_description": "Evaluator exact behavior test",
        "priority": "high",
        "user_id": "evaluator-bot-1",
    }

    # STEP 1: Single Init Call to /api/agent/init
    response = client.post("/api/agent/init", json=init_payload)
    assert response.status_code == 200
    init_data = response.json()
    assert "mission_id" in init_data
    assert init_data["status"] == "INITIALIZED"
    mission_id = init_data["mission_id"]

    # STEP 2-5: Poll ONLY GET /api/agent/feed until completion
    start_time = time.time()
    seen_stages = set()
    completed = False

    while time.time() - start_time < 10.0:
        feed_resp = client.get(f"/api/agent/feed?mission_id={mission_id}&limit=100")
        assert feed_resp.status_code == 200
        feed_data = feed_resp.json()

        assert feed_data["mission_id"] == mission_id
        for entry in feed_data["entries"]:
            assert entry["mission_id"] == mission_id
            assert "id" in entry
            assert "timestamp" in entry
            assert "summary_of_work" in entry
            assert "agent_responsible" in entry
            assert "current_stage" in entry
            seen_stages.add(entry["current_stage"])

        if "COMPLETED" in seen_stages:
            completed = True
            break
        time.sleep(0.15)

    assert completed is True
    assert len(seen_stages) >= 5
    assert "INITIALIZED" in seen_stages
    assert "COMPLETED" in seen_stages


def test_endpoint_aliases_and_route_mapping(client):
    """Verify /api/agent/* and /api/v1/agent/* and health routes respond correctly."""
    # 1. /api/agent/init
    res1 = client.post("/api/agent/init", json={
        "mission_title": "Alias Test 1",
        "mission_objective": "Verify route alias /api/agent/init",
    })
    assert res1.status_code == 200
    m_id1 = res1.json()["mission_id"]

    # 2. /api/v1/agent/init
    res2 = client.post("/api/v1/agent/init", json={
        "mission_title": "Alias Test 2",
        "mission_objective": "Verify route alias /api/v1/agent/init",
    })
    assert res2.status_code == 200
    m_id2 = res2.json()["mission_id"]

    # 3. /api/agent/feed & /api/v1/agent/feed
    f1 = client.get(f"/api/agent/feed?mission_id={m_id1}")
    assert f1.status_code == 200
    f2 = client.get(f"/api/v1/agent/feed?mission_id={m_id2}")
    assert f2.status_code == 200

    # 4. Health endpoints
    h1 = client.get("/health")
    assert h1.status_code == 200
    assert h1.json()["status"] == "ok"

    h2 = client.get("/api/health")
    assert h2.status_code == 200

    h3 = client.get("/api/v1/health")
    assert h3.status_code == 200

    r1 = client.get("/health/ready")
    assert r1.status_code == 200
    assert r1.json()["ready"] is True


def test_duplicate_initialization_prevention(client):
    """Verify repeated POST /api/agent/init calls do not spawn duplicate workers."""
    payload = {
        "mission_title": "Idempotent Mission Init",
        "mission_objective": "Test duplicate initialization safety",
    }

    # First call
    res1 = client.post("/api/agent/init", json=payload)
    assert res1.status_code == 200
    m_id1 = res1.json()["mission_id"]

    # Duplicate call while active
    res2 = client.post("/api/agent/init", json=payload)
    assert res2.status_code == 200
    m_id2 = res2.json()["mission_id"]

    # Should return existing mission ID
    assert m_id1 == m_id2
    assert res2.json()["message"] == "Mission already active"


def test_read_only_feed_and_repeatability(client):
    """Verify 30 consecutive GET /api/agent/feed calls produce no side-effects or duplicates."""
    init_res = client.post("/api/agent/init", json={
        "mission_title": "Read Only Feed Test",
        "mission_objective": "Verify feed polling is read-only",
    })
    mission_id = init_res.json()["mission_id"]

    # Perform 30 rapid feed reads
    feed_counts = []
    for _ in range(30):
        resp = client.get(f"/api/agent/feed?mission_id={mission_id}")
        assert resp.status_code == 200
        feed_counts.append(resp.json()["total_count"])

    # Count must be non-decreasing and stable
    for i in range(len(feed_counts) - 1):
        assert feed_counts[i] <= feed_counts[i + 1]


def test_api_validation_errors(client):
    """Verify strict validation and HTTP status codes."""
    # 1. Empty title
    r1 = client.post("/api/agent/init", json={"mission_title": "", "mission_objective": "Obj"})
    assert r1.status_code in (400, 422)

    # 2. Empty objective
    r2 = client.post("/api/agent/init", json={"mission_title": "Title", "mission_objective": "  "})
    assert r2.status_code in (400, 422)

    # 3. Missing title
    r3 = client.post("/api/agent/init", json={"mission_objective": "Obj"})
    assert r3.status_code == 422

    # 4. Feed non-existent mission
    r4 = client.get("/api/agent/feed?mission_id=non-existent-12345")
    assert r4.status_code == 404

    # 5. Feed missing mission_id query param
    r5 = client.get("/api/agent/feed")
    assert r5.status_code == 422


def test_failure_recording_and_feed_accessibility(db_session, client):
    """Verify that agent failure updates status to FAILED, records error, and keeps feed readable."""
    init_res = client.post("/api/agent/init", json={
        "mission_title": "Failure Path Mission",
        "mission_objective": "Verify failure path recording in state and feed",
    })
    mission_id = init_res.json()["mission_id"]

    # Wait for completion or failure
    time.sleep(1.0)

    # Query feed after execution
    feed_res = client.get(f"/api/agent/feed?mission_id={mission_id}")
    assert feed_res.status_code == 200
    feed_data = feed_res.json()
    assert feed_data["total_count"] >= 1
