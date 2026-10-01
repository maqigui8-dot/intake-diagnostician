import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const appPath = fileURLToPath(new URL('../src/App.vue', import.meta.url))
const appSource = readFileSync(appPath, 'utf8')
const template = appSource.split('<script setup>')[0]
const styleSource = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8')
const indexSource = readFileSync(new URL('../index.html', import.meta.url), 'utf8')

test('Enter sends while Shift+Enter keeps a newline', () => {
  assert.match(template, /@keydown\.enter="handleOpenEnter"/)
  assert.match(template, /@keydown\.enter="handleFollowUpEnter"/)
  assert.match(appSource, /event\.isComposing/)
  assert.match(appSource, /event\.shiftKey/)
  assert.match(template, /按 Enter 发送，Shift \+ Enter 换行/)
})

test('患者端采用紧凑侧栏、渐进式基础资料与固定聊天输入区', () => {
  assert.match(template, /class="sidebar-primary-action"/)
  assert.match(template, /class="[^"]*chat-workbench[^"]*"/)
  assert.match(styleSource, /\.left-panel\s*\{[^}]*position:\s*fixed[^}]*height:\s*100vh/s)
  assert.match(styleSource, /\.chat-composer\s*\{[^}]*position:\s*sticky/s)
})

test('患者端入口不使用全局书法字体', () => {
  assert.doesNotMatch(indexSource, /font-serif/)
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

test('完成后展示核对与纠错而不是自动保存', () => {
  assert.match(template, /请核对以下关键资料/)
  assert.match(template, /review_fields/)
  assert.match(template, /submitPatientCorrection/)
  assert.match(appSource, /确认并保存档案/)
  assert.doesNotMatch(appSource, /watch\(\[\(\) => state\.value\?\.phase, saving\]/)
  assert.match(appSource, /\$\{sessionBase\.value\}\/save/)
  assert.doesNotMatch(appSource, /request\('\/api\/save_record'/)
})

test('结果页用已确认、待确认、暂无法确认解释资料进度', () => {
  const result = template.match(/viewStage === 'result'[\s\S]*?(?=<p class="disclaimer")/)?.[0] || ''
  assert.match(result, /已确认/)
  assert.match(result, /待确认/)
  assert.match(result, /暂无法确认/)
  assert.match(result, /state\.progress\.pending_count/)
  assert.match(result, /state\.progress\.unavailable_count/)
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

test('患者模板展示基础资料输入（年龄/性别/身高/体重/腰围/臀围/测量日期）', () => {
  assert.match(template, /baseline\.age/)
  assert.match(template, /baseline\.sex/)
  assert.match(template, /baseline\.height_cm/)
  assert.match(template, /baseline\.weight_kg/)
  assert.match(template, /baseline\.waist_cm/)
  assert.match(template, /baseline\.hip_cm/)
  assert.match(template, /baseline\.measured_at/)
})

test('患者模板不出现确诊肥胖症表述', () => {
  assert.doesNotMatch(template, /确诊/)
  assert.doesNotMatch(template, /肥胖症/)
})

test('结果区展示 BMI 与医生确认文案', () => {
  const result = template.match(/viewStage === 'result'[\s\S]*?(?=<p class="disclaimer")/)?.[0] || ''
  assert.match(result, /state\.bmi_assessment\.bmi/)
  assert.match(result, /state\.bmi_assessment\.diagnosis_copy/)
  assert.match(result, /达到成人肥胖范围，待医生确认/)
})

test('基础资料提交后仍可编辑（编辑入口 + editingBaseline 可达）', () => {
  assert.match(template, /编辑基础资料/)
  assert.match(template, /viewStage === 'baseline_collection' \|\| editingBaseline/)
  assert.match(appSource, /function startEditBaseline/)
  assert.match(appSource, /function cancelEditBaseline/)
  assert.match(appSource, /editingBaseline\.value = false/)
  assert.match(appSource, /function fillBaselineForm/)
})

test('基础资料校验与后端规则一致（年龄整数18–120、腰臀围大于0）', () => {
  assert.match(appSource, /Number\.isInteger\(age\)\s*&&\s*age >= 18\s*&&\s*age <= 120/)
  assert.match(appSource, /Number\.isFinite\(height\)\s*&&\s*height >= 100\s*&&\s*height <= 250/)
  assert.match(appSource, /Number\.isFinite\(weight\)\s*&&\s*weight >= 20\s*&&\s*weight <= 500/)
  assert.match(appSource, /optionalPositive\(waist\)\s*&&\s*optionalPositive\(hip\)/)
  assert.match(appSource, /Number\.isFinite\(value\)\s*&&\s*value > 0/)
})

test('流程进度为基础资料阶段给出正确状态', () => {
  assert.match(appSource, /phase === 'baseline_collection' \? 'current' : 'completed'/)
  assert.match(appSource, /phase === 'baseline_collection' \? 'pending'/)
})

test('患者侧栏仅接入自己的问诊历史，并通过患者专用接口回看档案', () => {
  assert.match(template, /我的问诊记录/)
  assert.match(template, /historyRecords/)
  assert.match(template, /historyDetail/)
  assert.match(appSource, /function loadHistory/)
  assert.match(appSource, /function openHistory/)
  assert.match(appSource, /\/api\/patients\/\$\{props\.patientId\}\/records/)
  assert.doesNotMatch(template, /医生摘要/)
})

test('患者侧栏区分继续问诊和已完成档案并支持软归档', () => {
  assert.match(template, />继续问诊</)
  assert.match(template, />已完成档案</)
  assert.match(template, /visibleUnfinished/)
  assert.match(template, /@click\.stop="archiveUnfinished/)
  assert.match(appSource, /\/api\/patients\/\$\{props\.patientId\}\/sessions\/unfinished/)
  assert.match(appSource, /\/archive`/)
  assert.match(appSource, /该问诊将从列表隐藏，已有数据会保留/)
  assert.match(appSource, /function resumeUnfinished/)
})

test('已完成档案支持确认后软删除并关闭失效详情', () => {
  assert.match(template, /@click\.stop="deleteHistoryRecord\(record\)"/)
  assert.match(appSource, /\/api\/patients\/\$\{props\.patientId\}\/records\/\$\{record\.record_id\}\/delete/)
  assert.match(appSource, /该档案将从列表隐藏，已有问诊数据会保留。确定删除吗？/)
  assert.match(appSource, /historyDetail\.value\?\.record_id === record\.record_id/)
  assert.match(appSource, /const deletingRecordId = ref\(''\)/)
})

test('患者端使用可完全隐藏并记忆状态的全高侧栏', () => {
  assert.doesNotMatch(template, /class="topbar"/)
  assert.match(template, /class="sidebar-brand"/)
  assert.match(template, /aria-label="收起侧栏"/)
  assert.match(template, /aria-label="展开侧栏"/)
  assert.match(template, /class="sidebar-backdrop"/)
  assert.match(template, /class="floating-shell-actions"/)
  assert.match(appSource, /readSidebarCollapsed\(window\.localStorage\)/)
  assert.match(appSource, /writeSidebarCollapsed\(window\.localStorage/)
  assert.match(appSource, /matchMedia\('\(max-width: 860px\)'\)/)
  assert.match(styleSource, /\.sidebar-collapsed \.main-workspace\s*\{[^}]*margin-left:\s*0/s)
  assert.match(styleSource, /\.floating-shell-actions\s*\{[^}]*position:\s*fixed/s)
  assert.match(styleSource, /\.sidebar-backdrop\s*\{[^}]*position:\s*fixed/s)
  assert.match(styleSource, /\.mobile-sidebar-open \.left-panel\s*\{[^}]*transform:\s*translateX\(0\)/s)
})

test('桌面端主内容下移且移动端顶部间距保持不变', () => {
  assert.match(styleSource, /\.main-workspace\s*\{[^}]*padding:\s*70px clamp\(24px, 4vw, 64px\)/s)
  assert.match(styleSource, /@media \(max-width: 860px\)[\s\S]*?padding:\s*76px 12px 24px/s)
})

test('开放描述页将阶段身份与正文标题拆为独立区块', () => {
  const openIntake = template.match(/viewStage === 'open_intake'[\s\S]*?(?=<section v-else-if)/)?.[0] || ''
  assert.match(openIntake, /class="assistant-intro open-intake-identity"[\s\S]*?开放描述[\s\S]*?<\/div>\s*<div class="open-intake-heading">/)
  assert.match(styleSource, /\.open-intake-heading\s*\{[^}]*padding-top:/s)
})

test('开放描述介绍区融入背景且具体问题使用独立白色卡片', () => {
  assert.match(template, /class="open-intake-header"[\s\S]*?open-intake-identity[\s\S]*?open-intake-heading/)
  assert.match(styleSource, /\.open-intake\s*\{[^}]*background:\s*transparent/s)
  assert.match(styleSource, /\.open-question\s*\{[^}]*background:\s*rgba?\(/s)
})

test('侧栏已完成档案最多渲染最近两条且放弃操作位于底部', () => {
  assert.match(template, /v-for="record in visibleHistoryRecords"/)
  assert.match(appSource, /const visibleHistoryRecords = computed\(\(\) => historyRecords\.value\.slice\(0, 2\)\)/)
  assert.match(template, /class="sidebar-footer"[\s\S]*?class="archive-current-link sidebar-current-action"/)
})

test('开放问题卡片使用更紧凑的排版', () => {
  assert.match(styleSource, /\.open-question textarea\s*\{[^}]*min-height:\s*168px/s)
  assert.match(styleSource, /\.open-question h3\s*\{[^}]*font-size:\s*19px/s)
})
