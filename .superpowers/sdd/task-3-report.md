# Task 3 Report: 指南字段注册和分层完整度

## Status

DONE

## Scope Delivered

- `FieldDefinition` 新增 `layer: Literal["baseline", "risk", "tcm", "safety"]`，同时保留 `section` 兼容字段。
- 新增指南字段：`childhood_obesity`、`family_history`、`smoking`、`alcohol`、`work_activity`、`binge_eating`。
- 将 `metabolic_tests` 拆为 `glucose_tests`、`lipid_tests`、`uric_acid_test`、`liver_tests`、`kidney_tests`、`thyroid_tests`。
- 风险、中医、安全三层分别按适用字段权重归一化为 `0-100`，输出 `baseline_ready`、`risk_score`、`tcm_score`、`safety_score` 和显式 `blocking_keys`。
- 完成判定改为基础资料已确认、风险分数 `>=80`、中医分数 `>=70`、安全分数 `>=100`，并且没有未解决的硬性/优先字段或字段冲突。
- `differentiation_score` 和 `total_score` 仅保留为兼容输出；`evaluate_threshold` 不再使用旧 `total_score >= 85` 门槛。
- 新会话在 `context["baseline_confirmed"]` 中初始化 `False`，验证基础资料后写入 `True` 并重算执行结果。
- 增加旧 `metabolic_tests` 状态和更新向六个新检查组迁移的兼容路径。

## RED / GREEN Evidence

### RED 1: 注册表和分层门槛

写入新 schema/execution 测试后运行：

```powershell
python -m unittest backend.tests.test_obesity_intake_schema backend.tests.test_intake_execution -v
```

结果：`Ran 19 tests`，`5 failures, 5 errors`，均为预期的缺失功能：

- `FieldDefinition` 没有 `layer`。
- 12 个指南字段尚未注册，旧 `metabolic_tests` 仍存在。
- 执行结果没有 `baseline_ready`、`risk_score`、`tcm_score`。
- 缠绕在旧总分门槛中的完成逻辑允许缺失 baseline，并拒绝 `total_score=0` 但新分层条件已满足的状态。
- 字段冲突未形成显式 blocker。

### GREEN 1: 注册表和分层执行

实现注册表、独立归一化、显式 blockers 和旧字段迁移后运行同一命令。

结果：`Ran 19 tests in 0.003s`，`OK`。

### RED 2: 条件字段迁移回归

自审发现：不传 context 调用迁移函数时，已有 `not_applicable` 的 pregnancy 状态会被重开为 `not_asked`。先用脚本稳定复现：

```text
not_applicable -> not_asked
```

再加入回归测试并运行：

```powershell
python -m unittest backend.tests.test_intake_execution.IntakeExecutionTests.test_migration_without_context_preserves_not_applicable_fields -v
```

结果：按预期失败，断言得到 `not_asked != not_applicable`。

### GREEN 2: 保留无 context 的条件状态

迁移函数仅在明确提供 context 时重新判断已有 `not_applicable` 状态。运行同一回归测试：`Ran 1 test`，`OK`。

## Final Verification

Task 3 focused command：

```powershell
python -m unittest backend.tests.test_obesity_intake_schema backend.tests.test_intake_execution -v
```

结果：`Ran 20 tests in 0.002s`，`OK`。

Integration support command：

```powershell
python -m unittest backend.tests.test_intake_flow backend.tests.test_intake_question_policy -v
```

结果：`Ran 26 tests in 0.017s`，`OK`。

Full backend command：

```powershell
python -m unittest discover -s backend/tests -v
```

结果：`Ran 102 tests in 1.706s`，`OK`。

Syntax verification：

```powershell
python -m compileall -q backend
```

结果：exit code `0`，无输出。

## Changed Files

