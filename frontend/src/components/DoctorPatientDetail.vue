<template>
  <section class="doctor-detail-column">
    <div v-if="patient" class="doctor-profile">
      <span class="section-label">患者资料</span>
      <h2>{{ patient.display_name }}</h2>
      <p>共 {{ sessions.length }} 次问诊，选择一条记录查看资料就绪度与停止依据。</p>
    </div>
    <div v-if="!sessions.length" class="doctor-empty">该患者还没有问诊记录。</div>
    <div v-else class="doctor-session-list">
      <button
        v-for="session in sessions"
        :key="session.session_id"
        type="button"
        :class="['doctor-session-item', { active: session.session_id === selectedSessionId }]"
        @click="$emit('select-session', session.session_id)"
      >
        <span><strong>{{ phaseLabel(session.phase) }}</strong><small>{{ formatTime(session.updated_at) }}</small></span>
        <span>第 {{ session.turn || 0 }} 轮 →</span>
      </button>
    </div>
    <section v-if="summary" class="doctor-record-body">
      <div class="doctor-baseline-grid">
        <div><small>年龄</small><strong>{{ summary.baseline_assessment?.age ?? '—' }}</strong></div>
        <div><small>BMI</small><strong>{{ summary.baseline_assessment?.bmi ?? '—' }}</strong></div>
        <div><small>追问轮次</small><strong>{{ summary.follow_up_answers?.length || 0 }}</strong></div>
      </div>
      <div class="doctor-concern"><small>患者主要描述</small><p>{{ summary.open_answer || '尚未填写开放描述' }}</p></div>
      <div v-if="summary.follow_up_answers?.length" class="doctor-answer-list">
        <article v-for="(item, index) in summary.follow_up_answers" :key="index">
          <strong>{{ item.question }}</strong><p>{{ item.answer }}</p>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup>
defineProps({ patient: Object, sessions: { type: Array, default: () => [] }, selectedSessionId: String, summary: Object })
defineEmits(['select-session'])
const phaseLabel = (phase) => ({ baseline_collection: '基础资料', open_intake: '开放描述', processing: '信息整理', follow_up: '补充追问', completed: '已完成', incomplete: '待医生补充', escalated: '优先处理' }[phase] || '问诊记录')
const formatTime = (value) => value ? new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
</script>
