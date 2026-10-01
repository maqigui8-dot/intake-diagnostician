# Task 6 Report — 患者端基础资料和结果展示

## Status
DONE

## What changed

### Backend
- `backend/intake_views.py` — `build_patient_state()` now includes two new keys:
  - `"baseline": internal_state.get("baseline")`
  - `"bmi_assessment": internal_state.get("bmi_assessment")`
  - `context` / `execution` / `field_states` / `blocking_keys` remain excluded (unchanged).

### Frontend
- `frontend/src/follow-up-stage.js` — `getIntakeViewStage()` returns `'baseline_collection'` when `state.phase === 'baseline_collection'` (inserted before the `open_intake` case).
- `frontend/src/App.vue`:
  - New `baseline_collection` template section (before `open_intake`): numeric inputs for age/height/weight/waist/hip with explicit units + min/max constraints, a segmented 男/女 control, an optional waist/hip block, and a `date` input for measurement date.
  - Submit button disabled via `baselineValid` until age (>=18), sex, height (100–250), weight (20–500) and measured date are valid.
  - `submitBaseline()` POSTs to `/api/intake/session/{sessionId}/baseline`, converts empty optional waist/hip to `null`, preserves values on validation error via `formError`, and transitions via the returned state (phase becomes `open_intake`).
  - `loadState()` pre-fills the form from `state.baseline` when present.
  - Result section renders a BMI card: `state.bmi_assessment.bmi`, `state.bmi_assessment.bmi_grade`, and the static patient-safe copy `达到成人肥胖范围，待医生确认` (gated on `state.bmi_assessment.diagnosis_copy`). No "确诊" wording added.
- `frontend/src/style.css` — added `.baseline-form`, `.baseline-grid`, `.field`, `.segmented`, `.baseline-optional`, `.bmi-card`, `.bmi-row`, `.diagnosis-copy` styles; baseline form included in the 860px single-column + padding rules.

### Tests
- `frontend/tests/follow-up-stage.test.mjs` — added test: baseline_collection phase → `'baseline_collection'`.
- `frontend/tests/patient-visibility.test.mjs` — added tests: baseline inputs (age/sex/height/weight/waist/hip/measured date) present; no `确诊`/`肥胖症`; result renders BMI + `达到成人肥胖范围，待医生确认`.
- `backend/tests/test_intake_views.py` — added `test_patient_state_exposes_baseline_and_bmi_assessment` (exposes both keys, and still excludes `execution`/`field_states`/`blocking_keys`).

## RED (failing) output — captured before implementation

Backend (`python -m unittest tests.test_intake_views -v`):
```
ERROR: test_patient_state_exposes_baseline_and_bmi_assessment
  File ".../test_intake_views.py", line 35, in test_patient_state_exposes_baseline_and_bmi_assessment
    self.assertEqual(public["baseline"], state["baseline"])
KeyError: 'baseline'
Ran 7 tests in 0.005s
FAILED (errors=1)
```

Frontend (`npm test`):
```
✖ 新会话首先进入基础资料收集阶段
  (getIntakeViewStage returned 'analyzing')
✖ 患者模板展示基础资料输入（...）
  expected: /baseline\.age/  (not found in template)
✖ 结果区展示 BMI 与医生确认文案
  expected: /state\.bmi_assessment\.bmi/  (not found in result section)
```

## GREEN (passing) output — after implementation

Backend (`python -m unittest discover -s tests -v`):
```
Ran 135 tests in 4.025s
OK
```

Frontend (`npm test`):
```
ℹ tests 22
ℹ pass 22
ℹ fail 0
ℹ duration_ms 170.7854
```

Frontend (`npm run build`):
```
vite v6.4.3 building for production...
✓ 89 modules transformed.
✓ built in 1.04s   (exit 0)
```

## Files changed
- `backend/intake_views.py`
- `backend/tests/test_intake_views.py`
- `frontend/src/App.vue`
- `frontend/src/follow-up-stage.js`
- `frontend/src/style.css`
- `frontend/tests/follow-up-stage.test.mjs`
- `frontend/tests/patient-visibility.test.mjs`