- `backend/obesity_intake_schema.py`: 增加 layer、指南风险字段和六个检查组，移除在线注册表中的 `metabolic_tests`。
- `backend/intake_execution.py`: 独立分层计分、新门槛、显式 blockers、冲突拦截和旧状态迁移。
- `backend/intake_flow.py`: baseline 确认值进入 context，确认后重算 execution；pregnancy 适用性跟随已验证生理性别。
- `backend/tests/test_obesity_intake_schema.py`: 字段覆盖、layer/source、section 兼容、舌象/脉象边界测试。
- `backend/tests/test_intake_execution.py`: baseline、分层门槛、旧总分解耦、冲突、旧检查状态迁移和条件状态回归测试。
- `backend/tests/test_intake_flow.py`: baseline context 的 `False -> True` 集成断言。
- `backend/tests/test_intake_question_policy.py`: 既有 Task 4 前置测试显式建立已确认 baseline，未修改问题策略生产代码。
- `.superpowers/sdd/task-3-report.md`: 本报告。

## Self-Review

- 注册表 key 唯一，所有字段均有非空问题、重试问题、source 和合法 layer。
- `height_weight` 标为 baseline layer；baseline 是否完成只取 `context["baseline_confirmed"]`，不由 AI 字段证据推断。
- `risk`、`tcm`、`safety` 当前原始权重和分别为 `46`、`40`、`25`；各层独立除以自身适用权重和，权重仅表示内部资料完整度，不是临床概率。
- 满确认状态实测输出：`baseline_ready=True`、三层分数均为 `100.0`、兼容 `differentiation_score=70.0`、`total_score=100.0`、`blocking_keys=[]`。
- risk/tcm/baseline 字段继续使用 `section="differentiation"`，safety 字段继续使用 `section="safety"`。
- 四个 hard-required 字段仍严格为 `red_flags`、`allergies`、`medications`、`important_history`；pregnancy 仍为条件字段。
- 舌象保持可选，在线字段中没有 pulse。
- 旧 `metabolic_tests` 不再出现在新注册表，但旧 session state 和旧提取更新不会 KeyError；其状态会兼容映射到六个检查组。
- `calculate_execution` 提供层级 blockers；`evaluate_threshold` 再合并硬性/优先字段和字段冲突 blockers，并去重。
- 未修改 Task 4 问题选择/离线策略生产代码、Skills、前端或医生视图。
- 当前目录不是 Git 仓库；未初始化、提交或执行 Git 工作流。

## Concerns

- 旧 `metabolic_tests` 是一个宽泛字段，无法恢复六类检查的历史细粒度边界；兼容迁移会将同一旧状态和证据复制到六个新组。这避免旧会话崩溃并保留完成度，但医生复核时仍应把这类迁移证据视为宽泛历史信息。
- `RULE_VERSION` 保留现有 `adult-obesity-intake-v1`，因为 Task 3 未要求版本迁移；若后续需要跨版本审计或并行规则解释，应在专门迁移任务中定义版本升级和旧记录回放策略。
- Task 4 的分层追问和离线继续采集未提前实现；本任务只提供其依赖的 layer、scores 和 blockers。

# Review Fix Wave

## Status

DONE

本节覆盖 Task 3 审查提出的一个 Critical 和五个 Important 问题，并取代上文关于“将旧 `metabolic_tests` 复制到六个新组”的早期兼容策略。旧宽泛资料现在只保留为 legacy audit 数据，不再产生新组证据或分数。

## Fixes Delivered

1. **Completion bypass**
   - 新增终止但未完整的 `phase="incomplete"`。
   - `patient_unavailable`、`duplicate_gap`、`no_collectable_gap`、`ai_unavailable` 的 `complete=False` 决策不再写成 `completed`。
   - incomplete 会话保留报告用于医生接续，但内部和患者 serializer 均返回 `is_complete=False`。
   - `complete_intake_session` 重新计算 execution 并调用 `evaluate_threshold`；只有完整门槛实际满足时才进入 `completed`。

2. **Optional unavailable denominator**
   - 非 hard、`priority > 5` 的字段只有在 `status="unavailable"` 且已达到 `max_attempts` 后，才从所属 layer denominator 排除。
   - hard/high-priority unavailable 继续留在 denominator，并继续成为 blocker。
   - 当一个 layer 的全部字段都因最终可选拒绝被排除、denominator 为 `0` 时，该 layer 的采集完整度按 `100.0` 处理，避免可选拒绝造成永久死锁。

