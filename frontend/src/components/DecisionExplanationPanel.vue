<template>
  <aside class="doctor-decision-column">
    <div class="doctor-column-head"><span>决策解释</span><small>{{ summary?.rule_version || '规则版本' }}</small></div>
    <div v-if="!explanation" class="doctor-empty">选择一条问诊后查看判断依据。</div>
    <template v-else>
      <section class="decision-score-card" aria-label="诊前资料就绪度">
        <small>诊前资料就绪度</small>
        <h3>{{ readinessTitle }}</h3>
        <p>{{ readinessDescription }}</p>
        <div class="readiness-grid">
          <div><span>核心诊前资料</span><strong>{{ readiness.core?.completed ?? 0 }}/{{ readiness.core?.total ?? 0 }}</strong></div>
          <div><span>安全资料</span><strong>{{ readiness.safety?.completed ?? 0 }}/{{ readiness.safety?.total ?? 0 }}</strong></div>
          <div><span>核心未解决冲突</span><strong>{{ readiness.core_conflicts ?? 0 }} 项</strong></div>
          <div><span>诊中建议补充</span><strong>{{ readiness.optional_keys?.length ?? 0 }} 项</strong></div>
        </div>
        <p class="readiness-baseline">基础测量：{{ readiness.baseline_ready ? '已确认' : '待确认' }}</p>
      </section>
      <section class="decision-block">
        <small>{{ explanation.stop.should_stop ? '停止判断' : '当前判断' }}</small>
        <h3>{{ explanation.stop.should_stop ? '停止继续追问' : '继续补充信息' }}</h3>
        <p>{{ explanation.stop.reason }}</p>
      </section>
      <section v-if="explanation.selected_field" class="decision-block accent">
        <small>下一项追问来源</small>
        <h3>{{ explanation.selected_field.label }}</h3>
        <p>{{ explanation.selected_field.reason }}</p>
        <dl><div><dt>优先级</dt><dd>{{ explanation.selected_field.priority ?? '—' }}</dd></div><div><dt>已尝试</dt><dd>{{ explanation.selected_field.attempts }} 次</dd></div></dl>
      </section>
      <section class="decision-block">
        <small>关键缺口</small>
        <p v-if="!readiness.blocking_keys?.length">没有未解决的核心缺口</p>
        <div v-else class="decision-tags"><span v-for="key in readiness.blocking_keys" :key="key">{{ doctorFieldLabel(key) }}</span></div>
      </section>
      <section class="decision-block">
        <small>已覆盖的主要线索</small>
        <div v-if="decisionSummary.covered.length" class="decision-covered-list">
          <article v-for="item in decisionSummary.covered" :key="item.title">
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
          </article>
        </div>
        <p v-else>当前尚未形成可汇总的扩展线索。</p>
      </section>
      <section class="decision-block">
        <small>诊中建议补充</small>
        <p class="decision-helper">以下资料可由医生结合主诉在诊中按需确认。</p>
        <div v-if="decisionSummary.pending.length" class="decision-tags">
          <span v-for="item in decisionSummary.pending" :key="item">{{ item }}</span>
        </div>
        <p v-else>当前无额外诊中补充项。</p>
      </section>
      <section class="decision-block">
        <small>安全提醒</small>
        <p v-if="!summary?.safety_alerts?.length">当前未记录危险信号</p>
        <div v-else class="decision-tags"><span v-for="item in summary.safety_alerts" :key="item">{{ item }}</span></div>
      </section>
      <section class="decision-block">
        <small>检查建议</small>
        <p v-if="summary?.safety_alerts?.length" class="decision-safety-copy">已记录危险信号，请医生优先进行线下安全评估；系统不自动生成常规检查方案。</p>
        <p v-else-if="!summary?.recommended_exams?.length">当前资料下暂无自动生成的检查候选，最终由医生结合诊中情况决定。</p>
        <div v-else class="decision-exam-list">
          <article v-for="exam in summary.recommended_exams" :key="exam.name">
            <strong>{{ exam.name }}</strong><p>{{ exam.reason }}</p>
          </article>
        </div>
      </section>
    </template>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { buildDoctorDecisionSummary, doctorFieldLabel } from '../doctor-decision-summary.js'

const props = defineProps({ explanation: Object, summary: Object })
const readiness = computed(() => props.summary?.readiness_summary || props.explanation?.readiness || {})
const decisionSummary = computed(() => buildDoctorDecisionSummary(props.summary?.field_groups || {}, readiness.value.optional_keys || []))
const readinessTitle = computed(() => {
  if (readiness.value.status === 'escalated') return '需优先线下评估'
  if (readiness.value.status === 'needs_doctor') return '诊中仍需补充核心资料'
  if (readiness.value.status === 'ready') return props.explanation?.stop?.should_stop ? '可以停止在线追问' : '已满足结束条件'
  return '继续在线追问'
})
const readinessDescription = computed(() => {
  if (readiness.value.status === 'escalated') return '已记录需优先处理的安全情况，请医生先评估。'
  if (readiness.value.status === 'needs_doctor') return '在线问诊已经结束，核心资料仍有缺口，请医生诊中核对。'
  if (readiness.value.status === 'ready') return '核心与安全资料已就绪；其他扩展资料可在诊中补充。'
  return '尚有核心资料待确认，继续在线追问。'
})
</script>
