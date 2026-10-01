export function getIntakeViewStage({ state, loading = false, saving = false } = {}) {
  if (!state || loading) return 'analyzing'
  if (state.phase === 'baseline_collection') return 'baseline_collection'
  if (state.phase === 'processing' || (saving && state.phase === 'follow_up')) return 'analyzing'
  if (state.phase === 'open_intake') return 'open_intake'
  if (state.phase === 'follow_up') return 'follow_up_chat'
  if (state.phase === 'escalated') return 'escalated'
  if (state.phase === 'completed' || state.phase === 'incomplete') return 'result'
  return 'analyzing'
}

export function canSaveIntakeRecord({ state, saved = false, saving = false } = {}) {
  if (!state || saved || saving) return false
  return state.phase === 'completed'
}

export function canContinueIntake({ state, saving = false } = {}) {
  return !!state && state.phase === 'incomplete' && state.can_continue === true && !saving
}

export function shouldAutoSaveIntakeRecord({ state, saved = false, saving = false } = {}) {
  return false
}