3. **Legacy metabolic migration**
   - `metabolic_tests` 保留在旧 key 下，不再复制到六个新字段。
   - 六个新检查组迁移时初始化为独立 `not_asked`，无重复 evidence、无 fallback points。
   - 旧 key 的后续兼容更新仍只写回旧 key，不会扇出到新字段。
   - doctor summary 通过 `legacy_fields["metabolic_tests"]` 暴露旧状态、证据、冲突和 audit，未修改医生前端面板。

4. **Conflict resolution**
   - 新冲突记录包含 `resolved=False`。
   - 后续明确的 confirmed、nonconflicting 更新会保留冲突历史，并写入 `resolved=True` 和 `resolved_turn`。
   - `evaluate_threshold` 只阻塞未解决冲突；没有 `resolved` 的旧冲突仍按未解决处理。

5. **Pregnancy reactivation**
   - 从 `not_applicable` 恢复为 applicable 时不再替换整个字段状态。
   - evidence/conflicts/audit/attempts 原样保留；有历史资料时恢复为 `partial`，无历史资料时恢复为 `not_asked`。

6. **Resident session migration**
   - `IntakeSessionStore.get` 成为 resident session 的访问边界 normalization。
   - context 缺少 `baseline_confirmed` 时从现有顶层 flag 同步，随后迁移 field states 并重算 execution。
   - 迁移幂等，不重置 `current_question`、`current_field_key`、`attempt_number` 或 `follow_up_answers`。
   - 历史上被错误标为 `completed` 的 protective stop resident session 会修正为 `incomplete`。

## RED Evidence

### RED Wave 1: Six Reviewer Findings

写入 execution、flow 和 serializer 回归测试后运行：

```powershell
python -m unittest backend.tests.test_intake_execution backend.tests.test_intake_flow backend.tests.test_intake_views -v
```

结果：`Ran 41 tests`，`9 failures, 1 error`。失败点与审查项一致：

- resolved conflict 仍阻塞。
- legacy metabolic 状态仍复制为六个 confirmed 字段。
- 最终可选 unavailable 字段仍保留在 TCM denominator。
- pregnancy reactivation 丢失历史并回到 `not_asked`。
- 四种 `complete=False` stop reason 全部错误进入 `completed`。
- manual completion 在未达门槛时仍进入 `completed`。
- resident session 缺少 access-boundary context migration，读取 `context["baseline_confirmed"]` 抛出 `KeyError`。

### RED Wave 2: Resident Completion and Legacy Audit Visibility

```powershell
python -m unittest backend.tests.test_intake_flow.IntakeFlowTests.test_old_resident_incomplete_stop_is_not_left_completed backend.tests.test_intake_views.IntakeViewTests.test_doctor_summary_preserves_legacy_metabolic_state_for_audit -v
```

结果：`Ran 2 tests`，`1 failure, 1 error`：旧 protective stop 仍为 `completed`，doctor summary 缺少 `legacy_fields`。

### RED Wave 3: Zero Optional Denominator

```powershell
python -m unittest backend.tests.test_intake_execution.IntakeExecutionTests.test_fully_retried_optional_only_layer_with_zero_denominator_is_complete -v
```

结果：`Ran 1 test`，按预期失败，`tcm_score` 为 `0.0` 而不是 `100.0`。

## GREEN Evidence

Review-focused command：

```powershell
python -m unittest backend.tests.test_intake_execution backend.tests.test_intake_flow backend.tests.test_intake_views -v
```

结果：`Ran 44 tests in 0.044s`，`OK`。

Full backend command：

```powershell
python -m unittest discover -s backend/tests -v
```

结果：`Ran 114 tests in 1.940s`，`OK`。

Syntax command：

```powershell
python -m compileall -q backend
```

结果：exit code `0`，无输出。

## Review-Fix Files

- `backend/intake_execution.py`: optional denominator、zero-denominator、legacy isolation、conflict resolution、pregnancy history-preserving reactivation。
- `backend/intake_flow.py`: resident normalization、threshold-gated completion、protective incomplete phase 和报告保留。
- `backend/intake_views.py`: incomplete patient serialization、manual incomplete 文案和 legacy audit backend summary。
- `backend/tests/test_intake_execution.py`: findings 2-5 和 zero-denominator 回归。
- `backend/tests/test_intake_flow.py`: 四种 stop bypass、manual bypass、resident migration/idempotence 回归。
- `backend/tests/test_intake_views.py`: patient incomplete serializer 和 legacy audit visibility 回归。
- `.superpowers/sdd/task-3-report.md`: 本 review fix wave。

