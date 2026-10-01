const SECTION_LABELS = {
  '肥胖病程与可能病因': '病程与风险',
  '相关疾病风险': '病程与风险',
  '生活方式与心理情况': '生活方式',
  '中医诊前资料': '中医诊前',
  '待医生确认': '用药与安全',
  '安全资料': '用药与安全',
}

const FIELD_LABELS = {
  main_goal: '主要诉求',
  height_weight: '身高与体重',
  waist: '腰围',
  weight_change: '体重变化',
  onset_course: '持续时间',
  related_factors: '相关因素',
  childhood_obesity: '儿童期体重情况',
  family_history: '家族史',
  previous_weight_management: '既往体重管理',
  appetite_thirst: '食欲与口渴',
  cold_heat_sweat: '寒热与出汗',
  stool_urine: '大便与小便',
  sleep_emotion: '睡眠与情绪',
  fatigue_activity: '疲乏与活动耐受',
  edema_heaviness: '浮肿与身体困重',
  chest_abdomen: '胸腹不适',
  tongue: '舌象',
  diet_pattern: '饮食习惯',
  exercise: '运动情况',
  sleep_schedule: '作息规律',
  stress_eating: '情绪性进食',
  smoking: '吸烟情况',
  alcohol: '饮酒情况',
  work_activity: '工作与日常活动',
  binge_eating: '失控进食情况',
  glucose_tests: '近期代谢检查',
  lipid_tests: '血脂检查',
  uric_acid_test: '尿酸检查',
  liver_tests: '肝功能检查',
  kidney_tests: '肾功能检查',
  thyroid_tests: '甲状腺检查',
  allergies: '过敏史',
  medications: '当前用药与保健品',
  important_history: '既往疾病',
  pregnancy: '妊娠与生育情况',
  red_flags: '危险信号',
}

function displayFieldLabel(field) {
  return FIELD_LABELS[field.field_key] || '其他资料'
}

export function doctorFieldLabel(key) {
  return key === 'baseline' ? '基础测量' : (FIELD_LABELS[key] || '其他资料')
}

function displaySectionLabel(section) {
  return SECTION_LABELS[section] || '其他资料'
}

export function buildDoctorDecisionSummary(fieldGroups = {}, optionalKeys = []) {
  const coveredMap = new Map()
  const pending = []
  const optionalSet = new Set(optionalKeys)

  for (const [section, fields] of Object.entries(fieldGroups || {})) {
    for (const field of fields || []) {
      const label = displayFieldLabel(field)
      if (field.status === 'confirmed' && field.evidence?.length) {
        const title = displaySectionLabel(section)
        const labels = coveredMap.get(title) || []
        if (!labels.includes(label)) labels.push(label)
        coveredMap.set(title, labels)
      } else if (
        ['not_asked', 'partial', 'unavailable'].includes(field.status)
        && optionalSet.has(field.field_key)
        && !pending.includes(label)
      ) {
        pending.push(label)
      }
    }
  }

  return {
    covered: [...coveredMap].map(([title, labels]) => ({ title, detail: labels.join('、') })),
    pending,
  }
}
