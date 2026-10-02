<template>
  <div :class="['app-shell', { 'sidebar-collapsed': sidebarCollapsed && !isMobile, 'mobile-sidebar-open': mobileSidebarOpen }]">
    <div v-if="!sidebarVisible" class="floating-shell-actions">
      <button type="button" class="shell-icon-button" aria-label="展开侧栏" :aria-expanded="sidebarVisible" @click="expandSidebar">☰</button>
      <button type="button" class="floating-new-button" @click="restart"><span>+</span> 新建问诊</button>
    </div>
    <button v-if="isMobile && mobileSidebarOpen" type="button" class="sidebar-backdrop" aria-label="关闭侧栏" @click="closeMobileSidebar"></button>

    <aside :class="['left-panel', { open: sidebarVisible }]">
      <div class="sidebar-brand">
        <div class="brand-mark">中</div>
        <div class="brand-copy">
          <h1>中医智能助手</h1>
          <p>成人肥胖诊前资料整理</p>
        </div>
        <button type="button" class="sidebar-collapse-button" aria-label="收起侧栏" :aria-expanded="sidebarVisible" @click="collapseSidebar">‹</button>
      </div>
      <button type="button" class="sidebar-primary-action" @click="restart">
          <span>+</span> 新建问诊
      </button>
      <div class="sidebar-scroll">
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
        <div v-if="state?.progress && state.phase !== 'baseline_collection'" class="patient-core-progress">
          <span>关键资料整理进度</span>
          <strong>{{ state.progress.core_completed }}/{{ state.progress.core_total }} 项已确认</strong>
          <p v-if="state.progress.remaining_count && state.phase === 'incomplete' && !state.can_continue">仍有 {{ state.progress.remaining_count }} 项未确认，本轮在线追问已结束。</p>
          <p v-else-if="state.progress.remaining_count">还需确认 {{ state.progress.remaining_count }} 项，接下来会优先补充关键资料。</p>
          <p v-else>关键资料已确认，可以结束在线问诊。</p>
        </div>
        <button v-if="canEditBaseline" type="button" class="edit-baseline-link left-panel-edit" @click="startEditBaseline">编辑基础资料</button>
        <section class="history-panel" aria-label="我的问诊记录">
          <div class="history-head"><strong>继续问诊</strong><small>{{ visibleUnfinished.length }}</small></div>
          <p v-if="historyError" class="history-error">{{ historyError }}</p>
          <p v-else-if="!visibleUnfinished.length" class="history-empty">暂无其他待继续的问诊。</p>
          <article v-for="item in visibleUnfinished" :key="item.session_id" class="unfinished-record">
            <button type="button" class="unfinished-main" @click="resumeUnfinished(item)">
              <strong>{{ item.primary_concern }}</strong>
              <small>{{ formatRecordTime(item.updated_at) }} · {{ item.stage_label }}</small>
            </button>
            <button type="button" class="unfinished-archive" :disabled="archivingSessionId === item.session_id" @click.stop="archiveUnfinished(item)">
              {{ archivingSessionId === item.session_id ? '处理中' : '放弃' }}
            </button>
          </article>
          <div class="history-head completed-history-head"><strong>已完成档案</strong><small>{{ historyRecords.length }}</small></div>
          <p v-if="!historyError && !historyRecords.length" class="history-empty">完成问诊后，档案会自动保存在这里。</p>
          <article
            v-for="record in visibleHistoryRecords"
            :key="record.record_id"
            class="completed-record"
            :class="{ active: historyDetail?.record_id === record.record_id }"
          >
            <button type="button" class="history-record" @click="openHistory(record.record_id)">
              <strong>{{ record.primary_concern }}</strong>
              <small>{{ formatRecordDate(record.created_at) }} · {{ record.status }}</small>
            </button>
            <button type="button" class="record-delete" :disabled="deletingRecordId === record.record_id" @click.stop="deleteHistoryRecord(record)">
              {{ deletingRecordId === record.record_id ? '处理中' : '删除' }}
            </button>
          </article>
        </section>
      </div>
      <div class="sidebar-footer">
        <button v-if="canArchiveCurrent" type="button" class="archive-current-link sidebar-current-action" :disabled="archivingSessionId === sessionId" @click="archiveCurrent">
          放弃当前问诊
        </button>
        <div class="sidebar-user">
          <span class="user-avatar">{{ currentPatientName.slice(0, 1) }}</span>
          <div><strong>{{ currentPatientName }}</strong><small class="service-state"><i></i> 服务中</small></div>
          <select class="patient-switcher" :value="props.patientId" aria-label="切换演示患者" @change="switchPatient">
            <option value="patient-zhang">张女士</option>
            <option value="patient-ma">马先生</option>
            <option value="patient-li">李女士</option>
          </select>
        </div>
        <p>资料仅用于诊前整理，不能替代医生判断。</p>
      </div>
    </aside>

    <main class="main-workspace">
      <section class="main-panel">
        <section v-if="historyDetail" class="history-detail result-section workbench-panel">
          <div class="result-head">
            <div>
              <span class="section-label">已保存档案</span>
              <h2>{{ historyDetail.primary_concern }}</h2>
              <p>{{ formatRecordDate(historyDetail.created_at) }} · {{ historyDetail.status }}</p>
            </div>
          </div>
          <div v-if="historyDetail.bmi_assessment?.bmi" class="bmi-card">
            <div class="bmi-row">
              <span class="section-label">BMI 结果</span>
              <strong>{{ historyDetail.bmi_assessment.bmi }}</strong>
              <span>{{ historyDetail.bmi_assessment.bmi_grade }}</span>
            </div>
            <p v-if="historyDetail.bmi_assessment.diagnosis_copy" class="diagnosis-copy">{{ historyDetail.bmi_assessment.diagnosis_copy }}</p>
          </div>
          <div v-if="historyDetail.report_markdown" class="markdown-content report-content" v-html="renderMarkdown(historyDetail.report_markdown)"></div>
          <section v-if="historyDetail.follow_up_answers?.length" class="history-answers">
            <div class="section-title"><span class="section-label">问答记录</span><h3>本次补充问答</h3></div>
            <article v-for="(item, index) in historyDetail.follow_up_answers" :key="`${item.question}-${index}`" class="history-answer">
              <strong>问：{{ item.question }}</strong>
              <p>答：{{ item.answer }}</p>
            </article>
          </section>
          <section class="exam-section">
            <div class="section-title"><span class="section-label">检查准备</span><h3>建议检查项目</h3></div>
            <p v-if="!historyDetail.recommended_exams?.length" class="empty-note">本次档案暂无特别提示的检查项目，最终以医生诊中建议为准。</p>
            <div v-else class="exam-grid">
              <article v-for="exam in historyDetail.recommended_exams" :key="exam.name" class="exam-item">
                <div><strong>{{ exam.name }}</strong><span>{{ examPriorityLabel(exam.priority) }}</span></div>
                <small>{{ exam.type }} · {{ exam.department }}</small>
                <p>{{ exam.reason }}</p>
                <p v-if="exam.precautions" class="exam-note">注意：{{ exam.precautions }}</p>
              </article>
            </div>
          </section>
          <p v-if="formError" class="form-error">{{ formError }}</p>
          <div class="result-actions"><button class="secondary-button" @click="closeHistory">返回当前问诊</button><button class="primary-button" @click="restart">新建问诊</button></div>
        </section>

        <div v-else-if="loading && !state" class="loading-state">正在准备问诊...</div>

        <section v-else-if="state && (viewStage === 'baseline_collection' || editingBaseline)" class="baseline-form workbench-panel">
          <div class="assistant-intro">
            <span class="assistant-avatar">医</span>
            <div>
              <span class="section-label">基础资料</span>
              <h2>先了解一下您的基本情况</h2>
              <p>填写后即可开始描述困扰；这些资料仅用于诊前整理，最终由医生确认。</p>
            </div>
          </div>
          <form class="baseline-body" @submit.prevent="submitBaseline">
            <div class="baseline-grid">
              <label class="field">
                <span>年龄</span>
                <input type="number" min="18" max="120" step="1" v-model.number="baseline.age" placeholder="例如 32" />
                <small>岁 · 18–120</small>
              </label>
              <div class="field">
                <span>生理性别</span>
                <div class="segmented" role="radiogroup" aria-label="生理性别">
                  <button type="button" :class="{ active: baseline.sex === 'male' }" @click="baseline.sex = 'male'">男</button>
                  <button type="button" :class="{ active: baseline.sex === 'female' }" @click="baseline.sex = 'female'">女</button>
                </div>
              </div>
              <label class="field">
                <span>身高</span>
                <input type="number" min="100" max="250" step="0.1" v-model.number="baseline.height_cm" placeholder="例如 170" />
                <small>厘米 · 100–250</small>
              </label>
              <label class="field">
                <span>体重</span>
                <input type="number" min="20" max="500" step="0.1" v-model.number="baseline.weight_kg" placeholder="例如 81" />
                <small>千克 · 20–500</small>
              </label>
            </div>
            <section class="baseline-optional">
              <button type="button" class="optional-toggle" :aria-expanded="showOptionalMeasurements" @click="showOptionalMeasurements = !showOptionalMeasurements">
                <span>补充测量信息（可选）</span>
                <small>{{ showOptionalMeasurements ? '收起' : '展开' }}</small>
              </button>
              <div v-if="showOptionalMeasurements" class="baseline-grid baseline-optional-content">
                <label class="field">
                  <span>腰围</span>
                  <input type="number" min="0" step="0.1" v-model.number="baseline.waist_cm" placeholder="选填" />
                  <small>厘米 · 大于0</small>
                </label>
                <label class="field">
                  <span>臀围</span>
                  <input type="number" min="0" step="0.1" v-model.number="baseline.hip_cm" placeholder="选填" />
                  <small>厘米 · 大于0</small>
                </label>
              </div>
            </section>
            <div class="baseline-grid">
              <label class="field">
                <span>测量日期</span>
                <input type="date" v-model="baseline.measured_at" />
                <small>最近一次测量的时间</small>
              </label>
            </div>
            <div class="composer-actions">
              <p v-if="formError" class="form-error">{{ formError }}</p>
              <small>提交后即可开始描述您的困扰</small>
              <button v-if="editingBaseline" class="secondary-button" type="button" :disabled="saving" @click="cancelEditBaseline">取消</button>
              <button class="primary-button" type="submit" :disabled="!baselineValid || saving">
                {{ saving ? '正在提交...' : (editingBaseline ? '保存修改' : '确认并继续') }}
              </button>
            </div>
          </form>
        </section>

        <section v-else-if="state && viewStage === 'open_intake'" class="open-intake workbench-panel">
          <div class="open-intake-header">
            <div class="assistant-intro open-intake-identity">
              <span class="assistant-avatar">医</span>
              <span class="section-label">开放描述</span>
            </div>
            <div class="open-intake-heading">
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
              @keydown.enter="handleOpenEnter"
            ></textarea>
            <div class="composer-actions">
              <p v-if="formError" class="form-error">{{ formError }}</p>
              <small>按 Enter 发送，Shift + Enter 换行</small>
              <button class="primary-button" :disabled="!openAnswer.trim() || saving" @click="submitOpenAnswer">
                {{ saving ? '正在提交...' : '开始整理' }}
              </button>
            </div>
          </div>
        </section>

        <section v-else-if="state && viewStage === 'analyzing'" class="chat-section chat-workbench" data-testid="follow-up-chat">
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

        <section v-else-if="state && viewStage === 'follow_up_chat'" class="chat-section chat-workbench" data-testid="follow-up-chat">
          <div class="chat-head">
            <div><span class="section-label">补充问诊</span><h2>继续了解您的情况</h2></div>
            <span class="round-label">第 {{ currentRound }} 问 · 已确认 {{ state.progress.core_completed }}/{{ state.progress.core_total }} 项</span>
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
              @keydown.enter="handleFollowUpEnter"
            ></textarea>
            <div class="composer-actions">
              <p v-if="formError" class="form-error">{{ formError }}</p>
              <small>按 Enter 发送，Shift + Enter 换行</small>
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
          <div class="result-actions"><button class="secondary-button" @click="restart">重新开始</button></div>
        </section>

        <section v-else-if="state && viewStage === 'result'" class="result-section">
          <div class="result-head">
            <div>
              <span class="section-label">{{ state.phase === 'incomplete' ? '资料待补充' : '问诊完成' }}</span>
              <h2>{{ state.phase === 'incomplete' ? '本次诊前资料尚未完整' : '本次诊前档案已整理完成' }}</h2>
              <p>{{ state.stop_reason_public }}</p>
              <p v-if="state.phase === 'incomplete' && !state.can_continue">在线追问已结束，本次回答已保留为草稿。请在下方补充仍未确认的资料。</p>
            </div>
          </div>
          <div v-if="state.progress" class="result-progress" aria-label="关键资料状态">
            <div><strong>{{ state.progress.core_completed }}</strong><span>已确认</span></div>
            <div><strong>{{ state.progress.pending_count }}</strong><span>待确认</span></div>
            <div><strong>{{ state.progress.unavailable_count }}</strong><span>暂无法确认</span></div>
          </div>
          <p class="result-progress-note">以上仅表示关键诊前资料的整理状态，不代表诊断结论。</p>
          <section v-if="state.phase === 'incomplete' && state.blocking_fields?.length" class="patient-review" aria-label="草稿待补充资料">
            <div class="section-title"><span class="section-label">草稿缺口</span><h3>仍需您确认</h3></div>
            <p class="review-hint">这些内容尚未核实，不能保存为正式档案。您可以在下方逐项补充。</p>
            <ul><li v-for="item in state.blocking_fields" :key="item.field_key">{{ item.label }}</li></ul>
          </section>
          <div v-if="state.bmi_assessment?.bmi" class="bmi-card">
            <div class="bmi-row">
              <span class="section-label">BMI 结果</span>
              <strong>{{ state.bmi_assessment.bmi }}</strong>
              <span>{{ state.bmi_assessment.bmi_grade }}</span>
            </div>
            <p v-if="state.bmi_assessment.diagnosis_copy" class="diagnosis-copy">达到成人肥胖范围，待医生确认</p>
            <button v-if="canEditBaseline" type="button" class="edit-baseline-link" @click="startEditBaseline">编辑基础资料</button>
          </div>
          <div v-if="state.safety_alerts?.length" class="safety-alert persistent-alert result-safety-alert">
            <strong>发现需要优先线下确认的情况</strong>
            <p>您仍可继续填写诊前资料；如果症状正在发生、明显加重，或伴有呼吸困难、晕厥，请及时就医。</p>
            <p v-for="item in state.safety_alerts" :key="item" class="safety-item">已记录：{{ item }}</p>
          </div>
          <section v-if="!saved && state.review_fields?.length" class="patient-review" aria-label="患者核对资料">
            <div class="section-title">
              <span class="section-label">保存前确认</span>
              <h3>{{ state.phase === 'incomplete' ? '补充并核对草稿资料' : '请核对以下关键资料' }}</h3>
            </div>
            <p class="review-hint">发现整理有误时可以修改。原始问答会保留；危险信号不能在这里删除。</p>
            <div v-for="item in state.review_fields" :key="item.field_key" class="review-row">
              <div class="review-row-content">
                <strong>{{ item.label }}</strong>
                <span>{{ item.value || '尚未确认' }}</span>
              </div>
              <button type="button" class="review-edit-button" :disabled="saving" @click="startPatientCorrection(item)">修改</button>
              <div v-if="editingReviewField === item.field_key" class="review-edit-form">
                <textarea v-model="reviewCorrectionText" maxlength="300" :aria-label="`修正${item.label}`" rows="2"></textarea>
                <div>
                  <button type="button" class="secondary-button" :disabled="saving" @click="cancelPatientCorrection">取消</button>
                  <button type="button" class="primary-button" :disabled="saving || !reviewCorrectionText.trim()" @click="submitPatientCorrection(item.field_key)">保存修正</button>
                </div>
              </div>
            </div>
          </section>
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
          <p v-if="formError" class="form-error">{{ formError }}</p>
          <div class="result-actions"><button class="secondary-button" @click="restart">重新开始</button><button v-if="state.phase === 'incomplete' && state.can_continue" class="primary-button" :disabled="saving" @click="continueIntake">继续补充</button><button v-else-if="state.phase === 'completed'" class="primary-button" :disabled="!canSave || !!editingReviewField" @click="saveRecord">{{ saveLabel }}</button></div>
        </section>

        <p class="disclaimer">本系统仅用于诊前资料整理，不能替代医生诊断、检查决策或治疗。</p>
      </section>

    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import { canContinueIntake, canSaveIntakeRecord, getIntakeViewStage } from './follow-up-stage.js'