## Review-Fix Self-Review

- `evaluate_threshold` 仍只使用 baseline/risk/tcm/safety 门槛及 blockers，未恢复旧 total/differentiation gate。
- legacy `total_score` 和 `differentiation_score` 仍只作为 informational compatibility outputs。
- incomplete 终止不会清空已收集证据、回答、报告、推荐检查或 audit。
- optional unavailable 只有完成允许的两次追问后才退出 denominator；首次 unavailable 仍影响完整度。
- hard/high-priority unavailable 的 denominator 与 blocker 行为均有回归测试。
- resident normalization 每次访问可重复执行，第二次结果与第一次一致，活动中的问题和回答不变。
- 未修改 `intake_question_policy.py`、Skills、前端或医生面板，也未开始 Task 4。
- 当前目录不是 Git 仓库；未初始化或提交。

## Review-Fix Concerns

无已知阻塞问题。`RULE_VERSION` 仍保留既有 `adult-obesity-intake-v1`；版本升级和持久化记录回放不在本 review fix wave 范围内。

# Second Review Fix Wave

## Status

DONE

本轮按第二次复审的四项 Important 发现补齐旧驻留会话、患者端 incomplete 阶段和保存接口的端到端完整性。未进入 Task 4，也未扩展基线表单、Skills、追问选择或医生面板。

## Fixes Delivered

1. **Legacy manual completion normalization**
   - 驻留会话每次通过访问边界读取时，都会以迁移后的字段状态和当前 context 重新计算 execution，并调用当前 `evaluate_threshold`。
   - 旧 `phase="completed"`、`stop_reason="manual_completion"` 会话若不再满足当前门槛，会降级为 `phase="incomplete"`、`stop_reason="manual_incomplete"`；患者序列化不会把它标记为完整。
   - 当前门槛仍满足时保留 `completed/manual_completion`，避免误降级。
2. **Resident pregnancy applicability**
   - 在字段迁移和 execution 重算之前，从旧会话已验证 baseline 的 `sex` 推导 `context["pregnancy_applicable"]`：female 为 true，male 为 false。
   - 男性旧会话会将妊娠字段恢复为不适用；重复访问结果幂等，既有 evidence、conflicts 和 audit 不被清空。
3. **Frontend incomplete terminal stage**
   - `getIntakeViewStage` 将 `phase="incomplete"` 映射到 `result`，不再落入 analyzing。
   - 患者结果页显示“资料待补充 / 本次诊前资料尚未完整”，进度条将 incomplete 作为保护性终态。
   - `canSaveIntakeRecord` 对 incomplete 继续返回 false；未增加新表单或重做界面。
4. **Save API integrity**
   - `/api/save_record` 只依据服务端驻留会话状态判断，不信任客户端提交内容。
   - 保存前重新执行 access-boundary normalization 和 `evaluate_threshold`；phase 非 completed 或当前门槛不通过均返回 HTTP 400：`当前资料尚未达到完整条件，暂不能保存，请由医生继续补充确认。`
   - 真正达到当前完整度门槛的 completed 会话仍可保存。

## RED Evidence

后端新回归写入后运行：

```powershell
python -m unittest backend.tests.test_intake_flow backend.tests.test_skill_analysis.ApiIntegrationTests -v
```

结果：`Ran 35 tests`，`FAILED (failures=4)`。失败分别证明：旧男性会话未覆盖错误的 pregnancy applicability、旧 manual completion 未按当前门槛降级、incomplete 会话仍可保存、伪造 completed 但未过门槛的会话仍可保存。两个正向保护测试（门槛通过的旧 manual completion 与 completed 保存）在 RED 阶段保持通过。

前端新回归写入后运行：

```powershell
npm.cmd test
```

结果：`18 tests`，`16 pass, 2 fail`。失败分别证明 incomplete 被映射为 `analyzing`，以及结果模板/进度未将 incomplete 表示为保护性终态。直接使用 `npm test` 曾被本机 PowerShell execution policy 拦截，因此所有有效前端证据均使用同一 Node/npm 安装下的 `npm.cmd`。

