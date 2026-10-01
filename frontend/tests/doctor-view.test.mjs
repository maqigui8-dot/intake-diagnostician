import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

import { formatStopReason, isDoctorView, scoreTone } from '../src/doctor-view.js'

const panelPath = new URL('../src/components/DoctorExecutionPanel.vue', import.meta.url)
const panelSource = readFileSync(panelPath, 'utf8')
const decisionSource = readFileSync(new URL('../src/components/DecisionExplanationPanel.vue', import.meta.url), 'utf8')

test('只有明确 doctor 参数才进入医生视图', () => {
  assert.equal(isDoctorView('?view=doctor'), true)
  assert.equal(isDoctorView('?session=abc'), false)
})

test('停止原因转换为医生可理解中文', () => {
  assert.equal(formatStopReason('core_information_ready'), '核心资料已就绪')
  assert.equal(formatStopReason('threshold_reached'), '历史规则结束，需核对资料就绪度')
  assert.equal(formatStopReason('manual_incomplete'), '资料未就绪，已保存供医生补充')
  assert.equal(formatStopReason('safety_limit'), '历史问诊保护性结束')
  assert.equal(formatStopReason(null), '问诊进行中')
})

test('分数颜色按门槛稳定分类', () => {
  assert.equal(scoreTone(90, 85), 'good')
  assert.equal(scoreTone(70, 85), 'warning')
  assert.equal(scoreTone(40, 85), 'low')
})

test('医生视图包含六个分层档案区块标题', () => {
  const headings = [
    '基础测量与肥胖范围',
    '肥胖病程与可能病因',
    '相关疾病风险',
    '生活方式与心理情况',
    '中医诊前资料',
    '待医生确认',
  ]
  for (const heading of headings) {
    assert.ok(panelSource.includes(heading), `缺少区块标题：${heading}`)
  }
})

test('医生视图渲染基线评估、分层资料覆盖度与检查候选', () => {
  assert.match(panelSource, /baseline_assessment/)
  assert.match(panelSource, /layer_execution/)
  assert.match(panelSource, /recommended_exams/)
  assert.match(panelSource, /分层资料覆盖度/)
  assert.match(panelSource, /覆盖度不单独决定是否结束追问/)
  assert.match(decisionSource, /诊前资料就绪度/)
  assert.match(decisionSource, /readiness_summary/)
})

test('旧版医生档案页也显示统一的就绪度数据', () => {
  assert.match(panelSource, /readiness_summary/)
  assert.match(panelSource, /核心诊前资料/)
  assert.match(panelSource, /核心未解决冲突/)
})

test('医生视图渲染检查候选的触发、来源、优先级与注意事项', () => {
  assert.match(panelSource, /exam\.trigger/)
  assert.match(panelSource, /exam\.source/)
  assert.match(panelSource, /exam\.priority/)
  assert.match(panelSource, /exam\.precautions/)
})