import { readSidebarCollapsed, writeSidebarCollapsed } from './sidebar-state.js'
import { visibleUnfinishedSessions } from './unfinished-sessions.js'
import { patientName, patientUrl } from './patient-context.js'

const props = defineProps({ patientId: { type: String, required: true } })

const params = new URLSearchParams(window.location.search)
const currentPatientName = computed(() => patientName(props.patientId))
const sessionId = ref(params.get('session') || makeSessionId())
const sessionBase = computed(() => `/api/patients/${props.patientId}/sessions/${sessionId.value}`)
const state = ref(null)
const historyRecords = ref([])
const unfinishedSessions = ref([])
const historyDetail = ref(null)
const historyError = ref('')
const archivingSessionId = ref('')
const deletingRecordId = ref('')
const openAnswer = ref('')
const followUpAnswer = ref('')
const loading = ref(false)
const saving = ref(false)
const saved = ref(false)
const editingReviewField = ref('')
const reviewCorrectionText = ref('')
const formError = ref('')
const editingBaseline = ref(false)
const showOptionalMeasurements = ref(false)
const baseline = ref({
  age: '',
  sex: '',
  height_cm: '',
  weight_kg: '',
  waist_cm: '',
  hip_cm: '',
  measured_at: '',
})
const messageList = ref(null)
const sidebarCollapsed = ref(readSidebarCollapsed(window.localStorage))
const mobileSidebarOpen = ref(false)
const isMobile = ref(false)
let mobileMediaQuery = null
const md = new MarkdownIt({ html: false, linkify: false, typographer: true })

