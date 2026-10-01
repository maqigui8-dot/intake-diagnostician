export function getIntakeViewStage({ state, loading = false, saving = false } = {}) {
  if (!state || loading) return 'analyzing'
  if (saving || state.phase === 'processing') return 'analyzing'
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