## Concerns
- The result section renders the short static patient-safe copy `达到成人肥胖范围，待医生确认` (mandated by the global constraint) and uses `state.bmi_assessment.diagnosis_copy` as the visibility gate, rather than rendering the backend's longer `diagnosis_copy` sentence verbatim. This is intentional to honor "患者端只能显示“达到成人肥胖范围，待医生确认”". The full backend copy remains available on the doctor view only.
- The left `flowStages` panel was intentionally left unchanged: for a fresh `baseline_collection` session its first stage ("开放描述") still shows as `completed`, which is slightly misleading but out of this task's scope and not covered by any test. Flagging for a later polish pass.
- No git operations performed; nothing under `.superpowers/sdd/task-6-before/` or the brief was modified.

## Fix

Addresses the one Important finding (1) and four Minor findings (2–5) from review.

### 1. Baseline editable after submission (Important)
`frontend/src/App.vue`:
- Added `editingBaseline` ref (default `false`).
- Baseline section condition changed to `state && (viewStage === 'baseline_collection' || editingBaseline)`.
- Added `canEditBaseline` computed: true when `!editingBaseline` and phase is not `baseline_collection`/`completed`/`escalated` (so editing is offered mid-flow and for `incomplete`, but not after a completed/escalated intake).
- Added "编辑基础资料" affordances: a link in the left panel (mid-flow) and a button inside the BMI card in the result section (for `incomplete`), both gated on `canEditBaseline` and calling `startEditBaseline()`.
- Added `fillBaselineForm()` (extracted from the previous inline pre-fill in `loadState()`, which now calls it), `startEditBaseline()` (pre-fills from `state.baseline`, clears error, sets `editingBaseline = true`), and `cancelEditBaseline()` (sets `editingBaseline = false` without submitting).
- `submitBaseline()` now sets `editingBaseline.value = false` on success (backend returns `open_intake`); on validation error the form stays visible with `formError`. Submit button label shows 保存修改 while editing; a 取消 button appears only when editing.
- `restart()` also resets `editingBaseline`.
- Backend `set_baseline` left unchanged (re-submit resets phase to `open_intake`, as required).

### 2. flowStages premature ✓ during baseline_collection (Minor)
`frontend/src/App.vue` `flowStages`: added a leading "基础资料" stage (`current` during `baseline_collection`, otherwise `completed`) and marked "开放描述" as `pending` during `baseline_collection`.

### 3. Client validation mirrors backend (Minor)
`frontend/src/App.vue` `baselineValid`: age now `Number.isInteger(age) && age >= 18 && age <= 120` (mirrors `obesity_diagnosis.py` upper bound 120 and integer rule); height 100–250, weight 20–500 unchanged; waist/hip now must be `> 0` when provided via a shared `optionalPositive` check. Age field hint updated to "18–120".

### 4. No wrong-screen flash on baseline submit (Minor)
`frontend/src/follow-up-stage.js`: moved the `state.phase === 'baseline_collection'` check before the `saving → analyzing` short-circuit, so a baseline submit stays on `baseline_collection` while saving (the button's 正在提交... state stays visible).

### 5. Backend test asserts context exclusion (Minor)
`backend/tests/test_intake_views.py` `test_patient_state_exposes_baseline_and_bmi_assessment`: added `self.assertNotIn("context", public)`.

### Tests added/changed
- `frontend/tests/follow-up-stage.test.mjs`: added "基础资料提交中保持基础资料阶段而不是闪到整理中" (item 4).
- `frontend/tests/patient-visibility.test.mjs`: added "基础资料提交后仍可编辑…" (item 1), "基础资料校验与后端规则一致…" (item 3), "流程进度为基础资料阶段给出正确状态" (item 2).
- `backend/tests/test_intake_views.py`: added `context` exclusion assertion (item 5).

### Verification
- `cd frontend && npm test` → 26 pass / 0 fail.
- `cd frontend && npm run build` → exit 0 (89 modules transformed).
- `python -m unittest backend.tests.test_intake_views -v` → 7 tests OK.
- `python -m unittest discover -s backend/tests -v` → 135 tests OK.
