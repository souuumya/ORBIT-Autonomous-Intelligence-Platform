import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"

MISSIONS = [
    {
        "mission_title": f"Solar-Powered EV Charging Infrastructure ({uuid.uuid4().hex[:6]})",
        "mission_objective": "Analyze market opportunity for solar-powered EV charging stations in suburban hubs.",
        "priority": "high",
    },
    {
        "mission_title": f"AI Education Platform Launch Strategy ({uuid.uuid4().hex[:6]})",
        "mission_objective": "Create a multi-channel go-to-market strategy for interactive K-12 AI learning software.",
        "priority": "medium",
    },
    {
        "mission_title": f"Customer Retention & Product Improvement ({uuid.uuid4().hex[:6]})",
        "mission_objective": "Investigate SaaS customer churn feedback and propose automated workflow improvements.",
        "priority": "critical",
    },
]

def test_mission(idx, payload):
    print(f"\n--- Testing Mission {idx + 1}: '{payload['mission_title']}' ---")
    
    # 1. POST /api/agent/init
    init_res = requests.post(f"{BASE_URL}/api/agent/init", json=payload)
    assert init_res.status_code == 200, f"Init failed: {init_res.text}"
    data = init_res.json()
    mission_id = data["mission_id"]
    print(f"Initialized mission_id: {mission_id}, status: {data['status']}")
    
    # 2. Poll GET /api/agent/feed
    completed = False
    start_t = time.time()
    last_stage = ""
    feed_count = 0
    
    while time.time() - start_t < 35:
        feed_res = requests.get(f"{BASE_URL}/api/agent/feed", params={"mission_id": mission_id})
        assert feed_res.status_code == 200, f"Feed failed: {feed_res.text}"
        feed_data = feed_res.json()
        entries = feed_data["entries"]
        feed_count = len(entries)
        
        if entries:
            for entry in entries:
                stage = entry.get("current_stage") or ""
                if stage == "COMPLETED":
                    completed = True
            
            latest = entries[-1]
            stage = latest.get("current_stage") or ""
            if stage != last_stage:
                print(f"  Stage update -> [{stage}] Agent: {latest.get('agent_responsible')} | Work: {latest.get('summary_of_work')}")
                last_stage = stage
            
            if completed:
                break
                
        time.sleep(1)
        
    assert completed, f"Mission {mission_id} did not complete within timeout"
    print(f"Mission {mission_id} successfully reached COMPLETED with {feed_count} feed entries!")
    
    # 3. GET /api/agent/replay
    replay_res = requests.get(f"{BASE_URL}/api/agent/replay", params={"mission_id": mission_id})
    assert replay_res.status_code == 200
    replay_data = replay_res.json()
    print(f"  Replay steps recorded: {replay_data['total_steps']}")
    
    # 4. GET /api/agent/reflection
    reflection_res = requests.get(f"{BASE_URL}/api/agent/reflection", params={"mission_id": mission_id})
    assert reflection_res.status_code == 200
    reflection_data = reflection_res.json()
    print(f"  Reflection score: {reflection_data['performance_score']} | Lessons: {reflection_data['lessons_learned']}")

if __name__ == "__main__":
    print("Starting verification of 3 distinct autonomous missions against live backend...")
    for i, m in enumerate(MISSIONS):
        test_mission(i, m)
    print("\nALL 3 DISTINCT MISSIONS PASSED SUCCESSFULLY!")
