# Task 1 Report: 澄清回答与键盘发送

## Status

DONE_WITH_CONCERNS

## Implementation Summary

- Added `is_clarification_request(answer: str) -> bool` for short clarification requests containing one of: `这是什么`, `什么意思`, `没听懂`, `没明白`, `能解释`, or `请解释`.
- Follow-up clarification answers are retained in history with `answer_quality="clarification"`, but do not update field attempts or consume retry capacity.
- The field-selection policy and the next-question attempt calculation both exclude clarification rows.
- `process_intake_turn` discards all extraction updates, conflicts, and red flags for a clarification answer, retains the same field as eligible, and supplies a fixed explanatory retry without requesting another model-generated question.
- Replaced both Ctrl+Enter bindings with IME-safe Enter handlers. Enter sends, Shift+Enter preserves the textarea newline, and composition input never sends. Both composers display `按 Enter 发送，Shift + Enter 换行`.

## Changed Files

- `backend/intake_question_policy.py`
- `backend/intake_flow.py`
- `backend/skill_analysis.py`
- `frontend/src/App.vue`
- `backend/tests/test_intake_flow.py`
- `backend/tests/test_intake_question_policy.py`
- `backend/tests/test_skill_analysis.py`
- `frontend/tests/patient-visibility.test.mjs`
- `.superpowers/sdd/task-1-report.md`

The first eight files were compared against `.superpowers/sdd/task-1-before/`; all and only those Task 1 implementation/test files differ from their snapshots.

## RED Evidence

### Backend

Command:

```powershell
python -m unittest backend.tests.test_intake_flow backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v
```

Exit code: `1`

Observed output (verbatim failing portion):

```text
FAIL: test_clarification_does_not_consume_attempt_or_update_field (backend.tests.test_intake_flow.IntakeFlowTests.test_clarification_does_not_consume_attempt_or_update_field)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\Administrator\Desktop\codex\code\backend\tests\test_intake_flow.py", line 80, in test_clarification_does_not_consume_attempt_or_update_field
    self.assertEqual(state["follow_up_answers"][-1]["answer_quality"], "clarification")
AssertionError: 'provided' != 'clarification'
- provided
+ clarification

ERROR: test_intake_question_policy (unittest.loader._FailedTest.test_intake_question_policy)
----------------------------------------------------------------------
ImportError: cannot import name 'is_clarification_request' from 'intake_question_policy' (C:\Users\Administrator\Desktop\codex\code\backend\intake_question_policy.py)

FAIL: test_process_turn_discards_model_updates_for_clarification_request (backend.tests.test_skill_analysis.SkillAnalysisTests.test_process_turn_discards_model_updates_for_clarification_request)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\Administrator\Desktop\codex\code\backend\tests\test_skill_analysis.py", line 198, in test_process_turn_discards_model_updates_for_clarification_request
    self.assertEqual(state["field_states"]["allergies"]["status"], "not_asked")
AssertionError: 'confirmed' != 'not_asked'
- confirmed
+ not_asked

----------------------------------------------------------------------
Ran 51 tests in 1.856s

FAILED (failures=2, errors=1)
```

### Frontend

The requested PowerShell command, `npm test -- --test-name-pattern="回车|对话"`, could not run because this Windows profile blocks `npm.ps1`. The equivalent command that exposed the actual RED failure was:

```powershell
npm.cmd test -- --test-name-pattern=Enter
```

Exit code: `1`

Observed output (verbatim result):

```text
✖ Enter sends while Shift+Enter keeps a newline
AssertionError [ERR_ASSERTION]: The input did not match the regular expression /@keydown\.enter="handleOpenEnter"/.
Expected: /@keydown\.enter="handleOpenEnter"/

ℹ tests 17
ℹ pass 16
ℹ fail 1
```

## GREEN Evidence

### Focused Backend

Command:

```powershell
python -m unittest backend.tests.test_intake_flow backend.tests.test_intake_question_policy backend.tests.test_skill_analysis -v
```

Exit code: `0`

```text
test_clarification_does_not_consume_attempt_or_update_field ... ok
test_clarification_requests_are_detected_and_do_not_consume_attempts ... ok
test_process_turn_discards_model_updates_for_clarification_request ... ok
----------------------------------------------------------------------
Ran 58 tests in 1.860s

OK
```

### Focused Frontend

