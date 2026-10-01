<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">中</div>
        <div>
          <h1>中医智能助手</h1>
          <p>成人肥胖诊前资料整理</p>
        </div>
      </div>
      <div class="top-actions">
        <span class="service-state"><i></i> 服务中</span>
        <span class="user-avatar">张</span>
        <strong>{{ doctorMode ? '医生视图' : '张女士' }}</strong>
      </div>
    </header>

    <main :class="['workspace', { 'doctor-workspace': doctorMode }]">
      <aside class="left-panel">
        <div class="flow-head">
          <span>问诊流程</span>
          <small>{{ state?.follow_up_count || 0 }} 次补充</small>
        </div>
        <ol class="stage-list">
          <li v-for="(stage, index) in flowStages" :key="stage.label" :class="stage.status">
            <span class="stage-number">{{ index + 1 }}</span>
            <div><strong>{{ stage.label }}</strong><small>{{ stage.description }}</small></div>
            <span v-if="stage.status === 'completed'" class="stage-done">✓</span>
          </li>
        </ol>
        <div class="privacy-note">
          <strong>安心问诊</strong>
          <p>资料仅用于本次诊前整理，并由医生在诊中进一步确认。</p>
        </div>
      </aside>

      <section class="main-panel">
        <div v-if="loading && !state" class="loading-state">正在准备问诊...</div>

        <section v-else-if="state && viewStage === 'open_intake'" class="open-intake">
          <div class="assistant-intro">
            <span class="assistant-avatar">医</span>
            <div>
              <span class="section-label">开放描述</span>
              <h2>先从您最关心的情况说起</h2>
              <p>不需要使用医学术语，按自己的感受描述即可。</p>
            </div>
          </div>
          <div class="open-question">
            <h3>{{ state.open_question }}</h3>
            <textarea
              v-model="openAnswer"
              rows="8"
              placeholder="例如：最近半年体重增加了十斤，饭后容易困，想改善体重和精神状态。"
              :disabled="saving"
              @keydown.ctrl.enter.prevent="submitOpenAnswer"
            ></textarea>
            <div class="composer-actions">
              <p v-if="formError" class="form-error">{{ formError }}</p>
              <button class="primary-button" :disabled="!openAnswer.trim() || saving" @click="submitOpenAnswer">
                {{ saving ? '正在提交...' : '开始整理' }}
              </button>
            </div>
          </div>
        </section>

        <section v-else-if="state && viewStage === 'analyzing'" class="chat-section" data-testid="follow-up-chat">
          <div class="chat-head">
            <div><span class="section-label">补充问诊</span><h2>正在整理您刚才的回答</h2></div>
            <span class="round-label">请稍候</span>
          </div>
          <div v-if="state.safety_alerts?.length" class="safety-alert persistent-alert">
            <strong>发现需要优先线下确认的情况</strong>
            <p>您仍可继续填写诊前资料；如果症状正在发生、明显加重，或伴有呼吸困难、晕厥，请及时就医。</p>
            <p v-for="item in state.safety_alerts" :key="item" class="safety-item">已记录：{{ item }}</p>
          </div>
          <div ref="messageList" class="message-list">
            <div v-if="state.open_answer" class="message-row patient-message opening-message"><p>{{ state.open_answer }}</p></div>
            <template v-for="(item, index) in state.follow_up_answers || []" :key="index">
              <div class="message-row assistant-message"><span class="chat-avatar">医</span><p>{{ item.question }}</p></div>
              <div class="message-row patient-message"><p>{{ item.answer }}</p></div>
            </template>
            <div class="message-row assistant-message"><span class="chat-avatar">医</span><p class="typing"><i></i><i></i><i></i></p></div>
          </div>
        </section>

        <section v-else-if="state && viewStage === 'follow_up_chat'" class="chat-section" data-testid="follow-up-chat">
          <div class="chat-head">
            <div><span class="section-label">补充问诊</span><h2>继续了解您的情况</h2></div>
            <span class="round-label">第 {{ currentRound }} 问</span>
          </div>
          <div v-if="state.safety_alerts?.length" class="safety-alert persistent-alert">
            <strong>发现需要优先线下确认的情况</strong>
            <p>您仍可继续填写诊前资料；如果症状正在发生、明显加重，或伴有呼吸困难、晕厥，请及时就医。</p>
            <p v-for="item in state.safety_alerts" :key="item" class="safety-item">已记录：{{ item }}</p>
          </div>
          <div ref="messageList" class="message-list" data-testid="follow-up-messages">
            <div v-if="state.open_answer" class="message-row patient-message opening-message"><p>{{ state.open_answer }}</p></div>
            <template v-for="(item, index) in state.follow_up_answers || []" :key="index">
              <div class="message-row assistant-message"><span class="chat-avatar">医</span><p>{{ item.question }}</p></div>
              <div class="message-row patient-message"><p>{{ item.answer }}</p></div>
            </template>
            <div class="message-row assistant-message current-message"><span class="chat-avatar">医</span><p>{{ state.next_question }}</p></div>
          </div>
          <div class="chat-composer">
            <textarea
              v-model="followUpAnswer"
              rows="4"
              placeholder="请按实际情况回答，不清楚也可以直接说明。"
              :disabled="saving"
              @keydown.ctrl.enter.prevent="submitFollowUp"
            ></textarea>
            <div class="composer-actions">
              <p v-if="formError" class="form-error">{{ formError }}</p>
              <button class="primary-button" :disabled="!followUpAnswer.trim() || saving" @click="submitFollowUp">
                {{ saving ? '正在发送...' : '发送回答' }}
              </button>
            </div>
          </div>
        </section>

        <section v-else-if="state && viewStage === 'escalated'" class="result-section escalated-section">
          <span class="section-label alert-label">安全提示</span>
          <h2>建议优先由医生线下评估</h2>
          <p>{{ state.stop_reason_public }}</p>
          <div class="safety-alert" v-if="state.safety_alerts?.length">
            <p v-for="item in state.safety_alerts" :key="item">{{ item }}</p>
          </div>
          <div v-if="state.report_markdown" class="markdown-content" v-html="renderMarkdown(state.report_markdown)"></div>
          <div class="result-actions"><button class="secondary-button" @click="restart">重新开始</button><button class="primary-button" :disabled="!canSave" @click="saveRecord">{{ saveLabel }}</button></div>
        </section>

        <section v-else-if="state && viewStage === 'result'" class="result-section">
          <div class="result-head">
            <div><span class="section-label">问诊完成</span><h2>本次诊前档案已整理完成</h2><p>{{ state.stop_reason_public }}</p></div>
          </div>
          <div v-if="state.safety_alerts?.length" class="safety-alert persistent-alert result-safety-alert">
            <strong>发现需要优先线下确认的情况</strong>
            <p>您仍可继续填写诊前资料；如果症状正在发生、明显加重，或伴有呼吸困难、晕厥，请及时就医。</p>
            <p v-for="item in state.safety_alerts" :key="item" class="safety-item">已记录：{{ item }}</p>
          </div>
          <div class="markdown-content report-content" v-html="renderMarkdown(state.report_markdown)"></div>
          <section class="exam-section">
            <div class="section-title"><span class="section-label">检查建议</span><h3>推荐检查项目</h3></div>
            <p v-if="!state.recommended_exams?.length && state.safety_alerts?.length" class="empty-note alert-empty-note">存在需要优先线下评估的情况，暂不提供常规检查建议。</p>
            <p v-else-if="!state.recommended_exams?.length" class="empty-note">当前资料下暂无需要特别提示的检查项目，最终由医生结合诊中情况决定。</p>
            <div v-else class="exam-grid">
              <article v-for="exam in state.recommended_exams" :key="exam.name" class="exam-item">
                <div><strong>{{ exam.name }}</strong><span>{{ examPriorityLabel(exam.priority) }}</span></div>
                <small>{{ exam.type }} · {{ exam.department }}</small>
                <p>{{ exam.reason }}</p>
                <p v-if="exam.precautions" class="exam-note">注意：{{ exam.precautions }}</p>
              </article>
            </div>
          </section>
          <div class="result-actions"><button class="secondary-button" @click="restart">重新开始</button><button class="primary-button" :disabled="!canSave" @click="saveRecord">{{ saveLabel }}</button></div>
        </section>

        <p class="disclaimer">本系统仅用于诊前资料整理，不能替代医生诊断、检查决策或治疗。</p>
      </section>

      <DoctorExecutionPanel v-if="doctorMode" :summary="doctorSummary" :loading="doctorLoading" :error="doctorError" />
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import DoctorExecutionPanel from './components/DoctorExecutionPanel.vue'
import { isDoctorView } from './doctor-view.js'
import { canSaveIntakeRecord, getIntakeViewStage } from './follow-up-stage.js'

