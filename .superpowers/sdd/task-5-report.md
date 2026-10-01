# Task 5 Report — 更新两个 Skill

## Status: DONE

## What changed

### 1. `backend/tests/test_skill_analysis.py`
- Added a new test class `SkillSourceContractTests` with two methods:
  - `test_checklist_describes_four_layers_and_deterministic_authority` — asserts the checklist SKILL.md contains `基础诊断硬性字段`, `病因与风险资料`, `中医诊前资料`, `AI不得修改停止条件`.
  - `test_questioning_guide_documents_clarification_rules` — asserts the questioning SKILL.md contains `澄清请求不作为医学证据`, `先解释再重新询问`, `不消耗追问次数`.
- Updated the existing `test_skills_are_scoped_to_obesity_execution_and_patient_safe_language` to drop the now-obsolete two-part terms (`辨证资料执行度`, `开方安全执行度`) and assert `安全硬性字段` instead, so it stays consistent with the new four-layer model.

### 2. `backend/skills/tcm-intake-checklist/SKILL.md`
Rewrote from the old two-part model (辨证资料 / 开方安全资料) to the four-layer model:
- baseline = 基础诊断硬性字段 (年龄、生理性别、身高、体重、BMI)
- risk = 病因与风险资料 (threshold 80%)
- tcm = 中医诊前资料 (threshold 70%)
- safety = 安全硬性字段 (危险信号、过敏史、当前用药、重要既往疾病; threshold 100%)
- Classified fields required / conditional / optional.
- Stated that scoring/thresholds/completion are owned by deterministic code; LLM extracts evidence only and `AI不得修改停止条件`.
- Kept the adult-only (18+) boundary and physician-confirmation language `达到成人肥胖范围，待医生确认`.

### 3. `backend/skills/tcm-questioning-guide/SKILL.md`
- Added everyday-language explanations for BMI、腰围、过敏、既往疾病、检查项目 and TCM symptom concepts.
- Added clarification rule: `澄清请求不作为医学证据`, `先解释再重新询问`, `不消耗追问次数`.
- Added refusal handling (记录“无法提供”，最多委婉确认一次) and contradiction handling (前后矛盾 → partial，交由医生核实).
- Kept one-main-information-point-per-turn rule and the ban on exposing internal field keys/scores/missing items/stop conditions.

## RED (expected failures) — Step 1

`python -m unittest backend.tests.test_skill_analysis -v` failed with 3 failures:

```
FAIL: test_skills_are_scoped_to_obesity_execution_and_patient_safe_language (...SkillConfigurationTests)
AssertionError: '安全硬性字段' not found in '---\nname: tcm-intake-checklist...'

FAIL: test_checklist_describes_four_layers_and_deterministic_authority (...SkillSourceContractTests)
AssertionError: '基础诊断硬性字段' not found in '---\nname: tcm-intake-checklist...'

FAIL: test_questioning_guide_documents_clarification_rules (...SkillSourceContractTests)
AssertionError: '澄清请求不作为医学证据' not found in '---\nname: tcm-questioning-guide...'

Ran 52 tests in 4.060s
FAILED (failures=3)
```

(Note: the Windows console mangles UTF-8 in traceback output, but the assertions failed purely because the phrases were absent — the file contents were read correctly as UTF-8.)

## GREEN (passing output) — Step 4

`python -m unittest backend.tests.test_skill_analysis -v`:

```
Ran 52 tests in 4.046s
OK
```

`python -m unittest discover -s backend/tests -v`:

```
Ran 134 tests in 3.954s
OK
```

0 failures across the full backend suite.

## Files changed

- `backend/tests/test_skill_analysis.py` (added SkillSourceContractTests; updated one obsolete assertion)
- `backend/skills/tcm-intake-checklist/SKILL.md` (rewritten to four-layer model)
- `backend/skills/tcm-questioning-guide/SKILL.md` (rewritten with clarification/refusal/contradiction rules)

## Concerns

- `test_skills_are_scoped_to_obesity_execution_and_patient_safe_language` was modified (not just extended) because it encoded the old two-part terms that this task explicitly replaces. This is within the three allowed files and is required to keep the full suite green.
- No files outside the three listed were touched. No git commands were run (the directory is not a git repo).