function _optionalNumber(value) {
  return value === '' || value === null || value === undefined ? null : Number(value)
}

const viewStage = computed(() => getIntakeViewStage({ state: state.value, loading: loading.value, saving: saving.value }))
const currentRound = computed(() => (state.value?.follow_up_count || 0) + 1)
const canSave = computed(() => canSaveIntakeRecord({ state: state.value, saved: saved.value, saving: saving.value }))
const sidebarVisible = computed(() => isMobile.value ? mobileSidebarOpen.value : !sidebarCollapsed.value)
const baselineValid = computed(() => {
  const b = baseline.value
  const age = Number(b.age)
  const height = Number(b.height_cm)
  const weight = Number(b.weight_kg)
  const waist = _optionalNumber(b.waist_cm)
  const hip = _optionalNumber(b.hip_cm)
  const optionalPositive = (value) => value === null || (Number.isFinite(value) && value > 0)
  return (
    Number.isInteger(age) && age >= 18 && age <= 120 &&
    (b.sex === 'male' || b.sex === 'female') &&
    Number.isFinite(height) && height >= 100 && height <= 250 &&
    Number.isFinite(weight) && weight >= 20 && weight <= 500 &&
    optionalPositive(waist) && optionalPositive(hip) &&
    !!b.measured_at
  )
})
const saveLabel = computed(() => saved.value ? '档案已保存' : (saving.value ? '正在保存…' : '确认并保存档案'))
const visibleUnfinished = computed(() => visibleUnfinishedSessions(unfinishedSessions.value, sessionId.value))
const visibleHistoryRecords = computed(() => historyRecords.value.slice(0, 2))
const canArchiveCurrent = computed(() => {
  const phase = state.value?.phase
  return !!state.value?.baseline && !['completed', 'incomplete', 'escalated'].includes(phase)
})
const canEditBaseline = computed(() => {
  const phase = state.value?.phase
  return !editingBaseline.value && !!phase && !['baseline_collection', 'completed', 'escalated'].includes(phase)
})
const flowStages = computed(() => {
  const phase = state.value?.phase || 'open_intake'
  const terminal = ['completed', 'incomplete', 'escalated'].includes(phase)
  return [
    { label: '基础资料', description: '填写年龄、身高与体重', status: phase === 'baseline_collection' ? 'current' : 'completed' },
    { label: '开放描述', description: '说明主要困扰与变化', status: phase === 'baseline_collection' ? 'pending' : (phase === 'open_intake' ? 'current' : 'completed') },
    { label: '补充问诊', description: '逐项确认关键资料', status: ['processing', 'follow_up'].includes(phase) ? 'current' : (terminal ? 'completed' : 'pending') },
    { label: '诊前档案', description: '整理资料与检查建议', status: terminal ? 'current' : 'pending' },
  ]
})

