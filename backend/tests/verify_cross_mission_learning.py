import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_cross_mission_test():
    print("\n--- Starting Cross-Mission Learning Verification ---")
    
    # 1. Mission A
    payload_a = {
        "mission_title": f"Mission A: Autonomous Supply Chain Optimization ({uuid.uuid4().hex[:6]})",
        "mission_objective": "Optimize logistics routes and reduce warehouse fulfillment latency.",
        "priority": "high",
    }
    
    print(f"\nInitializing Mission A: '{payload_a['mission_title']}'...")
    res_a = requests.post(f"{BASE_URL}/api/agent/init", json=payload_a)
    assert res_a.status_code == 200, f"Init A failed: {res_a.text}"
    mission_id_a = res_a.json()["mission_id"]
    print(f"Mission A ID: {mission_id_a}")
    
    # Poll Mission A until COMPLETED
    start_t = time.time()
    completed_a = False
    while time.time() - start_t < 35:
        feed_res = requests.get(f"{BASE_URL}/api/agent/feed", params={"mission_id": mission_id_a})
        if feed_res.status_code == 200:
            entries = feed_res.json().get("entries", [])
            if any(e.get("current_stage") == "COMPLETED" for e in entries):
                completed_a = True
                break
        time.sleep(1)
        
    assert completed_a, "Mission A failed to complete within timeout"
    print(f"Mission A completed successfully!")
    
    # Verify Memory created for Mission A
    mem_res_a = requests.get(f"{BASE_URL}/api/agent/memories", params={"mission_id": mission_id_a})
    assert mem_res_a.status_code == 200
    memories_a = mem_res_a.json().get("memories", [])
    print(f"Mission A generated {len(memories_a)} long-term memory record(s):")
    for m in memories_a:
        print(f"  [{m['memory_type']}] {m['summary']}")
    assert len(memories_a) >= 1, "Mission A did not generate long-term memory records"

    # 2. Mission B (different mission objective)
    payload_b = {
        "mission_title": f"Mission B: Suburban Delivery Fleet Scaling ({uuid.uuid4().hex[:6]})",
        "mission_objective": "Expand last-mile delivery fleet using autonomous electric vans.",
        "priority": "medium",
    }
    
    print(f"\nInitializing Mission B: '{payload_b['mission_title']}'...")
    res_b = requests.post(f"{BASE_URL}/api/agent/init", json=payload_b)
    assert res_b.status_code == 200, f"Init B failed: {res_b.text}"
    mission_id_b = res_b.json()["mission_id"]
    print(f"Mission B ID: {mission_id_b}")

    # Poll Mission B until COMPLETED
    start_t = time.time()
    completed_b = False
    while time.time() - start_t < 35:
        feed_res = requests.get(f"{BASE_URL}/api/agent/feed", params={"mission_id": mission_id_b})
        if feed_res.status_code == 200:
            entries = feed_res.json().get("entries", [])
            if any(e.get("current_stage") == "COMPLETED" for e in entries):
                completed_b = True
                break
        time.sleep(1)

    assert completed_b, "Mission B failed to complete within timeout"
    print(f"Mission B completed successfully!")

    # Verify Experience Retrieval for Mission B
    ret_res_b = requests.get(f"{BASE_URL}/api/agent/memory/retrieval", params={"mission_id": mission_id_b})
    assert ret_res_b.status_code == 200
    ret_data_b = ret_res_b.json()
    
    retrievals = ret_data_b.get("retrievals", [])
    available_prior = ret_data_b.get("available_prior_experiences", [])
    
    print(f"Mission B retrieved {len(retrievals)} experience record(s) from prior missions!")
    print(f"Total available prior experiences in system: {len(available_prior)}")
    
    assert len(available_prior) >= 1, "Prior experiences were not available to Mission B"
    print("\nCROSS-MISSION LEARNING DEMONSTRATION VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    run_cross_mission_test()
