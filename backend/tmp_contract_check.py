from fastapi.testclient import TestClient
from app.main import app
import time
import uuid

client = TestClient(app)
payload = {
    'mission_title': f'Contract Check ({uuid.uuid4().hex[:6]})',
    'mission_objective': 'Verify init triggers autonomous execution and feed returns a persisted post.',
    'priority': 'critical',
}
init_res = client.post('/api/agent/init', json=payload)
print('INIT', init_res.status_code, init_res.json())
mission_id = init_res.json()['mission_id']
feed_res = None
for _ in range(20):
    feed_res = client.get('/api/agent/feed', params={'mission_id': mission_id})
    data = feed_res.json()
    posts = [e for e in data.get('entries', []) if (e.get('metadata') or {}).get('generated_by') == 'autonomous_agent']
    if posts:
        print('POST', posts[0])
        break
    time.sleep(0.25)
else:
    print('NO_POST_FOUND', feed_res.json())