watch([viewStage, () => state.value?.follow_up_count], async () => {
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
})

function makeSessionId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function switchPatient(event) {
  window.location.href = patientUrl(event.target.value)
}

function collapseSidebar() {
  if (isMobile.value) {
    mobileSidebarOpen.value = false
    return
  }
  sidebarCollapsed.value = true
  writeSidebarCollapsed(window.localStorage, true)
}

function expandSidebar() {
  if (isMobile.value) {
    mobileSidebarOpen.value = true
    return
  }
  sidebarCollapsed.value = false
  writeSidebarCollapsed(window.localStorage, false)
}

function closeMobileSidebar() {
  mobileSidebarOpen.value = false
}

function updateMobileLayout(event) {
  isMobile.value = event.matches
  mobileSidebarOpen.value = false
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
  if (!response.ok) {
    const error = new Error(payload.detail || '请求失败，请稍后再试。')
    error.status = response.status
    throw error
  }
  return payload
}

async function loadState() {
  loading.value = true
  formError.value = ''
  try {
    try {
      state.value = await request(sessionBase.value)
    } catch (error) {
      if (error.status !== 404) throw error
      state.value = await request(`/api/patients/${props.patientId}/sessions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId.value }),
      })
    }
    openAnswer.value = state.value.open_answer || ''
    fillBaselineForm()
    syncUrl()
  } catch (error) {
    if (error.status === 410) {
      window.alert(error.message)
      restart()
    } else {
      formError.value = error.message
    }
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  historyError.value = ''
  try {
    historyRecords.value = await request(`/api/patients/${props.patientId}/records`)
  } catch {
    historyError.value = '问诊记录暂时无法加载，请确认服务已启动。'
  }
}

async function loadUnfinished() {
  historyError.value = ''
  try {
    unfinishedSessions.value = await request(`/api/patients/${props.patientId}/sessions/unfinished`)
  } catch {
    historyError.value = '待继续问诊暂时无法加载，请确认服务已启动。'
  }
}

async function resumeUnfinished(item) {
  if (saving.value || archivingSessionId.value) return
  sessionId.value = item.session_id
  state.value = null
  historyDetail.value = null
  editingReviewField.value = ''
  reviewCorrectionText.value = ''
  openAnswer.value = ''
  followUpAnswer.value = ''
  formError.value = ''
  saved.value = false
  editingBaseline.value = false
  closeMobileSidebar()
  await loadState()
}

async function archiveUnfinished(item) {
  if (archivingSessionId.value) return
  const confirmed = window.confirm('该问诊将从列表隐藏，已有数据会保留。确定放弃吗？')
  if (!confirmed) return
  archivingSessionId.value = item.session_id
  formError.value = ''
  try {
    await request(`/api/patients/${props.patientId}/sessions/${item.session_id}/archive`, { method: 'POST' })
    await loadUnfinished()
    if (item.session_id === sessionId.value) restart()
  } catch (error) {
    formError.value = error.message
  } finally {
    archivingSessionId.value = ''
  }
}

function archiveCurrent() {
  return archiveUnfinished({ session_id: sessionId.value })
}

async function openHistory(recordId) {
  formError.value = ''
  try {
    historyDetail.value = await request(`/api/patients/${props.patientId}/records/${recordId}`)
    closeMobileSidebar()
  } catch (error) {
    if (error.status === 410) historyDetail.value = null
    formError.value = error.message
  }
}

async function deleteHistoryRecord(record) {
  if (deletingRecordId.value) return
  const confirmed = window.confirm('该档案将从列表隐藏，已有问诊数据会保留。确定删除吗？')
  if (!confirmed) return
  deletingRecordId.value = record.record_id
  formError.value = ''
  try {
    await request(`/api/patients/${props.patientId}/records/${record.record_id}/delete`, { method: 'POST' })
    if (historyDetail.value?.record_id === record.record_id) historyDetail.value = null
    await loadHistory()
  } catch (error) {
    formError.value = error.message
  } finally {
    deletingRecordId.value = ''
  }
}

function closeHistory() {
  historyDetail.value = null
  formError.value = ''
}

function formatRecordDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '日期待补充'
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'numeric', day: 'numeric' }).format(date)
}

function formatRecordTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '时间待补充'
  return new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date)
}

function fillBaselineForm() {
  const b = state.value?.baseline
  if (!b) return
  baseline.value = {
    age: b.age ?? '',
    sex: b.sex ?? '',
    height_cm: b.height_cm ?? '',
    weight_kg: b.weight_kg ?? '',
    waist_cm: b.waist_cm ?? '',
    hip_cm: b.hip_cm ?? '',
    measured_at: b.measured_at ?? '',
  }
  showOptionalMeasurements.value = Boolean(b.waist_cm || b.hip_cm)
}

function startEditBaseline() {
  fillBaselineForm()
  formError.value = ''
  editingBaseline.value = true
}

function cancelEditBaseline() {
  editingBaseline.value = false
  formError.value = ''
}

async function submitBaseline() {
  if (!baselineValid.value || saving.value) return
  saving.value = true
  formError.value = ''
  try {
    state.value = await request(`${sessionBase.value}/baseline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        age: Number(baseline.value.age),
        sex: baseline.value.sex,
        height_cm: Number(baseline.value.height_cm),
        weight_kg: Number(baseline.value.weight_kg),
        waist_cm: _optionalNumber(baseline.value.waist_cm),
        hip_cm: _optionalNumber(baseline.value.hip_cm),
        measured_at: baseline.value.measured_at,
      }),
    })
    saved.value = false
    editingBaseline.value = false
    await loadUnfinished()
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

