# Task 7 Report — 医生端分层档案和检查候选

## What changed

### Backend
- `backend/exam_recommendations.py`
  - Added `trigger`, `source`, `rule_version` to every exam item, while keeping `type` and `department` (still rendered by the patient result view in `frontend/src/App.vue`, which was NOT modified).
  - `source` = `国家卫生健康委《肥胖症诊疗指南（2024年版）》`; `rule_version` = schema `RULE_VERSION` (`adult-obesity-intake-v1`); `trigger` states the triggering field/evidence.
  - Introduced a small `_exam(...)` helper to avoid duplicating the shared metadata.
  - Red flags still return `[]` (routine package suppressed); the safety alert stays a separate concern.
- `backend/intake_views.py`
  - Added top-level `baseline_assessment` (from `internal_state["baseline"]` + `["bmi_assessment"]`, plus a `rule_hint` about adult-only BMI rule and doctor confirmation) and `layer_execution` (four layer entries: baseline/risk/tcm/safety, each with score, threshold, raw, max).
  - Reorganized `field_groups` from status-keyed (`confirmed`/`partial`/...) into the six design sections: 基础测量与肥胖范围 / 肥胖病程与可能病因 / 相关疾病风险 / 生活方式与心理情况 / 中医诊前资料 / 待医生确认, mapping via `definition.layer` + `definition.group`.
  - Kept `execution`, `safety_fields`, `legacy_fields`, `blocking_keys`, `conflicts`, `safety_alerts`, `recommended_exams`, `rule_version` for backward compatibility.
  - `build_patient_state` untouched — no execution details leaked to the patient view.
- `backend/tests/test_intake_views.py` — added tests for `baseline_assessment`, `layer_execution`, six-section `field_groups`, and patient-state omission.
- `backend/tests/test_exam_recommendations.py` — added tests for the 7 required exam fields + retained type/department, source/rule_version, trigger, no-diagnosis-wording on missing data, and red-flag suppression.

### Frontend
- `frontend/src/components/DoctorExecutionPanel.vue` — rewritten to the six-section layered model: baseline measurements + BMI + rule hint, four layer statuses with scores and rule version, per-section field groups with evidence/status, plus 待医生确认 aggregation (conflicts, safety alerts, exam candidates rendering `name`/`reason`/`trigger`/`priority`/`source`/`precautions`). Read-only (no editable clinical decisions).
- `frontend/src/style.css` — appended minimal new classes (baseline grid, layer grid, field rows, pending blocks, exam list) without modifying existing rules.
- `frontend/tests/doctor-view.test.mjs` — added source-read tests asserting the six section headings and rendering of `baseline_assessment` / `layer_execution` / `recommended_exams` / exam metadata.

## RED failing output (before implementation)

`python -m unittest backend.tests.test_intake_views backend.tests.test_exam_recommendations -v`

- FAILED (failures=2, errors=4)
- errors:
  - `test_doctor_summary_exposes_baseline_assessment_with_bmi_and_rule_hint` — KeyError: 'baseline_assessment'
  - `test_doctor_summary_exposes_four_layer_scores` — KeyError: 'layer_execution'
  - `test_exam_source_and_rule_version_reference_guideline` — KeyError: 'rule_version'
  - `test_metabolic_history_triggers_glycated_hemoglobin_with_trigger` — KeyError: 'trigger'
- failures:
  - `test_doctor_summary_groups_fields_into_six_sections` — AssertionError (section key missing from field_groups)
  - `test_every_exam_carries_required_metadata_fields` — AssertionError: 'trigger' not found in item

## GREEN passing output (after implementation)

- `python -m unittest backend.tests.test_intake_views backend.tests.test_exam_recommendations -v` → Ran 19 tests, OK
- `python -m unittest discover -s backend/tests -v` → Ran 144 tests, OK (0 failures)
- `cd frontend && npm test` → 29 pass, 0 fail
- `cd frontend && npm run build` → built in 1.02s (exit 0)

## Files changed

- `backend/exam_recommendations.py`
- `backend/intake_views.py`
- `backend/tests/test_intake_views.py`
- `backend/tests/test_exam_recommendations.py`
- `frontend/src/components/DoctorExecutionPanel.vue`
- `frontend/src/style.css`
- `frontend/tests/doctor-view.test.mjs`

## Concerns

- None blocking. The exam candidate model path in `backend/skill_analysis.py` (`_normalize_exams`) still emits the pre-Task-7 6-field shape (name/type/department/reason/priority/precautions); however the session-persisted `recommended_exams` (which the doctor summary and patient result view consume) always comes from `build_recommended_exams` (via `process_intake_turn`), so it always carries `trigger`/`source`/`rule_version`. `skill_analysis.py` was out of scope per the task file list and was not modified.
- The safety-layer fields (allergies/medications/important_history/pregnancy/red_flags) are placed under 待医生确认 because they are hard-required safety data that the doctor must confirm; the remaining "缺失/无法提供/矛盾/安全提醒/检查候选" items are aggregated under that same section in the frontend.