Command:

```powershell
npm.cmd test -- --test-name-pattern=Enter
```

Exit code: `0`

```text
✔ Enter sends while Shift+Enter keeps a newline
ℹ tests 17
ℹ pass 17
ℹ fail 0
```

## Full-Suite Results

### Backend

Command run from `backend`:

```powershell
python -m unittest discover -s tests -v
```

Exit code: `0`

```text
Ran 79 tests in 1.763s

OK
```

### Frontend

Command run from `frontend`:

```powershell
npm.cmd test
```

Exit code: `0`

```text
ℹ tests 17
ℹ pass 17
ℹ fail 0
ℹ duration_ms 174.9361
```

## Self-Review

- The clarification classifier normalizes whitespace and trailing Chinese/ASCII punctuation, and its 24-character limit prevents longer substantive replies from being classified as clarification requests.
- Attempt accounting excludes clarification history in every relevant path: policy selection, follow-up submission, and next-question numbering.
- Clarification processing clears all model-derived updates before merge and uses a fixed retry, so model output cannot turn a clarification into evidence or move the flow past the current field.
- The Enter helper checks `event.isComposing` before calling `preventDefault()` or submission, then separately permits Shift+Enter for multiline input.
- No Task 2+ production modules, tests, dependencies, or project metadata were changed.

## Concerns

- PowerShell execution policy blocks `npm.ps1`; all frontend test evidence uses the equivalent `npm.cmd` command.
- The focused frontend test is intentionally source-level, as specified by the task. The full frontend suite passes, but no browser-level IME composition simulation exists in the current test stack.
- The declared workspace path `C:\Users\Administrator\Desktop\code` was missing. To use the required `apply_patch` workflow, a junction was created at that path targeting `C:\Users\Administrator\Desktop\codex\code`; it is outside the project root and is not a changed project file.

## Review Fix

### Root Cause

`process_intake_turn` cleared model-derived data for a clarification answer, but it still called `extract_local_red_flags()` on `latest_answer` and merged that result. Therefore, the clarification `胸痛是什么意思？` was incorrectly converted into confirmed `red_flags` evidence and a safety alert.

### Changed Files

- `backend/skill_analysis.py`
- `backend/tests/test_skill_analysis.py`
- `.superpowers/sdd/task-1-report.md`

No frontend or Task 2 files were changed by this review fix.

### RED

Command run from `backend`:

```powershell
python -m unittest tests.test_skill_analysis.SkillAnalysisTests.test_clarification_with_red_flag_word_creates_no_safety_evidence -v
```

Exit code: `1`

```text
test_clarification_with_red_flag_word_creates_no_safety_evidence (tests.test_skill_analysis.SkillAnalysisTests.test_clarification_with_red_flag_word_creates_no_safety_evidence) ... FAIL

FAIL: test_clarification_with_red_flag_word_creates_no_safety_evidence (tests.test_skill_analysis.SkillAnalysisTests.test_clarification_with_red_flag_word_creates_no_safety_evidence)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\Administrator\Desktop\codex\code\backend\tests\test_skill_analysis.py", line 219, in test_clarification_with_red_flag_word_creates_no_safety_evidence
    self.assertEqual(state["field_states"]["red_flags"]["status"], "not_asked")
AssertionError: 'confirmed' != 'not_asked'
- confirmed
+ not_asked

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
```

### GREEN

Focused command run from `backend`:

```powershell
python -m unittest tests.test_skill_analysis -v
```

Exit code: `0`

```text
test_clarification_with_red_flag_word_creates_no_safety_evidence ... ok
test_process_turn_locally_detects_red_flag_when_agent_omits_it ... ok
----------------------------------------------------------------------
Ran 39 tests in 1.795s

OK
```

Full backend command run from `backend`:

```powershell
python -m unittest discover -s tests -v
```

Exit code: `0`

```text
Ran 80 tests in 1.814s

OK
```

### Self-Review

- Local red-flag extraction now occurs only when the latest response is not classified as clarification, so clarification text cannot create local safety evidence.
- The guard is scoped to the local extraction call; normal red-flag detection remains covered by `test_process_turn_locally_detects_red_flag_when_agent_omits_it`, which passed in the focused run.
- The new regression asserts no `red_flags` status/evidence and no `safety_alerts`, while retaining `red_flags` as the current field and an explanatory retry.
