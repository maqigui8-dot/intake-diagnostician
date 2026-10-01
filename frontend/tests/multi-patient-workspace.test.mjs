import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const root = fs.readFileSync(new URL('../src/RootApp.vue', import.meta.url), 'utf8')
const identity = fs.readFileSync(new URL('../src/components/IdentityChooser.vue', import.meta.url), 'utf8')
const patientApp = fs.readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const patientContext = await import('../src/patient-context.js')

test('入口按显式身份分流且患者 URL 保留身份', () => {
  assert.equal(patientContext.readPatientId('?patient=patient-ma'), 'patient-ma')
  assert.equal(patientContext.patientUrl('patient-li'), '/?patient=patient-li')
  assert.match(root, /<App v-if="patientId"/)
  assert.match(root, /<IdentityChooser v-else/)
})

test('患者入口不再提供医生端，旧医生参数也不会进入患者会话', () => {
  assert.doesNotMatch(root, /DoctorWorkspace/)
  assert.doesNotMatch(identity, /doctorUrl|进入医生工作台/)
  assert.equal(patientContext.readPatientEntryId('?view=doctor&patient=patient-ma'), '')
  assert.equal(patientContext.readPatientEntryId('?patient=patient-ma'), 'patient-ma')
})

test('患者问诊页展示关键资料进度', () => {
  assert.match(patientApp, /state\.progress\.core_completed/)
  assert.match(patientApp, /state\.progress\.core_total/)
  assert.match(patientApp, /state\.progress\.remaining_count/)
  assert.match(patientApp, /第 \{\{ currentRound \}\} 问 · 已确认/)
})