## GREEN Evidence

后端 review-focused：

```powershell
python -m unittest backend.tests.test_intake_flow backend.tests.test_skill_analysis.ApiIntegrationTests -v
```

结果：`Ran 35 tests`，`OK`。

前端 review-focused：

```powershell
node --test tests/follow-up-stage.test.mjs tests/patient-visibility.test.mjs
```

结果：`15 tests`，`15 pass, 0 fail`。

完整后端套件：

```powershell
python -m unittest discover -s backend/tests -v
```

结果：`Ran 120 tests in 1.847s`，`OK`。

完整前端套件：

```powershell
npm.cmd test
```

结果：`18 tests`，`18 pass, 0 fail`。

前端生产构建：

```powershell
npm.cmd run build
```

结果：Vite 转换 `89 modules`，`built in 1.87s`，exit code `0`。

后端语法验证：

```powershell
python -m compileall -q backend
```

结果：exit code `0`，无输出。

## Files Changed

- `backend/intake_flow.py`: 旧 manual completion 当前门槛复核，以及 baseline sex 驱动的 pregnancy applicability 归一化。
- `backend/main.py`: `/api/save_record` 服务端 phase 与当前 threshold 双重校验及患者安全 HTTP 400 文案。
- `backend/tests/test_intake_flow.py`: manual completion 降级/保留、男性旧会话妊娠适用性、幂等与历史保留回归。
- `backend/tests/test_skill_analysis.py`: incomplete、伪 completed 未过门槛、真实 completed 已过门槛三条保存 API 回归。
- `frontend/src/follow-up-stage.js`: incomplete 到 result 的阶段映射，保存资格保持 false。
- `frontend/src/App.vue`: incomplete 保护性结果文案和终态进度显示。
- `frontend/tests/follow-up-stage.test.mjs`: incomplete view stage 和 canSave 回归。
- `frontend/tests/patient-visibility.test.mjs`: incomplete 结果文案与进度回归。
- `.superpowers/sdd/task-3-report.md`: 本节 RED/GREEN、文件和自审记录。

## Self-Review

- resident normalization 的顺序为 baseline context 同步、pregnancy applicability 推导、字段迁移、execution 重算、threshold 评估，满足迁移前推导要求。
- normalization 不写入当前问题、当前字段、尝试次数或问答历史；重复访问测试确认状态幂等且 evidence/conflicts/audit 保留。
- 保存接口不读取客户端提供的 phase、scores 或 completion 声明；保存文件函数在拒绝路径中未被调用。
- threshold 判断仍只使用 baseline/risk/tcm/safety 和未解决 blockers；legacy `total_score`、`differentiation_score` 保持 informational only。
- incomplete 在患者端是可查看报告的保护性终态，但 `canSave` 为 false，服务端也独立拒绝保存。
- 未修改 `intake_question_policy.py`、Skills、Task 6 baseline form 或 doctor panel；未开始 Task 4。
- 目录无 Git 仓库，本轮未初始化或提交。

## Concerns

无已知功能阻塞。开发机 PowerShell 禁止直接执行 `npm.ps1`，因此验证命令使用 `npm.cmd`；这不影响 Node 测试或 Vite 生产构建结果。

# Final Review Fix Wave

## Status

DONE

本轮严格限于 Task 3 最终复审的两个 Important 问题：旧 resident 完成态的当前门槛复核，以及 escalated 前端保存资格与后端 `/api/save_record` 的一致性。未实现 Task 4。

## Fixes Delivered

1. **Stale resident completion recheck**
   - resident session 每次访问仍先迁移字段、重算 execution 并调用当前 `evaluate_threshold`。
   - 所有旧 `phase="completed"` 会话只要不满足当前分层门槛，都会降级为 `phase="incomplete"`；不再仅覆盖 `manual_completion`。
   - `manual_completion` 继续映射为 `manual_incomplete`；旧 `threshold_reached` 或其他普通完成原因映射为 `threshold_recheck_incomplete`，患者文案明确资料未满足现行完整条件且可继续补充。
   - 原有 protective stop reason 仍保留专用原因与患者文案，但不会被序列化为完成。
