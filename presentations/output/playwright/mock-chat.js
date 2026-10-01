async page => {
  const question = {
    id: 'chief_complaint',
    topic: '主要症状',
    field: 'chief_complaint',
    stage: 'guide',
    question: '您目前最主要的不适是什么？',
    hint: '先了解最困扰您的症状。',
    options: [
      { id: 'stomach', label: '胃胀、反酸' },
      { id: 'fatigue', label: '乏力、没精神' },
    ],
  }
  const stages = [
    { id: 'guide', label: '导诊', status: 'completed' },
    { id: 'pre_intake', label: '预问诊', status: 'completed' },
    { id: 'confirm', label: '信息确认', status: 'completed' },
    { id: 'suggestion', label: '检查建议', status: 'current' },
  ]
  const base = {
    session_id: 'qa',
    current_index: 0,
    current_question: question,
    questions: [{ ...question, status: 'current', number: 1 }],
    answers: {},
    follow_up_answers: [],
    follow_up_count: 12,
    summary: {},
    progress: { answered: 0, total: 1, percent: 0 },
    is_complete: false,
    report_markdown: null,
    stages,
    assistant_note: '我会按照中医十问歌，陪您一步步把情况说清楚。',
  }

  await page.unroute('**/api/intake/session/**')
  await page.route('**/api/intake/session/**', async route => {
    const path = route.request().url().split('?')[0]
    if (path.endsWith('/analyze')) {
      return route.fulfill({
        json: {
          status: 'completed',
          completeness_status: 'needs_follow_up',
          follow_up_questions: ['您说胃胀反酸已有一段时间，请问通常是饭前明显，还是饭后更明显？'],
          recommended_exams: [{
            name: '腹部超声',
            type: '仪器检查',
            department: '消化科',
            priority: 'routine',
            reason: '帮助了解腹部脏器情况',
            precautions: '是否需要检查由医生结合实际情况决定',
          }],
          safety_alerts: [],
          disclaimer: '以上内容仅供医生参考，不能替代线下诊断。',
        },
      })
    }
    if (path.endsWith('/complete')) {
      return route.fulfill({
        json: {
          ...base,
          is_complete: true,
          progress: { answered: 1, total: 1, percent: 100 },
          summary: { 主要症状: '胃胀、反酸' },
          answers: { chief_complaint: { option_id: 'stomach', label: '胃胀、反酸', note: '' } },
          report_markdown: '## 诊前信息\n\n- 主要症状：胃胀、反酸',
        },
      })
    }
    if (path.endsWith('/answer')) {
      return route.fulfill({
        json: {
          ...base,
          progress: { answered: 1, total: 1, percent: 100 },
          answers: { chief_complaint: { option_id: 'stomach', label: '胃胀、反酸', note: '' } },
        },
      })
    }
    return route.fulfill({ json: base })
  })
  await page.reload()
}
