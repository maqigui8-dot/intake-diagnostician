# Task 2 Report: 基础测量和成人肥胖规则

## Status

DONE

## Scope Delivered

- 新增后端确定性基础测量校验、BMI 计算与成人 BMI 分级。
- 新增男女腰围阈值和腰臀比提示计算。
- 新增 `POST /api/intake/session/{session_id}/baseline`，校验后保存规范化基础资料。
- 会话新增 `baseline`、`bmi_assessment` 和 `baseline_confirmed`，不改变既有开放问答或追问状态。

## RED / GREEN Evidence

### RED 1: 规则模块不存在

Command:

```powershell
python -m unittest backend.tests.test_obesity_diagnosis -v
```

Result: `ModuleNotFoundError: No module named 'obesity_diagnosis'` as expected after writing the new diagnosis tests.

### GREEN 1: 确定性规则

Command:

```powershell
python -m unittest backend.tests.test_obesity_diagnosis -v
```

Result: `Ran 7 tests ... OK` after implementing BMI, central-obesity, validation, and the waist-to-hip boundary fix.

### RED 2: 会话基础资料接口不存在

Command:

```powershell
python -m unittest backend.tests.test_intake_flow -v
```

Result: `ImportError: cannot import name 'set_baseline' from 'intake_flow'` as expected after adding session and endpoint contract tests.

### GREEN 2: 会话和端点

Command:

```powershell
python -m unittest backend.tests.test_intake_flow -v
```

Result: `Ran 14 tests ... OK` after adding the session state, `set_baseline`, Pydantic request model, and endpoint.

### RED 3: 腰臀比边界

Command:

```powershell
python -m unittest backend.tests.test_obesity_diagnosis.ObesityDiagnosisTests.test_waist_hip_ratio_compares_before_rounding -v
```

Result: failed as expected because a male ratio of `0.85` was rounded to `0.9` before comparison and was incorrectly considered to reach the `0.90` threshold.

### GREEN 3: 比较原始比例

Command:

```powershell
python -m unittest backend.tests.test_obesity_diagnosis -v
```

Result: `Ran 7 tests ... OK` after comparing the unrounded ratio while retaining one-decimal display output.

## Final Verification

Focused command:

```powershell
python -m unittest backend.tests.test_obesity_diagnosis backend.tests.test_intake_flow -v
```

Result: `Ran 21 tests in 0.008s` and `OK`.

Full backend command, run once after focused verification:

```powershell
python -m unittest discover -s backend/tests -v
```

Result: `Ran 89 tests in 1.679s` and `OK`.

## Changed Files

- `backend/obesity_diagnosis.py` (new): validation, BMI and central-obesity rules.
- `backend/tests/test_obesity_diagnosis.py` (new): rule, validation, and threshold-boundary tests.
- `backend/intake_flow.py`: baseline session fields and validated storage function.
- `backend/main.py`: baseline request model and API endpoint.
- `backend/tests/test_intake_flow.py`: baseline state and endpoint contract tests.
- `.superpowers/sdd/task-2-report.md` (new): this report.

## Self-Review

- 成人 BMI 分级边界为 `<18.5`、`18.5-<24`、`24-<28`、`28-<32.5`、`32.5-<37.5`、`37.5-<50`、`>=50`。
- 腰围阈值为男性 `>=90 cm`、女性 `>=85 cm`；腰臀比按男性 `>=0.90`、女性 `>=0.85` 以未四舍五入的值比较。
- 未成年人、未知生理性别、超出身高/体重范围、非正腰围/臀围以及缺少测量时间均返回患者安全的中文信息。
- BMI `>=28` 时仅保存“当前BMI达到成人肥胖范围，最终结果需由医生结合测量和检查确认。”；未输出确诊、患病概率、辨证或处方。
- 未修改 `intake_execution.py`、`obesity_intake_schema.py`、Skills、医生端、前端或既有对话流程。
- 当前目录不是 Git 仓库；未初始化 Git、未提交，也未执行 Git 命令修改工作区。

## Concerns

无已知阻塞或遗留问题。前端基础资料表单和患者端 BMI 展示明确留给后续任务，未在 Task 2 提前实现。

## Review-Fix: Baseline Bypass Gate

### Finding and Scope

Review identified that a new session was created as `open_intake` while `baseline_confirmed=False`. As a result, open-answer, analysis, and manual completion paths could advance without adult baseline validation. This review fix is limited to the Task 2 backend flow, its API boundary, and affected backend tests. No frontend Task 6 work was added.

### RED Evidence

Command:

```powershell
python -m unittest backend.tests.test_intake_flow -v
```

Result: `Ran 18 tests` with `5` expected failures before production changes:

- New session reported `open_intake` instead of `baseline_collection`.
- `submit_open_answer` did not raise the required Chinese baseline error.
- `complete_intake_session` and `complete_structured_intake` allowed completion.
- `analyze_structured_intake` invoked analysis instead of returning a 400 error before baseline confirmation.

### GREEN Evidence

Focused command:

```powershell
python -m unittest backend.tests.test_intake_flow backend.tests.test_skill_analysis -v
```

Result: `Ran 57 tests in 1.698s` and `OK`.

Full backend command:

```powershell
python -m unittest discover -s backend/tests -v
```

Result: `Ran 93 tests in 1.715s` and `OK`.

### Review-Fix Changes

- `backend/intake_flow.py`: new sessions begin at `baseline_collection`; centralized baseline-confirmation guard blocks open answers, follow-up answers, analysis application, and manual completion; valid baseline submission moves the session to `open_intake`.
- `backend/main.py`: analyze and manual-complete endpoints map the guard's patient-safe Chinese `ValueError` to HTTP 400 before state-changing work begins.
- `backend/tests/test_intake_flow.py`: RED/GREEN coverage for the baseline phase, open-answer gate, analyze gate, manual-completion gates, and successful post-baseline transition.
- `backend/tests/test_skill_analysis.py`: existing flow and API tests now explicitly establish a valid baseline before exercising post-baseline paths.
- `.superpowers/sdd/task-2-report.md`: appended this review-fix evidence.

### Review-Fix Self-Review

- An unbaselined session remains `baseline_collection`; blocked open-answer and manual-complete tests verify it has no open answer and no report.
- The analyze guard runs before agent selection or timeout fallback, so it cannot turn an unbaselined session into `follow_up`.
- Baseline validation remains in `validate_baseline`; under-18 and invalid-measurement errors retain the existing deterministic Chinese messages.
