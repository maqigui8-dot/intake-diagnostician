<template>
  <aside class="doctor-patient-column">
    <div class="doctor-column-head"><span>患者目录</span><small>{{ patients.length }} 人</small></div>
    <button
      v-for="patient in patients"
      :key="patient.patient_id"
      type="button"
      :class="['doctor-patient-item', { active: patient.patient_id === selectedPatientId }]"
      @click="$emit('select', patient.patient_id)"
    >
      <span class="doctor-list-avatar">{{ patient.display_name.slice(0, 1) }}</span>
      <span class="doctor-list-copy">
        <strong>{{ patient.display_name }}</strong>
        <small>{{ patient.record_count }} 份档案 · {{ patient.unfinished_count }} 个进行中</small>
      </span>
      <i v-if="patient.has_safety_alert" title="存在安全提示"></i>
    </button>
  </aside>
</template>

<script setup>
defineProps({ patients: { type: Array, default: () => [] }, selectedPatientId: { type: String, default: '' } })
defineEmits(['select'])
</script>
