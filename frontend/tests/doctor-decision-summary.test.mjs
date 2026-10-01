import test from 'node:test'
import assert from 'node:assert/strict'

import { buildDoctorDecisionSummary } from '../src/doctor-decision-summary.js'

test('把已确认字段汇总为已覆盖线索', () => {
  const result = buildDoctorDecisionSummary({
    '肥胖病程与可能病因': [
      { field_key: 'onset_course', group: '起病经过与相关因素', status: 'confirmed', evidence: ['一年'] },
    ],
    '中医诊前资料': [
      { field_key: 'stool_urine', group: '中医症状资料', status: 'confirmed', evidence: ['无明显变化'] },
    ],
  })

  assert.deepEqual(result.covered, [
    { title: '病程与风险', detail: '持续时间' },
    { title: '中医诊前', detail: '大便与小便' },
  ])
})

test('把未确认选填字段转换成中文诊中补充项并去重', () => {
  const result = buildDoctorDecisionSummary({
    '中医诊前资料': [
      { field_key: 'cold_heat_sweat', group: '中医症状资料', status: 'not_asked', evidence: [] },
      { field_key: 'tongue', group: '舌象', status: 'not_asked', evidence: [] },
      { field_key: 'tongue', group: '舌象', status: 'partial', evidence: [] },
    ],
  }, ['cold_heat_sweat', 'tongue'])

  assert.deepEqual(result.pending, ['寒热与出汗', '舌象'])
})

test('缺少字段中文名时使用资料类别而不展示 field_key', () => {
  const result = buildDoctorDecisionSummary({
    '未知资料': [
      { field_key: 'internal_only_key', group: '其他症状资料', status: 'unavailable', evidence: [] },
    ],
  }, ['internal_only_key'])

  assert.deepEqual(result.pending, ['其他资料'])
  assert.equal(result.pending.some((item) => item.includes('internal_only_key')), false)
})

test('只有后端列出的选填字段才进入诊中补充项', () => {
  const result = buildDoctorDecisionSummary({
    '安全资料': [
      { field_key: 'red_flags', group: '危险信号', status: 'not_asked', evidence: [] },
      { field_key: 'tongue', group: '舌象', status: 'not_asked', evidence: [] },
    ],
  }, ['tongue'])

  assert.deepEqual(result.pending, ['舌象'])
})

test('同一资料类别中已确认和待补充字段使用字段级名称，互不冲突', () => {
  const result = buildDoctorDecisionSummary({
    '中医诊前资料': [
      { field_key: 'appetite_thirst', group: '中医症状资料', status: 'confirmed', evidence: ['食欲增加'] },
      { field_key: 'cold_heat_sweat', group: '中医症状资料', status: 'not_asked', evidence: [] },
    ],
  }, ['cold_heat_sweat'])

  assert.deepEqual(result.covered, [{ title: '中医诊前', detail: '食欲与口渴' }])
  assert.deepEqual(result.pending, ['寒热与出汗'])
})

test('后端未列为待补充的字段不会在前端自行推断', () => {
  const result = buildDoctorDecisionSummary({
    '中医诊前资料': [{ field_key: 'tongue', group: '舌象', status: 'not_asked', evidence: [] }],
  }, [])

  assert.deepEqual(result.pending, [])
})
