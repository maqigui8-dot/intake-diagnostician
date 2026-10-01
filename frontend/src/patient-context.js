export const DEMO_PATIENTS = [
  { patient_id: 'patient-zhang', display_name: '张女士' },
  { patient_id: 'patient-ma', display_name: '马先生' },
  { patient_id: 'patient-li', display_name: '李女士' },
]

export function readPatientId(search = window.location.search) {
  return new URLSearchParams(search).get('patient') || ''
}

export function readPatientEntryId(search = window.location.search) {
  return new URLSearchParams(search).get('view') === 'doctor' ? '' : readPatientId(search)
}

export function patientUrl(patientId) {
  return `/?patient=${encodeURIComponent(patientId)}`
}

export function patientName(patientId) {
  return DEMO_PATIENTS.find((item) => item.patient_id === patientId)?.display_name || '演示患者'
}
