import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_live_demo_scenario():
    print("\n=============================================================")
    print("      ORBIT HACKATHON LIVE DEMO FLOW (REAL MISSION)")
    print("=============================================================\n")

    print("0:00 — Mission Control is idle (Empty State displayed on UI).")
    time.sleep(1)

    title = f"Launch AI-powered student productivity app ({uuid.uuid4().hex[:6]})"
    objective = "Synthesize market strategy, student task automation features, and go-to-market plan."

    print(f"\n0:15 — Initializing ONE mission: '{title}'...")
    init_res = requests.post(f"{BASE_URL}/api/agent/init", json={
        "mission_title": title,
        "mission_objective": objective,
        "priority": "high",
    })
    assert init_res.status_code == 200, f"Init failed: {init_res.text}"
    data = init_res.json()
    mission_id = data["mission_id"]
    print(f"       Backend initialized mission_id: {mission_id}")
    print("0:25 — Stop interacting with system. Frontend acts strictly as an Observer.\n")

    start_t = time.time()
    last_stage = ""
    completed = False

    while time.time() - start_t < 35:
        feed_res = requests.get(f"{BASE_URL}/api/agent/feed", params={"mission_id": mission_id})
        if feed_res.status_code == 200:
            entries = feed_res.json().get("entries", [])
            if entries:
                for entry in entries:
                    stage = entry.get("current_stage")
                    if stage == "COMPLETED":
                        completed = True
                
                latest = entries[-1]
                stage = latest.get("current_stage")
                if stage != last_stage:
                    print(f"[{time.strftime('%M:%S')}] Stage Transition -> [{stage}] Agent: {latest.get('agent_responsible')}")
                    print(f"         Work Summary: {latest.get('summary_of_work')}")
                    print(f"         Decision Made: {latest.get('decision_made')}\n")
                    last_stage = stage

                if completed:
                    break
        time.sleep(1)

    assert completed, "Live demo mission did not reach completion within timeout"
    print("2:30 — Mission completed autonomously!")

    # Verify Decision Replay
    print("\n2:40 — Fetching Decision Replay data from GET /api/agent/replay...")
    replay_res = requests.get(f"{BASE_URL}/api/agent/replay", params={"mission_id": mission_id})
    assert replay_res.status_code == 200
    replay_data = replay_res.json()
    print(f"2:50 — Decision Replay verified with {replay_data['total_steps']} steps.")
    dec_step = next((s for s in replay_data['steps'] if s['action_type'] == 'DECISION'), None)
    if dec_step:
        meta = dec_step.get('metadata', {})
        print(f"       Selected Strategy: {meta.get('selected_strategy', {}).get('title')}")
        rejected = meta.get('rejected_strategies', [])
        if rejected:
            print(f"       Rejected Strategy: {rejected[0].get('title')} (Reason: {rejected[0].get('reason')})")

    # Verify Long-Term Memory
    print("\n3:00 — Fetching Long-Term Memory records from GET /api/agent/memories...")
    mem_res = requests.get(f"{BASE_URL}/api/agent/memories", params={"mission_id": mission_id})
    assert mem_res.status_code == 200
    memories = mem_res.json().get("memories", [])
    print(f"       Generated {len(memories)} long-term memory records for future mission retrieval.")

    print("\n=============================================================")
    print("   LIVE DEMO SCENARIO VERIFIED SUCCESSFULLY WITH REAL DATA!")
    print("=============================================================\n")

if __name__ == "__main__":
    run_live_demo_scenario()
