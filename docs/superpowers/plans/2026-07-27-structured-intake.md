# 结构化问诊改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a guided structured intake workflow with selectable questions, progress, collected summaries, and final archive generation.

**Architecture:** Add a focused backend intake flow module that owns questions, session state, summaries, and fallback reports. Expose new FastAPI endpoints for session state, answers, navigation, and completion. Replace the Vue chat-only screen with a three-column guided intake workspace that consumes those endpoints.

**Tech Stack:** Python 3 + FastAPI + unittest for backend verification; Vue 3 + Vite + TailwindCSS + markdown-it for frontend rendering.

## Global Constraints

- Keep `/api/chat`, `/api/save_record`, and `/api/records` compatible where practical.
- Use a hybrid model: fixed questions, selectable options, optional free-text details, AI/fallback final report.
- First pass uses 10 core questions and excludes login, notifications, prescription, and complex specialty branching.
- If AI fails, structured answers must still save and the user can continue.
- This project directory is not currently a Git repository, so checkpoint by running tests and build instead of committing.

---

### Task 1: Backend Structured Intake Core

**Files:**
- Create: `backend/intake_flow.py`
- Create: `backend/tests/test_intake_flow.py`

**Interfaces:**
- Produces: `intake_sessions`, `get_intake_state(session_id)`, `submit_intake_answer(session_id, question_id, option_id, note)`, `move_intake(session_id, direction)`, `complete_intake_session(session_id)`.
- Return values are JSON-serializable dictionaries for direct FastAPI use.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_intake_flow.py` with tests for initialization, answer submission, editing, navigation, and fallback completion.

- [ ] **Step 2: Run tests and verify they fail**

Run: `python -m unittest discover -s backend/tests -v`
Expected: FAIL because `intake_flow` does not exist.

- [ ] **Step 3: Implement `backend/intake_flow.py`**

Add question definitions, in-memory session manager, progress calculation, collected summary, report generation, and record export data.

- [ ] **Step 4: Run tests and verify they pass**

Run: `python -m unittest discover -s backend/tests -v`
Expected: PASS.

### Task 2: Backend API Endpoints

**Files:**
- Modify: `backend/main.py`

**Interfaces:**
- Consumes: functions from `backend/intake_flow.py`.
- Produces: `GET /api/intake/session/{session_id}`, `POST /api/intake/session/{session_id}/answer`, `POST /api/intake/session/{session_id}/move`, `POST /api/intake/session/{session_id}/complete`.

- [ ] **Step 1: Add request models and imports**

Add Pydantic models for answer and movement requests.

- [ ] **Step 2: Add endpoint handlers**

Expose intake state, answer submission, previous/next movement, and completion.

- [ ] **Step 3: Keep record compatibility**

Allow `/api/save_record` to accept and persist `structured_answers`.

- [ ] **Step 4: Run backend tests**

Run: `python -m unittest discover -s backend/tests -v`
Expected: PASS.

### Task 3: Frontend Guided Workspace

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: new `/api/intake/session`, `/answer`, `/move`, and `/complete` endpoints.
- Produces: three-column guided intake UI with selectable answers, notes, progress, summary, and final report display.

- [ ] **Step 1: Replace chat shell with intake workspace**

Implement app state, loading, selected option, note input, progress, required question list, and collected summary.

- [ ] **Step 2: Render completion state**

Display final markdown report and saved record status after completion.

- [ ] **Step 3: Update global styling**

Move visual style toward the reference image: white surfaces, soft green accents, restrained cards, responsive layout.

- [ ] **Step 4: Build frontend**

Run: `npm run build`
Expected: build succeeds.

### Task 4: End-To-End Verification

**Files:**
- No new files expected.

**Interfaces:**
- Verifies backend and frontend work together.

- [ ] **Step 1: Run backend tests**

Run: `python -m unittest discover -s backend/tests -v`
Expected: PASS.

- [ ] **Step 2: Run frontend build**

Run: `npm run build`
Expected: build succeeds.

- [ ] **Step 3: Start services and inspect UI**

Start backend on port 8000 and frontend on port 5173. Open the app and check that the first screen renders, option selection works, progress updates, and completion shows a report.
