<template>
  <main class="identity-page">
    <section class="identity-card">
      <span class="demo-badge">演示环境</span>
      <p class="identity-kicker">中医智能助手</p>
      <h1>选择演示患者</h1>
      <p class="identity-copy">选择一位演示患者，体验问诊、继续补充和查看已保存档案。</p>
      <div class="identity-patient-grid">
        <a v-for="patient in patients" :key="patient.patient_id" :href="patientUrl(patient.patient_id)" class="identity-option">
          <span class="identity-avatar">{{ patient.display_name.slice(0, 1) }}</span>
          <span><strong>{{ patient.display_name }}</strong><small>进入患者端</small></span>
        </a>
      </div>
      <p class="identity-notice">当前为功能演示，不代表正式账号与医疗授权系统。</p>
    </section>
  </main>
</template>

<script setup>
import { DEMO_PATIENTS, patientUrl } from '../patient-context.js'
const patients = DEMO_PATIENTS
</script>
