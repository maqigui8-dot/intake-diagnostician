import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const appPath = fileURLToPath(new URL('../src/App.vue', import.meta.url))
const appSource = readFileSync(appPath, 'utf8')
const template = appSource.split('<script setup>')[0]
const styleSource = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8')

test('Enter sends while Shift+Enter keeps a newline', () => {
  assert.match(template, /@keydown\.enter="handleOpenEnter"/)
  assert.match(template, /@keydown\.enter="handleFollowUpEnter"/)
  assert.match(appSource, /event\.isComposing/)
  assert.match(appSource, /event\.shiftKey/)
  assert.match(template, /按 Enter 发送，Shift \+ Enter 换行/)
})

test('患者首屏使用开放式文本回答而不是固定十题', () => {
  assert.match(template, /state\.open_question/)
  assert.match(template, /submitOpenAnswer/)
  assert.doesNotMatch(template, /问题 \{\{ currentNumber \}\} \/ \{\{ progress\.total \}\}/)
  assert.doesNotMatch(template, /option-list/)
})

test('患者模板提供独立的对话式追问区域', () => {
  assert.match(template, /data-testid="follow-up-chat"/)
  assert.match(template, /state\.next_question/)
})

test('整理和追问阶段都保留完整的可滚动问答历史', () => {
  const analyzing = template.match(/viewStage === 'analyzing'[\s\S]*?(?=<section v-else-if="state && viewStage === 'follow_up_chat')/)?.[0] || ''
  const followUp = template.match(/viewStage === 'follow_up_chat'[\s\S]*?(?=<section v-else-if="state && viewStage === 'escalated')/)?.[0] || ''

  for (const section of [analyzing, followUp]) {
    assert.match(section, /ref="messageList"/)
    assert.match(section, /state\.open_answer/)
    assert.match(section, /state\.follow_up_answers/)
  }
  assert.match(styleSource, /\.message-list\s*\{[^}]*max-height:\s*520px[^}]*overflow-y:\s*auto/s)
})

test('危险信号在整理追问和结果阶段持续提示但不中断流程', () => {
  const analyzing = template.match(/viewStage === 'analyzing'[\s\S]*?(?=<section v-else-if="state && viewStage === 'follow_up_chat')/)?.[0] || ''
  const followUp = template.match(/viewStage === 'follow_up_chat'[\s\S]*?(?=<section v-else-if="state && viewStage === 'escalated')/)?.[0] || ''
  const result = template.match(/viewStage === 'result'[\s\S]*?(?=<p class="disclaimer")/)?.[0] || ''

  for (const section of [analyzing, followUp, result]) {
    assert.match(section, /state\.safety_alerts/)
    assert.match(section, /仍可继续填写诊前资料/)
  }
  assert.match(result, /存在需要优先线下评估的情况，暂不提供常规检查建议/)
})

test('患者模板不展示内部执行度与缺口', () => {
  for (const phrase of ['信息完整度', '缺失必问项', '建议选问项', '辨证资料执行度', '开方安全执行度']) {
    assert.doesNotMatch(template, new RegExp(`>${phrase}<`))
  }
})

test('危险信号、档案和检查建议均有独立结果状态', () => {
  assert.match(template, /viewStage === 'escalated'/)
  assert.match(template, /推荐检查项目/)
  assert.match(template, /state\.report_markdown/)
})

test('未完整阶段显示保护性结果并进入档案进度', () => {
  const result = template.match(/viewStage === 'result'[\s\S]*?(?=<p class="disclaimer")/)?.[0] || ''
  assert.match(result, /state\.phase === 'incomplete'/)
  assert.match(result, /诊前资料尚未完整/)
  assert.match(appSource, /\['completed', 'incomplete', 'escalated'\]/)
})

test('手机端布局使用单列且文本框不会溢出', () => {
  assert.match(styleSource, /@media \(max-width: 860px\)/)
  assert.match(styleSource, /grid-template-columns:\s*1fr/)
  assert.match(styleSource, /max-width:\s*100%/)
})
