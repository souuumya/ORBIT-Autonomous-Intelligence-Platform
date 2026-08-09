import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ENVIRONMENT"] = "testing"

import time
from fastapi.testclient import TestClient

from app.db.session import Base, engine, SessionLocal
from app.main import app
from app.services.mission_state_manager import MissionStateManager

def run_e2e_verification():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    
    print("=== Step 1: POST /api/v1/agent/init ===")
    init_payload = {
        "mission_title": "Autonomous Core Validation Mission",
        "mission_objective": "Demonstrate complete autonomous execution pipeline from initialization to completed state",
        "mission_description": "Real E2E integration test for Phase 1",
        "priority": "high",
        "user_id": "user-e2e-demo",
    }
    
    response = client.post("/api/v1/agent/init", json=init_payload)
    print(f"Init Response Code: {response.status_code}")
    init_data = response.json()
    print(f"Init Response Body: {init_data}")
    
    mission_id = init_data["mission_id"]
    initial_status = init_data["status"]
    print(f"Mission ID: {mission_id} | Initial Status: {initial_status}")
    
    print("\n=== Step 2: Polling /api/v1/agent/feed autonomously ===")
    stages_seen = set()
    start_time = time.time()
    completed = False
    
    while time.time() - start_time < 15.0:
        feed_resp = client.get(f"/api/v1/agent/feed?mission_id={mission_id}&limit=100")
        if feed_resp.status_code == 200:
            feed_json = feed_resp.json()
            entries = feed_json.get("entries", [])
            for entry in entries:
                stage = entry.get("current_stage")
                if stage and stage not in stages_seen:
                    stages_seen.add(stage)
                    print(f"  [Feed Event] Stage: {stage:<15} | Agent: {entry.get('agent_responsible'):<15} | Progress: {entry.get('progress_percentage'):.1f}% | Summary: {entry.get('summary_of_work')[:60]}...")
            
            if "COMPLETED" in stages_seen:
                completed = True
                break
        time.sleep(0.3)
        
    print(f"\nFinal Autonomous Completion Status: {'SUCCESS' if completed else 'TIMED OUT'}")
    print(f"Stages observed in feed: {sorted(list(stages_seen))}")
    
    print("\n=== Step 3: Verifying Completed Mission Summary ===")
    db = SessionLocal()
    try:
        manager = MissionStateManager(db)
        summary = manager.get_completed_mission_summary(mission_id)
        print(f"Mission ID: {summary['mission_id']}")
        print(f"Original Objective: {summary['original_objective']}")
        print(f"Execution Status: {summary['execution_status']}")
        print(f"Milestones Count: {len(summary['milestones'])}")
        print(f"Decisions Count: {len(summary['decisions'])}")
        print(f"Rejected Alternatives Count: {len(summary['rejected_alternatives'])}")
        print(f"Created Output Title: {summary['created_output']['title']}")
        print(f"Review Score: {summary['review_result']['score']} (Passed: {summary['review_result']['passed']})")
        print(f"Reflection Performance Score: {summary['reflection']['performance_score']}")
        print(f"Lessons Learned: {summary['lessons_learned']}")
        print(f"Timeline Events Count: {len(summary['timeline_events'])}")
    finally:
        db.close()

if __name__ == "__main__":
    run_e2e_verification()
