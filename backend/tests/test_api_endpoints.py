import pytest
from app.api.v1.endpoints.agent import get_db


def test_health_and_readiness_endpoints(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res_ready = client.get("/api/v1/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["ready"] is True


def test_agent_init_and_feed_api_flow(client):
    init_payload = {
        "mission_title": "API Test Campaign",
        "mission_objective": "Test initialization and activity feed retrieval",
        "mission_description": "Validate API contract adherence",
        "priority": "high",
        "user_id": "tester_1",
    }
    res_init = client.post("/api/v1/agent/init", json=init_payload)
    assert res_init.status_code == 200
    data = res_init.json()
    assert "mission_id" in data
    assert data["status"] == "INITIALIZED"
    mission_id = data["mission_id"]

    res_feed = client.get(f"/api/v1/agent/feed?mission_id={mission_id}")
    assert res_feed.status_code == 200
    feed_data = res_feed.json()
    assert feed_data["mission_id"] == mission_id
    assert feed_data["total_count"] >= 1
    assert len(feed_data["entries"]) >= 1


def test_agent_init_validation_error(client):
    res = client.post("/api/v1/agent/init", json={"mission_title": ""})
    assert res.status_code == 422


def test_agent_feed_not_found(client):
    res = client.get("/api/v1/agent/feed?mission_id=nonexistent-mission")
    assert res.status_code == 404
    err = res.json()
    assert err["error"]["code"] == "NOT_FOUND"


def test_agent_feed_empty_mission_id(client):
    res = client.get("/api/v1/agent/feed?mission_id=   ")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BAD_REQUEST"


def test_get_db_generator():
    db_gen = get_db()
    db_instance = next(db_gen)
    assert db_instance is not None
    try:
        next(db_gen)
    except StopIteration:
        pass