async function submitOpenAnswer() {
  const answer = openAnswer.value.trim()
  if (!answer || saving.value) return
  saving.value = true
  formError.value = ''
  try {
    state.value = await request(`${sessionBase.value}/open-answer`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answer }),
    })
    await analyzeTurn()
    await loadUnfinished()
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
    state.value = await request(`${sessionBase.value}/follow-up`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answer }),
    })
    followUpAnswer.value = ''
    await analyzeTurn()
    await loadUnfinished()
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

function handleComposerEnter(event, submit) {
  if (event.isComposing || event.shiftKey) return
  event.preventDefault()
  submit()
}

function handleOpenEnter(event) {
  handleComposerEnter(event, submitOpenAnswer)
}

function handleFollowUpEnter(event) {
  handleComposerEnter(event, submitFollowUp)
}

async function analyzeTurn() {
  state.value = await request(`${sessionBase.value}/analyze`, { method: 'POST' })
  saved.value = false
}

async function continueIntake() {
  if (!canContinueIntake({ state: state.value, saving: saving.value })) return
  saving.value = true
  formError.value = ''
  try {
    await analyzeTurn()
    await loadUnfinished()
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

async function saveRecord() {
  if (!canSave.value) return
  saving.value = true
  formError.value = ''
  try {
    await request(`${sessionBase.value}/save`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_confirmed: true }),
    })
    saved.value = true
    await Promise.all([loadHistory(), loadUnfinished()])
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

function startPatientCorrection(item) {
  editingReviewField.value = item.field_key
  reviewCorrectionText.value = item.value || ''
  formError.value = ''
}

function cancelPatientCorrection() {
  editingReviewField.value = ''
  reviewCorrectionText.value = ''
}

async function submitPatientCorrection(fieldKey) {
  const value = reviewCorrectionText.value.trim()
  if (!value || saving.value) return
  saving.value = true
  formError.value = ''
  try {
    state.value = await request(`${sessionBase.value}/corrections`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ field_key: fieldKey, value }),
    })
    cancelPatientCorrection()
  } catch (error) {
    formError.value = error.message
  } finally {
    saving.value = false
  }
}

function restart() {
  sessionId.value = makeSessionId()
  state.value = null
  historyDetail.value = null
  editingReviewField.value = ''
  reviewCorrectionText.value = ''
  openAnswer.value = ''
  followUpAnswer.value = ''
  formError.value = ''
  saved.value = false
  editingBaseline.value = false
  closeMobileSidebar()
  loadState()
}

function examPriorityLabel(priority) {
  return { urgent: '尽快就医', priority: '优先检查', routine: '常规参考' }[priority] || '常规参考'
}

onMounted(() => {
  mobileMediaQuery = window.matchMedia('(max-width: 860px)')
  updateMobileLayout(mobileMediaQuery)
  mobileMediaQuery.addEventListener('change', updateMobileLayout)
  loadState()
  loadHistory()
  loadUnfinished()
})

onBeforeUnmount(() => {
  mobileMediaQuery?.removeEventListener('change', updateMobileLayout)
})
</script>
