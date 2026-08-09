import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_evaluator_simulation():
    print("\n--- Starting Final End-to-End Evaluator Simulation ---")

    title = f"Official Evaluator Audit Mission ({uuid.uuid4().hex[:6]})"
    objective = "Execute autonomous multi-agent creation and verification campaign for hackathon evaluation."

    # STEP 1: POST /api/agent/init ONLY ONCE
    print(f"STEP 1: POST /api/agent/init for '{title}'...")
    init_res = requests.post(f"{BASE_URL}/api/agent/init", json={
        "mission_title": title,
        "mission_objective": objective,
        "priority": "critical",
    })
    assert init_res.status_code == 200, f"Init failed: {init_res.text}"
    init_data = init_res.json()
    mission_id = init_data["mission_id"]
    print(f"  Mission ID: {mission_id}, Status: {init_data['status']}")

    # STEP 2 & 3: No further instructions. Periodically call GET /api/agent/feed
    print("\nSTEP 2 & 3: Polling GET /api/agent/feed periodically without further input...")
    start_t = time.time()
    completed = False
    received_entry_ids = set()
    stages_seen = set()

    while time.time() - start_t < 35:
        feed_res = requests.get(f"{BASE_URL}/api/agent/feed", params={"mission_id": mission_id})
        assert feed_res.status_code == 200, f"Feed polling failed: {feed_res.text}"
        feed_data = feed_res.json()
        entries = feed_data.get("entries", [])

        for entry in entries:
            received_entry_ids.add(entry["id"])
            stages_seen.add(entry.get("current_stage"))
            if entry.get("current_stage") == "COMPLETED":
                completed = True

        if completed:
            break
        time.sleep(1)

    # STEP 4 & 5: Observe autonomous feed & wait for COMPLETED
    assert completed, f"Mission {mission_id} did not reach COMPLETED within timeout"
    print(f"STEP 4 & 5: Mission reached COMPLETED successfully with {len(received_entry_ids)} unique feed entries!")

    # STEP 6: Verify all autonomous stages occurred
    print(f"STEP 6: Stages observed: {sorted(list(stages_seen))}")
    assert "INITIALIZED" in stages_seen
    assert "COMPLETED" in stages_seen

    # STEP 7: Verify feed entries were generated after initialization
    assert len(received_entry_ids) >= 5, f"Expected at least 5 stage feed entries, got {len(received_entry_ids)}"

    # STEP 8: Verify no duplicate entry IDs
    feed_res_final = requests.get(f"{BASE_URL}/api/agent/feed", params={"mission_id": mission_id})
    final_entries = feed_res_final.json()["entries"]
    final_ids = [e["id"] for e in final_entries]
    assert len(final_ids) == len(set(final_ids)), "Duplicate feed entry IDs detected"
    print("STEP 8: Verified zero duplicate feed entry IDs!")

    # STEP 9: Verify mission persisted correctly in replay & reflection endpoints
    replay_res = requests.get(f"{BASE_URL}/api/agent/replay", params={"mission_id": mission_id})
    assert replay_res.status_code == 200
    assert replay_res.json()["total_steps"] >= 5

    reflection_res = requests.get(f"{BASE_URL}/api/agent/reflection", params={"mission_id": mission_id})
    assert reflection_res.status_code == 200
    assert reflection_res.json()["performance_score"] > 0.0
    print("STEP 9: Verified mission persisted in replay timeline and reflection engine!")

    print("\nFINAL EVALUATOR SIMULATION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_evaluator_simulation()