2. **Escalated save eligibility**
   - `canSaveIntakeRecord` 现在只允许 `phase="completed"`。
   - `escalated` 继续进入线下就医提示视图，但保存按钮保持禁用，与后端只接受 completed 且门槛通过的规则一致。

## RED Evidence

后端序列化回归写入后运行：

```powershell
python -m unittest backend.tests.test_intake_views.IntakeViewTests.test_stale_threshold_reached_resident_is_serialized_as_incomplete -v
```

结果：`Ran 1 test`，`FAILED (failures=1)`；实际 `phase` 为 `completed`，预期为 `incomplete`，准确复现旧 `threshold_reached` 绕过当前分层门槛的问题。

前端保存资格回归更新后运行：

```powershell
node --test --test-name-pattern="只有完整结束阶段可以保存档案" tests/follow-up-stage.test.mjs
```

结果：`1 test`，`0 pass, 1 fail`；`escalated` 实际返回 true，预期 false。

## GREEN Evidence

最小后端 GREEN（包含 stale threshold 序列化及 manual completion 正反向保护）：

```powershell
python -m unittest backend.tests.test_intake_views.IntakeViewTests.test_stale_threshold_reached_resident_is_serialized_as_incomplete backend.tests.test_intake_flow.IntakeFlowTests.test_old_manual_completion_below_current_gate_is_downgraded backend.tests.test_intake_flow.IntakeFlowTests.test_old_manual_completion_meeting_current_gate_stays_completed -v
```

结果：`Ran 3 tests`，`OK`。

最小前端 GREEN：

```powershell
node --test --test-name-pattern="只有完整结束阶段可以保存档案" tests/follow-up-stage.test.mjs
```

结果：`1 test`，`1 pass, 0 fail`。

相关后端套件：

```powershell
python -m unittest backend.tests.test_intake_flow backend.tests.test_intake_views -v
```

结果：`Ran 31 tests in 0.055s`，`OK`。

相关前端套件：

```powershell
node --test tests/follow-up-stage.test.mjs
```

结果：`6 tests`，`6 pass, 0 fail`。

完整后端套件：

```powershell
python -m unittest discover -s backend/tests -v
```

结果：`Ran 121 tests in 1.821s`，`OK`。

完整前端套件：

```powershell
npm.cmd test
```

结果：`18 tests`，`18 pass, 0 fail`。

前端生产构建：

```powershell
npm.cmd run build
```

结果：Vite 转换 `89 modules`，`built in 1.18s`，exit code `0`。

后端语法检查：

```powershell
python -m compileall -q backend
```

结果：exit code `0`，无输出。

## Files Changed

- `backend/intake_flow.py`: 将当前 threshold 复核扩展到所有旧 completed resident sessions。
- `backend/intake_views.py`: 新增 stale threshold 降级后的患者安全文案。
- `backend/tests/test_intake_views.py`: 新增 resident 访问归一化到患者序列化的端到端回归。
- `frontend/src/follow-up-stage.js`: 保存资格收紧为仅 completed。
- `frontend/tests/follow-up-stage.test.mjs`: escalated 不可保存回归。
- `.superpowers/sdd/task-3-report.md`: 本轮 RED/GREEN 与自审记录。

## Self-Review

- 当前 completion gate 仍只由 `evaluate_threshold` 的 baseline/risk/tcm/safety 门槛和 unresolved blockers 决定；legacy total/differentiation outputs 未参与判断。
- 达到当前门槛的旧 completed 会话不受影响；既有 manual completion 通过门槛测试保持 GREEN。
- 降级只更新 phase 和面向患者的 stop reason，不清空 report、evidence、conflicts、audit、answers 或 active question 数据。
- 患者序列化回归同时验证 `phase="incomplete"`、`is_complete=false`，并防止继续显示“已整理完成”的过时文案。
- escalated 的页面阶段和线下就医提示保持不变，仅 `canSave` 变为 false；后端保存校验未放宽。
- 未修改追问选择、Skills、baseline form 或 doctor panel；未开始 Task 4。
- 当前目录无 Git 仓库，本轮未初始化或提交。

## Concerns

无已知阻塞问题。
