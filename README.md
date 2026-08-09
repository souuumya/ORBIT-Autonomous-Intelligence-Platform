# ORBIT Autonomous Intelligence Platform

ORBIT is a mission-driven autonomous multi-agent creation, decision auditing, and continuous learning platform. It enables users and automated evaluators to initialize high-level complex missions, observe real-time multi-agent execution, audit candidate strategy decisions, and leverage long-term cross-mission memory.

---

## 1. Product Overview
ORBIT operates as an **autonomous digital worker**. Given a single high-level objective, ORBIT autonomously decomposes goals, conducts research, formulates risk-weighted candidate strategies, synthesizes deliverable assets, verifies output quality, and reflects on performance—storing reusable knowledge in long-term memory.

---

## 2. Problem
Traditional AI tools operate as single-turn reactive assistants requiring constant human prompting, micromanagement, and manual step-by-step guidance. They lack:
- Multi-step autonomous execution capabilities.
- Transparent decision auditing (why a strategy was chosen and what alternatives were rejected).
- Long-term memory and cross-mission learning from prior mistakes and successes.

---

## 3. Solution
ORBIT introduces a **Mission-Driven Observer System**:
- **Single-Turn Submission**: Initialize a mission once via `POST /api/agent/init`; the system executes autonomously to completion without further prompt intervention.
- **Transparent Decision Replay**: Audit candidate strategies, rejected options, confidence scores, and selection rationales via `GET /api/agent/replay`.
- **Long-Term Memory Engine**: Automatically reflects on completed missions (`ReflectionEngine`) and stores reusable lessons in `MemoryRecordModel` for cross-mission experience retrieval.

---

## 4. Architecture
ORBIT uses a decoupled **Observer Frontend** and **Autonomous Backend**:
- **Frontend**: Next.js 14 (App Router, TypeScript, Tailwind CSS, Framer Motion) acting as a read-only visual observer.
- **Backend Core**: FastAPI (Python 3.12/3.14) orchestrating asynchronous agent pipelines via background workers.
- **Persistence**: SQLite (development default) / PostgreSQL (production) with SQLAlchemy ORM.
- **Event Bus**: EventBus emitting state transitions (`MISSION_STARTED`, `DECISION_COMPLETED`, `MEMORY_UPDATED`, `MISSION_COMPLETED`).

---

## 5. Autonomous Workflow
Every mission runs through a 7-stage autonomous lifecycle:
1. **MISSION INITIALIZED**: Submitted once; background worker spawned.
2. **PLANNING** (`PlannerAgent`): Objective decomposed into milestones and tasks.
3. **RESEARCH** (`ResearchAgent`): Context gathered; prior long-term memories retrieved.
4. **DECISION** (`DecisionAgent` & `ReasoningEngine`): Candidate strategies scored; selected option approved; rejected options recorded with rationales.
5. **CREATION** (`CreatorAgent`): Deliverable outputs synthesized.
6. **REVIEW** (`ReviewerAgent`): Quality scored; self-correction revision loops triggered if score < threshold.
7. **REFLECTION & MEMORY** (`ReflectionEngine` & `MemoryEngine`): Performance score computed; lessons stored in `MemoryRecordModel`; mission marked `COMPLETED`.

---

## 6. Technology Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Framer Motion, Lucide Icons.
- **Backend**: FastAPI, Python 3.12/3.14, Pydantic v2, SQLAlchemy 2.0, Pytest.
- **Database**: SQLite (dev) / PostgreSQL 16 (docker).
- **Containerization**: Docker & Docker Compose.

---

## 7. Installation

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+
- (Optional) Docker & Docker Compose

```bash
# Clone repository
git clone https://github.com/org/autonomous-intelligent-platform.git
cd AutonomousIntelligentPlatform
```

---

## 8. Environment Variables

### Backend (`backend/.env` or `backend/.env.example`)
```env
ENVIRONMENT=development
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=autonomous_ai_creator
REDIS_URL=redis://localhost:6379/0
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend (`frontend/.env` or `frontend/.env.example`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 9. Running Backend Locally
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate | On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# Run FastAPI backend with SQLite fallback
$env:DATABASE_URL="sqlite:///./orbit.db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Backend will be available at `http://127.0.0.1:8000` (API docs at `http://127.0.0.1:8000/docs`).

---

## 10. Running Frontend Locally
```bash
cd frontend
npm install
npm run dev
```
Frontend will be available at `http://localhost:3000`.

---

## 11. Running Docker Compose
```bash
# Build and start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## 12. API Endpoints Overview
- `POST /api/agent/init`: Initialize an autonomous mission (single call).
- `GET /api/agent/feed`: Retrieve real-time progress feed for a mission.
- `GET /api/agent/replay`: Retrieve complete decision replay timeline and candidate strategy evaluations.
- `GET /api/agent/reflection`: Retrieve post-mission self-review reflection report.
- `GET /api/agent/memories`: Search and filter persisted long-term memory records.
- `GET /api/agent/memory/retrieval`: Retrieve cross-mission experience retrieval records.
- `GET /api/agent/missions`: List all missions.
- `GET /health` or `GET /api/health`: Health status check.

---

## 13. Testing

### Backend Unit & Integration Tests (65 Tests)
```bash
cd backend
python -m pytest tests
```

### Frontend Unit Tests (14 Tests)
```bash
cd frontend
npm test
```

### Frontend Linting & Type Checking
```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

---

## 14. Evaluator Behavior & Contract
ORBIT is designed for strict compatibility with automated hackathon evaluators:
1. Evaluator calls `POST /api/agent/init` **ONCE** with `mission_title` and `mission_objective`.
2. Backend returns `200 OK` with `mission_id` and starts background execution task.
3. Evaluator sends no further prompts or control requests.
4. Evaluator periodically calls `GET /api/agent/feed?mission_id=...` to observe progress.
5. Mission transitions autonomously through all 7 stages until reaching `COMPLETED`.

Verify evaluator behavior locally:
```bash
python backend/tests/verify_evaluator_simulation.py
```

---

## 15. Decision Replay Inspector
Navigate to `http://localhost:3000/replay` or `http://localhost:3000/replay?mission_id=<MISSION_ID>`.
- **Chronological Timeline**: Step through every persisted action (`PLANNER`, `RESEARCH`, `DECISION`, `CREATOR`, `REVIEWER`, `MEMORY_UPDATE`).
- **Rejected Alternatives**: Inspect strategy options that were considered but rejected, complete with rejection rationales and scores.
- **Why Did AI Choose This?**: Interactive decision rationale graph tracing research context → candidate options → selected strategy → deliverable output → reflection.

---

## 16. Long-Term Memory & Learning Experience
Navigate to `http://localhost:3000/memory`.
- **Memory Overview**: Inspect real `MemoryRecordModel` records (`mission_reflection`, `lesson_learned`, `experience_retrieval`).
- **Cross-Mission Learning**: When a new mission starts, `ResearchAgent` queries `MemoryEngine` for prior mission learnings and feeds retrieved insights into `DecisionAgent`.

Verify cross-mission learning:
```bash
python backend/tests/verify_cross_mission_learning.py
```

---

## 17. AI Usage Log Location
The AI Usage Log detailing tools, prompts, generated modules, and manual engineering iterations is available in [`AI_USAGE_LOG.md`](file:///c:/Users/Soumya%20P/Desktop/AutonomousIntelligentPlatform/AI_USAGE_LOG.md).
