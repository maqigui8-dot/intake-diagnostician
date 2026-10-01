export function isDoctorView(search = '') {
  return new URLSearchParams(search).get('view') === 'doctor'
}

const STOP_LABELS = {
  core_information_ready: '核心资料已就绪',
  threshold_reached: '历史规则结束，需核对资料就绪度',
  red_flag_escalation: '发现危险信号，已建议线下就医',
  patient_unavailable: '患者无法继续提供关键资料',
  safety_limit: '历史问诊保护性结束',
  duplicate_gap: '同一缺口已达到询问上限',
  no_collectable_gap: '没有可继续在线采集的缺口',
  ai_unavailable: '智能提取不可用，已完成固定安全采集',
  manual_completion: '人工结束并生成档案',
  manual_incomplete: '资料未就绪，已保存供医生补充',
  threshold_recheck_incomplete: '重新校验后仍有核心资料缺口',
}

export function formatStopReason(reason) {
  return STOP_LABELS[reason] || '问诊进行中'
}

export function scoreTone(score, threshold) {
  if (score >= threshold) return 'good'
  if (score >= threshold * 0.7) return 'warning'
  return 'low'
}
