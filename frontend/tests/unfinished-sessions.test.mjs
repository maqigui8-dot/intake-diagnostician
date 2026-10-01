import test from 'node:test'
import assert from 'node:assert/strict'

import { buildSessionUrl, visibleUnfinishedSessions } from '../src/unfinished-sessions.js'


test('当前问诊不会在继续问诊列表中重复显示', () => {
  const items = [
    { session_id: 'current', primary_concern: '当前' },
    { session_id: 'other', primary_concern: '其他' },
  ]

  assert.deepEqual(visibleUnfinishedSessions(items, 'current'), [items[1]])
})

test('切换问诊只替换 session 参数并保留其他查询参数', () => {
  const result = buildSessionUrl('http://127.0.0.1:5173/?mode=patient&session=old', 'new id')
  const url = new URL(result)

  assert.equal(url.searchParams.get('mode'), 'patient')
  assert.equal(url.searchParams.get('session'), 'new id')
})