const params = new URLSearchParams(window.location.search)
const doctorMode = isDoctorView(window.location.search)
const sessionId = ref(params.get('session') || makeSessionId())
const state = ref(null)
const openAnswer = ref('')
const followUpAnswer = ref('')
const loading = ref(false)
const saving = ref(false)
const saved = ref(false)
const formError = ref('')
const messageList = ref(null)
const doctorSummary = ref(null)
const doctorLoading = ref(false)
const doctorError = ref('')
const md = new MarkdownIt({ html: false, linkify: false, typographer: true })

const viewStage = computed(() => getIntakeViewStage({ state: state.value, loading: loading.value, saving: saving.value }))
const currentRound = computed(() => (state.value?.follow_up_count || 0) + 1)
const canSave = computed(() => canSaveIntakeRecord({ state: state.value, saved: saved.value, saving: saving.value }))
const saveLabel = computed(() => saved.value ? '已保存' : '保存档案')
const flowStages = computed(() => {
  const phase = state.value?.phase || 'open_intake'
  return [
    { label: '开放描述', description: '说明主要困扰与变化', status: phase === 'open_intake' ? 'current' : 'completed' },
    { label: '补充问诊', description: '逐项确认关键资料', status: ['processing', 'follow_up'].includes(phase) ? 'current' : (['completed', 'escalated'].includes(phase) ? 'completed' : 'pending') },
    { label: '诊前档案', description: '整理资料与检查建议', status: ['completed', 'escalated'].includes(phase) ? 'current' : 'pending' },
  ]
})

