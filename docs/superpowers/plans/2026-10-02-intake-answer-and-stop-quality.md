# Intake Answer and Stop Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent repeated questions after clear answers and let a stopped-but-incomplete patient session be corrected without calling it a completed record.

**Architecture:** Keep rule-driven `decide_stop` and the existing core field set. Reconcile narrow, field-specific local evidence with online model extraction before calculating the next question. Reuse persisted unfinished sessions and the scoped correction API for draft completion; never promote ambiguous text or erase safety alerts.

**Tech Stack:** Python 3, unittest, FastAPI, SQLAlchemy, Vue 3, Node test runner, Vite.

## Global Constraints

- Preserve all existing MySQL sessions and saved reports.
- Keep `PATIENT_CORE_FIELD_KEYS` unchanged.
- AI may extract evidence and phrase questions; deterministic code owns field state and stop decisions.
- A stopped incomplete session is a draft, not an official completed record.
- Do not clear recorded danger signals via patient correction.

---

### Task 1: Reconcile explicit current answers before question selection

**Files:** Modify `backend/skill_analysis.py`; test `backend/tests/test_skill_analysis.py`.

**Interfaces:** Consume `extract_local_follow_up_field(key, answer)` and current session state; produce a field update for unambiguous current-key negative answers and durations even when online extraction omits them.

- [ ] **Step 1: Write failing tests.** Add two `FakeAgent` process-turn cases: the model returns empty `field_updates` after `stool_urine` gets `没有` and after `onset_course` gets `一年`; assert the field is confirmed and `current_field_key` advances.
- [ ] **Step 2: Run red tests.** `cd backend && python -m unittest tests.test_skill_analysis -v`; expect the two new assertions to fail because online extraction omitted the answer.
- [ ] **Step 3: Implement minimal reconciliation.** In `process_intake_turn`, for the latest non-clarification follow-up, call `extract_local_follow_up_field` only when the answer is a direct negative or the key is `onset_course`; if it confirms the current key and there is no unresolved conflict, replace weaker model updates for that key. Keep existing evidence and red-flag filters.
- [ ] **Step 4: Run green tests.** Run the same unittest module; expect all pass. Add one regression test where an unresolved conflict prevents a simple negative from silently resolving it.

### Task 2: Draft correction and completion transition

**Files:** Modify `backend/intake_flow.py`, `backend/intake_views.py`; test `backend/tests/test_patient_review.py`, `backend/tests/test_multi_patient_api.py`.

**Interfaces:** Existing `correct_patient_field(session_id, field_key, value, patient_id=None)` accepts a currently blocking applicable core key in `incomplete`, while retaining the five review keys; public `review_fields` includes editable blocking keys and `blocking_fields` gives labels and status.

- [ ] **Step 1: Write failing tests.** Build an incomplete session with `stool_urine` unavailable and two attempts. Assert `build_patient_state` exposes that blocker, correction `没有` confirms it, and all-core-confirmed correction transitions to `completed`. Assert unrelated text is rejected or remains partial, and correction cannot clear an existing danger signal.
- [ ] **Step 2: Run red tests.** `cd backend && python -m unittest tests.test_patient_review tests.test_multi_patient_api -v`; expect missing draft blocker/edit behavior.
- [ ] **Step 3: Implement minimal correction.** Extend the whitelist only for `incomplete` blocking core keys. Validate new draft values with `extract_local_follow_up_field` in a local import to avoid a module import cycle; a recognized unavailable phrase remains unavailable. Reject unrelated/ambiguous values with a clear `ValueError`. Preserve original Q&A and correction audit. For red flags, never remove old alerts; append newly detected explicit danger signals. Re-run `evaluate_patient_readiness` and regenerate report after accepted corrections.
- [ ] **Step 4: Expose draft gaps.** In `build_patient_state`, provide public `blocking_fields` with field label/status and extend `review_fields` on incomplete sessions to these fields; omit the synthetic `baseline` key because baseline has its own editor.
- [ ] **Step 5: Run green tests.** Run both unittest modules and verify all pass; keep formal save rejecting `incomplete`.

### Task 3: Patient-facing draft explanation and edit path

**Files:** Modify `frontend/src/App.vue`, `backend/intake_views.py`, `backend/intake_flow.py`; test `frontend/tests/follow-up-stage.test.mjs` and existing patient-interface tests.

**Interfaces:** Incomplete result shows the missing field names and correction controls; only `completed` can call `/save`.

- [ ] **Step 1: Write failing front-end tests.** Assert incomplete result exposes the public blocking fields, has editable correction rows, and does not promise future in-clinic verification. Assert `canSaveIntakeRecord` stays false for `incomplete`.
- [ ] **Step 2: Run red tests.** `cd frontend && node --test tests/*.test.mjs`; expect the new source/UI assertions to fail.
- [ ] **Step 3: Implement minimal UI/copy.** Display the `blocking_fields` list, label the result a saved session draft rather than a completed file, reuse correction controls, and remove “诊中补充” default copy from patient-facing messages. Keep `saveRecord` button exclusive to completed phase.
- [ ] **Step 4: Run green tests.** Re-run front-end tests and `node build-app.mjs`; expect exit 0.

### Task 4: Full regression and documentation

**Files:** Update `README.md` only where workflow descriptions are now stale; add cases to `backend/evaluation/cases.json` if the current deterministic runner can represent them without new machinery.

- [ ] **Step 1: Review the spec against the diff.** Check that no core field scope changed, no danger signal can be deleted, and incomplete reports cannot be saved as completed records.
- [ ] **Step 2: Run full verification.** `cd backend && python -m unittest discover -s tests`; `cd frontend && node --test tests/*.test.mjs`; `cd frontend && node build-app.mjs`; `git diff --check`.
- [ ] **Step 3: Document verified behavior.** Update README only for draft correction/stop wording. State offline and live-model evidence separately; do not claim clinical validation.
