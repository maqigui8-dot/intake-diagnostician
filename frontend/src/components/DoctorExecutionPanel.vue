<template>
  <section class="doctor-panel" aria-label="医生诊前资料视图">
    <div class="doctor-panel-head">
      <div>
        <span class="section-label">医生视图</span>
        <h2>分层诊前档案</h2>
      </div>
      <span class="stop-reason">{{ formatStopReason(summary?.stop_reason) }}</span>
    </div>

    <p v-if="loading" class="muted">正在读取医生摘要...</p>
    <p v-else-if="error" class="form-error">{{ error }}</p>

    <template v-else-if="summary">
      <section class="doctor-section">
        <div class="section-heading">
          <h3>诊前资料就绪度</h3>
          <span>{{ readinessStatus }}</span>
        </div>
        <div class="doctor-readiness-grid">
          <div><small>核心诊前资料</small><strong>{{ readiness.core?.completed ?? 0 }}/{{ readiness.core?.total ?? 0 }}</strong></div>
          <div><small>安全资料</small><strong>{{ readiness.safety?.completed ?? 0 }}/{{ readiness.safety?.total ?? 0 }}</strong></div>
          <div><small>核心未解决冲突</small><strong>{{ readiness.core_conflicts ?? 0 }} 项</strong></div>
          <div><small>诊中建议补充</small><strong>{{ readiness.optional_keys?.length ?? 0 }} 项</strong></div>
        </div>
        <p class="coverage-helper">{{ summary.decision_explanation?.stop?.reason || '选择问诊记录后查看结束依据。' }}</p>
      </section>

      <!-- 1. 基础测量与肥胖范围 -->
      <section class="doctor-section">
        <div class="section-heading">
          <h3>基础测量与肥胖范围</h3>
          <span>规则版本 {{ summary.rule_version }}</span>
        </div>
        <div class="baseline-grid-rows">
          <div class="baseline-cell"><span>年龄</span><strong>{{ baseline.age ?? '—' }} 岁</strong></div>
          <div class="baseline-cell"><span>生理性别</span><strong>{{ sexLabel(baseline.sex) }}</strong></div>
          <div class="baseline-cell"><span>身高</span><strong>{{ baseline.height_cm ?? '—' }} cm</strong></div>
          <div class="baseline-cell"><span>体重</span><strong>{{ baseline.weight_kg ?? '—' }} kg</strong></div>
          <div class="baseline-cell"><span>BMI</span><strong>{{ baseline.bmi ?? '—' }}</strong></div>
          <div class="baseline-cell"><span>BMI 分级</span><strong>{{ baseline.bmi_grade || '—' }}</strong></div>
          <div class="baseline-cell"><span>腰围</span><strong>{{ baseline.waist_cm ?? '—' }} cm</strong></div>
          <div class="baseline-cell"><span>测量时间</span><strong>{{ baseline.measured_at || '—' }}</strong></div>
        </div>
        <p v-if="baseline.rule_hint" class="rule-hint">{{ baseline.rule_hint }}</p>
        <p v-if="baseline.diagnosis_copy" class="diagnosis-copy">{{ baseline.diagnosis_copy }}</p>
      </section>

      <!-- 分层资料覆盖度 -->
      <section class="doctor-section">
        <div class="section-heading">
          <h3>分层资料覆盖度</h3>
          <span>覆盖度不单独决定是否结束追问</span>
        </div>
        <p class="coverage-helper">下列比例表示各类资料的加权覆盖情况；在线追问是否结束，以核心与安全资料、冲突核对结果为准。</p>
        <div class="layer-grid">
          <div v-for="layer in layerList" :key="layer.key" class="layer-item">
            <span>{{ layer.label }}</span>
            <strong>{{ layer.key === 'baseline' ? (layer.ready ? '就绪' : '待确认') : displayScore(layer.score) }}</strong>
            <small>{{ layerDescription(layer.key) }}</small>
            <small>{{ layerMeta(layer) }}</small>
          </div>
        </div>
      </section>

      <!-- 2-6. 各分层字段区块 -->
      <section v-for="section in fieldSections" :key="section.title" class="doctor-section">
        <div class="section-heading">
          <h3>{{ section.title }}</h3>
          <span>{{ section.items.length }} 项 · {{ statusSummary(section.items) }}</span>
        </div>
        <div class="field-table">
          <div v-for="field in section.items" :key="field.field_key" class="field-row">
            <div class="field-row-head">
              <strong>{{ field.group }}</strong>
              <span :class="['status-text', field.status]">{{ statusLabel(field.status) }}</span>
            </div>
            <p>{{ field.evidence?.join('；') || '待诊中确认' }}</p>
          </div>
        </div>

        <template v-if="section.key === 'pending'">
          <div v-if="summary.conflicts?.length" class="pending-block conflict-block">
            <strong>需要医生确认的矛盾</strong>
            <p v-for="(item, index) in summary.conflicts" :key="index">{{ item.description || item.field_key }}</p>
          </div>

          <div v-if="summary.safety_alerts?.length" class="pending-block safety-block">
            <strong>安全提醒</strong>
            <p v-for="item in summary.safety_alerts" :key="item">{{ item }}</p>
          </div>

          <div class="pending-block exam-block">
            <strong>检查候选（{{ summary.recommended_exams?.length || 0 }} 项）</strong>
            <p v-if="!summary.recommended_exams?.length" class="empty-note">暂无检查候选，由医生结合诊中情况决定。</p>
            <div v-else class="exam-list">
              <article v-for="exam in summary.recommended_exams" :key="exam.name" class="exam-item">
                <div><strong>{{ exam.name }}</strong><span>{{ examPriorityLabel(exam.priority) }}</span></div>
                <small>{{ exam.type }} · {{ exam.department }} · {{ exam.source }}</small>
                <p>{{ exam.reason }}</p>
                <p class="exam-note">触发：{{ exam.trigger }}</p>
                <p v-if="exam.precautions" class="exam-note">注意：{{ exam.precautions }}</p>
              </article>
            </div>
          </div>
        </template>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatStopReason } from '../doctor-view.js'