watch([viewStage, () => state.value?.follow_up_count], async () => {
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
})

function makeSessionId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function syncUrl() {
  const next = new URLSearchParams(window.location.search)
  next.set('session', sessionId.value)
  history.replaceState(null, '', `${window.location.pathname}?${next.toString()}`)
}

function renderMarkdown(text) {
  return text ? md.render(text) : ''
}

async function request(url, options = {}) {
  const response = await fetch(url, options)
  const payload = await response.json()
  if (!response.ok) throw new Error(payload.detail || '请求失败，请稍后再试。')
  return payload
}

async function loadState() {
  loading.value = true
  formError.value = ''
  try {
    state.value = await request(`/api/intake/session/${sessionId.value}`)
    openAnswer.value = state.value.open_answer || ''
    syncUrl()
    await loadDoctorSummary()
  } catch (error) {
    formError.value = error.message
  } finally {
    loading.value = false
  }
}

async function submitOpenAnswer() {
  const answer = openAnswer.value.trim()
  if (!answer || saving.value) return
  saving.value = true
  formError.value = ''
  try {
    state.value = await request(`/api/intake/session/${sessionId.value}/open-answer`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answer }),
    })
    await analyzeTurn()
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

async function submitFollowUp() {
  const answer = followUpAnswer.value.trim()
  if (!answer || saving.value) return
  saving.value = true
  formError.value = ''
  try {
    state.value = await request(`/api/intake/session/${sessionId.value}/follow-up`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answer }),
    })
    followUpAnswer.value = ''
    await analyzeTurn()
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

async function analyzeTurn() {
  state.value = await request(`/api/intake/session/${sessionId.value}/analyze`, { method: 'POST' })
  saved.value = false
  await loadDoctorSummary()
}

async function loadDoctorSummary() {
  if (!doctorMode) return
  doctorLoading.value = true
  doctorError.value = ''
  try {
    doctorSummary.value = await request(`/api/intake/session/${sessionId.value}/doctor-summary`)
  } catch (error) {
    doctorError.value = error.message
  } finally {
    doctorLoading.value = false
  }
}

async function saveRecord() {
  if (!canSave.value) return
  saving.value = true
  try {
    await request('/api/save_record', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId.value, patient_name: '匿名患者' }),
    })
    saved.value = true
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

function restart() {
  sessionId.value = makeSessionId()
  state.value = null
  doctorSummary.value = null
  openAnswer.value = ''
  followUpAnswer.value = ''
  formError.value = ''
  saved.value = false
  loadState()
}

function examPriorityLabel(priority) {
  return { urgent: '尽快就医', priority: '优先检查', routine: '常规参考' }[priority] || '常规参考'
}

onMounted(loadState)
</script>
