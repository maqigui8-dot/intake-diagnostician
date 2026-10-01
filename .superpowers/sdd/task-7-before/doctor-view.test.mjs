import test from 'node:test'
import assert from 'node:assert/strict'

import { formatStopReason, isDoctorView, scoreTone } from '../src/doctor-view.js'

test('只有明确 doctor 参数才进入医生视图', () => {
  assert.equal(isDoctorView('?view=doctor'), true)
  assert.equal(isDoctorView('?session=abc'), false)
})

test('停止原因转换为医生可理解中文', () => {
  assert.equal(formatStopReason('threshold_reached'), '已达到正常完成门槛')
  assert.equal(formatStopReason('safety_limit'), '历史问诊保护性结束')
  assert.equal(formatStopReason(null), '问诊进行中')
})

test('分数颜色按门槛稳定分类', () => {
  assert.equal(scoreTone(90, 85), 'good')
  assert.equal(scoreTone(70, 85), 'warning')
  assert.equal(scoreTone(40, 85), 'low')
})
