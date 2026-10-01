<template>
  <App v-if="patientId" :patient-id="patientId" />
  <IdentityChooser v-else />
</template>

<script setup>
import App from './App.vue'
import IdentityChooser from './components/IdentityChooser.vue'
import { readPatientEntryId } from './patient-context.js'

const patientId = readPatientEntryId()
</script>
