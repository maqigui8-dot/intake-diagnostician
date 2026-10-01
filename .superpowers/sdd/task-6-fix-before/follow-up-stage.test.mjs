import test from 'node:test'
import assert from 'node:assert/strict'

import { canSaveIntakeRecord, getIntakeViewStage } from '../src/follow-up-stage.js'

test('新会话进入开放描述阶段', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'open_intake' } }), 'open_intake')
})

test('开放回答后进入整理阶段', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'processing' } }), 'analyzing')
  assert.equal(getIntakeViewStage({ state: { phase: 'follow_up' }, saving: true }), 'analyzing')
})

test('后台给出下一问时进入对话阶段', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'follow_up', next_question: '最近有胸痛吗？' } }), 'follow_up_chat')
})

test('正常和保护性结束都进入结果阶段', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'completed' } }), 'result')
  assert.equal(getIntakeViewStage({ state: { phase: 'incomplete' } }), 'result')
})

test('危险信号结束进入线下就医提示', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'escalated' } }), 'escalated')
})

test('新会话首先进入基础资料收集阶段', () => {
  assert.equal(getIntakeViewStage({ state: { phase: 'baseline_collection' } }), 'baseline_collection')
})

test('只有完整结束阶段可以保存档案', () => {
  assert.equal(canSaveIntakeRecord({ state: { phase: 'completed' } }), true)
  assert.equal(canSaveIntakeRecord({ state: { phase: 'escalated' } }), false)
  assert.equal(canSaveIntakeRecord({ state: { phase: 'incomplete' } }), false)
  assert.equal(canSaveIntakeRecord({ state: { phase: 'follow_up' } }), false)
  assert.equal(canSaveIntakeRecord({ state: { phase: 'completed' }, saving: true }), false)
})
