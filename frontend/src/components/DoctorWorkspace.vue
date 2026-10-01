<template>
  <main class="doctor-page">
    <header class="doctor-topbar">
      <div><a href="/" class="doctor-back">中医智能助手</a><span class="doctor-title-divider"></span><strong>医生工作台</strong></div>
      <div><span class="demo-badge">演示环境 · 只读</span></div>
    </header>
    <div v-if="error" class="doctor-global-error">{{ error }}</div>
    <div v-else class="doctor-workspace-grid">
      <DoctorPatientList :patients="patients" :selected-patient-id="selectedPatientId" @select="selectPatient" />
      <DoctorPatientDetail :patient="patient" :sessions="sessions" :selected-session-id="selectedSessionId" :summary="summary" @select-session="selectSession" />
      <DecisionExplanationPanel :explanation="summary?.decision_explanation" :summary="summary" />
    </div>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { request } from '../api.js'
import DoctorPatientList from './DoctorPatientList.vue'
import DoctorPatientDetail from './DoctorPatientDetail.vue'
import DecisionExplanationPanel from './DecisionExplanationPanel.vue'

const patients = ref([]), patient = ref(null), sessions = ref([]), summary = ref(null)
const selectedPatientId = ref(''), selectedSessionId = ref(''), error = ref('')

async function selectSession(sessionId) {
  selectedSessionId.value = sessionId
  summary.value = sessionId ? await request(`/api/doctor/sessions/${sessionId}/summary`) : null
}
async function selectPatient(patientId) {
  selectedPatientId.value = patientId; selectedSessionId.value = ''; summary.value = null
  patient.value = await request(`/api/doctor/patients/${patientId}`)
  sessions.value = patient.value.sessions || []
  if (sessions.value[0]) await selectSession(sessions.value[0].session_id)
}
onMounted(async () => {
  try {
    patients.value = await request('/api/doctor/patients')
    const first = patients.value.find((item) => item.latest_intake_at) || patients.value[0]
    if (first) await selectPatient(first.patient_id)
  } catch (cause) { error.value = cause.message }
})
</script>
