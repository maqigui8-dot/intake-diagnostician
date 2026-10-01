import test from 'node:test'
import assert from 'node:assert/strict'

import {
  SIDEBAR_STORAGE_KEY,
  readSidebarCollapsed,
  writeSidebarCollapsed,
} from '../src/sidebar-state.js'


test('读取保存的折叠状态且存储失败时安全回退', () => {
  assert.equal(readSidebarCollapsed({ getItem: () => 'true' }), true)
  assert.equal(readSidebarCollapsed({ getItem: () => 'false' }), false)
  assert.equal(readSidebarCollapsed({ getItem: () => null }), false)
  assert.equal(readSidebarCollapsed({ getItem: () => { throw new Error('blocked') } }), false)
})

test('写入折叠状态使用稳定键和值且存储失败不抛错', () => {
  const writes = []
  writeSidebarCollapsed({ setItem: (...args) => writes.push(args) }, true)
  writeSidebarCollapsed({ setItem: (...args) => writes.push(args) }, false)

  assert.deepEqual(writes, [
    [SIDEBAR_STORAGE_KEY, 'true'],
    [SIDEBAR_STORAGE_KEY, 'false'],
  ])
  assert.doesNotThrow(() => writeSidebarCollapsed({ setItem: () => { throw new Error('blocked') } }, true))
})