const props = defineProps({
  summary: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const SECTION_KEYS = [
  { key: 'course', title: '肥胖病程与可能病因' },
  { key: 'disease', title: '相关疾病风险' },
  { key: 'lifestyle', title: '生活方式与心理情况' },
  { key: 'tcm', title: '中医诊前资料' },
  { key: 'pending', title: '待医生确认' },
]

const baseline = computed(() => props.summary?.baseline_assessment || {})
const readiness = computed(() => props.summary?.readiness_summary || {})
const readinessStatus = computed(() => ({
  ready: '可以停止在线追问',
  collecting: '继续在线追问',
  needs_doctor: '诊中补充核心资料',
  escalated: '需优先线下评估',
}[readiness.value.status] || '待确认'))
const layerList = computed(() => {
  const layers = props.summary?.layer_execution || {}
  return ['baseline', 'risk', 'tcm', 'safety'].map((key) => layers[key]).filter(Boolean)
})

const fieldSections = computed(() => {
  const groups = props.summary?.field_groups || {}
  return SECTION_KEYS.map((section) => ({ ...section, items: groups[section.title] || [] }))
})

function displayScore(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function sexLabel(sex) {
  return { male: '男', female: '女' }[sex] || '—'
}

function statusLabel(status) {
  return { confirmed: '已明确', partial: '部分明确', unavailable: '无法提供', not_asked: '待确认', not_applicable: '不适用' }[status] || '待确认'
}

function layerMeta(layer) {
  if (layer.key === 'baseline') return layer.ready ? '基础测量已确认' : '基础测量未完成'
  return layer.raw != null && layer.max != null ? `加权覆盖 ${layer.raw}/${layer.max} 分` : '暂无覆盖数据'
}

function layerDescription(key) {
  return {
    baseline: '年龄、身高、体重等基础测量',
    risk: '病程、生活方式与相关疾病风险',
    tcm: '食欲、二便、睡眠等中医症状',
    safety: '过敏、用药、既往疾病与危险信号',
  }[key] || ''
}

function statusSummary(items) {
  const counts = items.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1
    return acc
  }, {})
  return ['confirmed', 'partial', 'unavailable', 'not_asked', 'not_applicable']
    .filter((status) => counts[status])
    .map((status) => `${statusLabel(status)} ${counts[status]}`)
    .join(' · ') || '暂无字段'
}

function examPriorityLabel(priority) {
  return { urgent: '尽快就医', priority: '优先检查', routine: '常规参考' }[priority] || '常规参考'
}
</script>
