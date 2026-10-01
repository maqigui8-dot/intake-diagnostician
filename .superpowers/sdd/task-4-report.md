# Task 4 Report

## Scope

Implemented layered follow-up selection, offline fallback continuation, deterministic stop handling, and patient-evidence validation for model field updates. No Skill, frontend, or doctor-view files were changed.

## RED

Commands run before production changes:

```powershell
python -m unittest backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v
```

Result: 55 tests run, 5 expected failures:

- Offline fallback stopped after safety fields.
- Baseline blocker was not retained in a terminal decision.
- Baseline-derived height/weight was selected before risk fields.
- An unresolved confirmed-field conflict did not trigger a retry.
- A model update without patient-provided evidence was accepted.

```powershell
python -m unittest backend.tests.test_skill_analysis.SkillAnalysisTests.test_process_turn_accepts_punctuation_normalized_multi_field_evidence -v
```

Result: 1 expected failure because the unsupported `allergies` update was accepted with the two valid updates.

## GREEN

```powershell
python -m unittest backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v
```

Result: 55 tests passed.

```powershell
python -m unittest discover -s backend/tests -v
```

Result: 126 tests passed, 0 failures, 0 errors.

## Modified Files

- `backend/intake_question_policy.py`
- `backend/skill_analysis.py`
- `backend/tests/test_intake_question_policy.py`
- `backend/tests/test_skill_analysis.py`
- `.superpowers/sdd/task-4-report.md`

## Self-Review

- Selection skips baseline conversational fields and orders collectable gaps by safety, risk, then TCM; unresolved conflicts are eligible for retry.
- Completion remains delegated to `evaluate_threshold`, which requires Task 3 baseline/risk/TCM/safety gates and has no global round-count condition.
- Offline mode now selects all applicable non-baseline fields and uses existing `question_for_field()` fallback questions.
- Model field updates require non-empty normalized evidence contained in one individual non-clarification patient answer; valid multi-field updates from one answer remain independent.
- Model red-flag labels are also constrained to patient-answer evidence; deterministic local red-flag detection remains available offline.

## Residual Risk

Evidence matching intentionally permits only whitespace and punctuation normalization. Legitimate paraphrases that do not occur verbatim after this normalization are rejected and will require a later patient answer or clinician review.

## Re-review Fix

### RED

```powershell
python -m unittest backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_irrelevant_answer_does_not_confirm_current_safety_field backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_second_irrelevant_answer_advances_without_confirming_field backend.tests.test_skill_analysis.SkillAnalysisTests.test_open_clarification_is_not_model_evidence -v
```

Result: 3 expected failures. Offline `provided` answers falsely confirmed the current field, and a clarification-style `open_answer` was accepted as model evidence.

```powershell
python -m unittest backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_unrelated_mention_of_medicine_does_not_confirm_medications -v
```

Result: 1 expected failure. A bare `药` character falsely confirmed the medications field.

### GREEN

```powershell
python -m unittest backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_irrelevant_answer_does_not_confirm_current_safety_field backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_second_irrelevant_answer_advances_without_confirming_field backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_unrelated_mention_of_medicine_does_not_confirm_medications backend.tests.test_skill_analysis.SkillAnalysisTests.test_open_clarification_is_not_model_evidence -v
```

Result: 4 tests passed.

```powershell
python -m unittest backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v
```

Result: 59 tests passed.

```powershell
python -m unittest discover -s backend/tests -v
```

Result: 130 tests passed, 0 failures, 0 errors.

### Re-review Self-Review

- Offline `provided` follow-up answers now confirm a field only when a field-specific deterministic rule matches; otherwise the field becomes `partial` without invented evidence.
- A partial field is re-asked once and, after the existing second-attempt limit, the selector advances to the next collectable field without satisfying hard gates.
- Clarification-style open answers are omitted from model evidence sources, so matching model text cannot confirm a field.
- Medication extraction requires an explicit medication-use or medication-denial phrase; a bare, unrelated `药` character is insufficient.

### Re-review Residual Risk

Offline deterministic extraction intentionally recognizes only narrow, explicit phrasing. Ambiguous but clinically relevant answers remain `partial` for the second retry or clinician review instead of being inferred.

## Second Re-review Fix

### RED

```powershell
python -m unittest backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_direct_negative_confirms_each_current_safety_field backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_open_clarification_skips_local_basic_extraction -v
```

Result: both tests failed as expected: all four safety-field subtests kept a direct `没有` at `partial`, and an offline clarification-style open answer confirmed `main_goal` through local extraction.

### GREEN

```powershell
python -m unittest backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_direct_negative_confirms_each_current_safety_field backend.tests.test_skill_analysis.SkillAnalysisTests.test_offline_open_clarification_skips_local_basic_extraction -v
```

Result: 2 tests passed, including all four safety-field subtests.

```powershell
python -m unittest backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v
```

Result: 61 tests passed.

```powershell
python -m unittest discover -s backend/tests -v
```

Result: 132 tests passed, 0 failures, 0 errors.

### Second Re-review Self-Review

- Exact normalized direct negations (`没有`, `无`, `否`, `否认`, `未`) confirm only the current `red_flags`, `allergies`, `medications`, or `important_history` field.
- The direct-negation path is unavailable to every other field and requires an exact answer after punctuation and whitespace normalization; unrelated text remains partial under the existing retry policy.
- Clarification detection now includes `open_answer`, so offline local extraction cannot infer `main_goal` from `想减重是什么意思？`.

### Second Re-review Residual Risk

The intentionally strict direct-negation allowlist may leave colloquial negative replies partial when they are not an exact allowed phrase. This favors preserving hard safety gates over inferring a negative medical history.
