<template>
  <section class="doctor-panel" aria-label="医生诊前资料视图">
    <div class="doctor-panel-head">
      <div>
        <span class="section-label">医生视图</span>
        <h2>诊前资料执行情况</h2>
      </div>
      <span class="stop-reason">{{ formatStopReason(summary?.stop_reason) }}</span>
    </div>

    <p v-if="loading" class="muted">正在读取医生摘要...</p>
    <p v-else-if="error" class="form-error">{{ error }}</p>

    <template v-else-if="summary">
      <div class="score-grid">
        <article :class="['score-item', scoreTone(execution.total_score, 85)]">
          <span>总执行度</span>
          <strong>{{ displayScore(execution.total_score) }}</strong>
          <div class="score-track"><i :style="{ width: `${bounded(execution.total_score)}%` }"></i></div>
          <small>正常门槛 85</small>
        </article>
        <article :class="['score-item', scoreTone(execution.differentiation_score, 55)]">
          <span>辨证资料</span>
          <strong>{{ displayScore(execution.differentiation_score) }}<em>/70</em></strong>
          <div class="score-track"><i :style="{ width: `${bounded((execution.differentiation_score || 0) / 70 * 100)}%` }"></i></div>
          <small>最低要求 55/70</small>
        </article>
        <article :class="['score-item', scoreTone(execution.safety_score, 27)]">
          <span>开方安全</span>
          <strong>{{ displayScore(execution.safety_score) }}<em>/30</em></strong>
          <div class="score-track"><i :style="{ width: `${bounded((execution.safety_score || 0) / 30 * 100)}%` }"></i></div>
          <small>最低要求 27/30</small>
        </article>
      </div>

      <section class="doctor-section safety-section">
        <div class="section-heading">
          <h3>开方安全资料</h3>
          <span>{{ confirmedSafety }}/{{ summary.safety_fields?.length || 0 }} 项明确</span>
        </div>
        <div class="safety-table">
          <div v-for="field in summary.safety_fields" :key="field.field_key" class="safety-row">
            <div>
              <strong>{{ field.group }}</strong>
              <span :class="['status-text', field.status]">{{ statusLabel(field.status) }}</span>
            </div>
            <p>{{ field.evidence?.join('；') || '待诊中确认' }}</p>
          </div>
        </div>
      </section>

      <section class="doctor-section">
        <div class="section-heading"><h3>资料状态</h3><span>规则版本 {{ summary.rule_version }}</span></div>
        <div class="status-grid">
          <div v-for="group in visibleGroups" :key="group.key" class="status-group">
            <strong>{{ group.label }} · {{ group.items.length }}</strong>
            <ul>
              <li v-for="field in group.items" :key="field.field_key">
                <span>{{ field.group }}</span>
                <small>{{ field.evidence?.join('；') || '无可用证据' }}</small>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section v-if="summary.conflicts?.length" class="doctor-section conflict-section">
        <h3>需要医生确认的矛盾</h3>
        <p v-for="(item, index) in summary.conflicts" :key="index">{{ item.description || item.field_key }}</p>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatStopReason, scoreTone } from '../doctor-view.js'

const props = defineProps({
  summary: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const execution = computed(() => props.summary?.execution || {})
const confirmedSafety = computed(() => (props.summary?.safety_fields || []).filter((item) => item.status === 'confirmed').length)
const visibleGroups = computed(() => {
  const groups = props.summary?.field_groups || {}
  return [
    { key: 'confirmed', label: '已明确', items: groups.confirmed || [] },
    { key: 'partial', label: '部分明确', items: groups.partial || [] },
    { key: 'unavailable', label: '患者无法提供', items: groups.unavailable || [] },
    { key: 'not_asked', label: '待诊中确认', items: groups.not_asked || [] },
  ].filter((group) => group.items.length)
})

function bounded(value) {
  return Math.max(0, Math.min(100, Number(value) || 0))
}

function displayScore(value) {
  return Number(value || 0).toFixed(1)
}

function statusLabel(status) {
  return { confirmed: '已明确', partial: '部分明确', unavailable: '无法提供', not_asked: '待确认', not_applicable: '不适用' }[status] || '待确认'
}
</script>
