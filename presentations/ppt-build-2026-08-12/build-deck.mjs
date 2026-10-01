import fs from 'node:fs/promises'
import path from 'node:path'
import { Presentation, PresentationFile } from '@oai/artifact-tool'

const ROOT = 'C:/Users/Administrator/Desktop/project/intake-diagnostician'
const OUT_DIR = path.join(ROOT, 'ppt-build-2026-08-12', 'rendered')
const FINAL = path.join(ROOT, 'ppt-output', '中医诊前问诊系统-对话式追问与动态判断-2026-08-12.pptx')

const C = {
  bg: '#F7F9F5',
  bg2: '#EAF2E8',
  white: '#FFFFFF',
  green: '#2F6B4F',
  green2: '#4C8C7A',
  mint: '#DDEDE0',
  gold: '#D6A84B',
  ink: '#1F2A24',
  muted: '#657269',
  line: '#DCE5DC',
  red: '#B86155',
}

const FONT = 'Microsoft YaHei'

async function bytes(file) {
  const value = await fs.readFile(file)
  return value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength)
}

function shape(slide, geometry, position, fill = C.white, lineFill = C.line, radius = 'rounded-xl') {
  return slide.shapes.add({
    geometry,
    position,
    fill,
    line: { style: 'solid', fill: lineFill, width: lineFill === 'none' ? 0 : 1 },
    ...(geometry === 'roundRect' ? { borderRadius: radius } : {}),
  })
}

function text(slide, value, position, options = {}) {
  const box = slide.shapes.add({
    geometry: 'textbox',
    position,
    fill: 'none',
    line: { style: 'solid', fill: 'none', width: 0 },
  })
  box.text = value
  box.text.style = {
    fontSize: options.fontSize ?? 22,
    typeface: FONT,
    color: options.color ?? C.ink,
    bold: options.bold ?? false,
    alignment: options.alignment ?? 'left',
    verticalAlignment: options.verticalAlignment ?? 'top',
    autoFit: 'shrinkText',
    wrap: 'square',
    insets: options.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  }
  return box
}

function rule(slide, left, top, width, height = 2, fill = C.line) {
  return shape(slide, 'rect', { left, top, width, height }, fill, 'none')
}

function addHeader(slide, title, section, page) {
  text(slide, section, { left: 72, top: 46, width: 220, height: 24 }, { fontSize: 16, bold: true, color: C.green2 })
  text(slide, title, { left: 72, top: 82, width: 1040, height: 68 }, { fontSize: 48, bold: true })
  text(slide, String(page).padStart(2, '0'), { left: 1160, top: 50, width: 48, height: 24 }, { fontSize: 16, bold: true, color: C.muted, alignment: 'right' })
  rule(slide, 72, 158, 1136, 2, C.line)
}

function addFooter(slide, label = '中医诊前问诊系统') {
  text(slide, label, { left: 72, top: 681, width: 420, height: 18 }, { fontSize: 13, color: C.muted })
}

function addNotes(slide, script, sources) {
  const notes = `${script}\n\n[Sources]\n${sources.map((item) => `- ${item}`).join('\n')}\n[/Sources]`
  slide.speakerNotes.textFrame.setText(notes)
  slide.speakerNotes.setVisible(true)
}

function addArrow(slide, left, top, width = 48, height = 34, fill = C.green2) {
  return shape(slide, 'chevron', { left, top, width, height }, fill, 'none')
}

function addStep(slide, number, title, body, left, top, width, fill = C.white) {
  shape(slide, 'roundRect', { left, top, width, height: 142 }, fill, C.line)
  shape(slide, 'ellipse', { left: left + 18, top: top + 18, width: 38, height: 38 }, C.green, 'none')
  text(slide, String(number), { left: left + 18, top: top + 24, width: 38, height: 25 }, { fontSize: 18, bold: true, color: C.white, alignment: 'center' })
  text(slide, title, { left: left + 70, top: top + 18, width: width - 88, height: 34 }, { fontSize: 25, bold: true })
  text(slide, body, { left: left + 18, top: top + 70, width: width - 36, height: 56 }, { fontSize: 18, color: C.muted })
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true })
  await fs.mkdir(path.dirname(FINAL), { recursive: true })

  const home = await bytes(path.join(ROOT, 'output/playwright/project-home-current.png'))
  const mobile = await bytes(path.join(ROOT, 'output/playwright/dynamic-follow-up-mobile-13.png'))
  const before = await bytes(path.join(ROOT, 'output/playwright/follow-up-desktop.png'))
  const after = await bytes(path.join(ROOT, 'output/playwright/dynamic-follow-up-13.png'))

  const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } })

  // Slide 1
  {
    const slide = deck.slides.add()
    slide.background.fill = C.bg
    rule(slide, 0, 0, 18, 720, C.green)
    text(slide, '阶段进展 · 2026.08.12', { left: 74, top: 72, width: 320, height: 30 }, { fontSize: 18, bold: true, color: C.green2 })
    text(slide, '中医诊前问诊系统\n阶段进展', { left: 74, top: 132, width: 510, height: 160 }, { fontSize: 68, bold: true })
    text(slide, '对话式追问与动态完整度判断', { left: 76, top: 324, width: 500, height: 45 }, { fontSize: 30, color: C.green })
    rule(slide, 76, 396, 116, 4, C.gold)
    text(slide, '对话式追问  ·  动态结束规则  ·  两个 Skill 协作', { left: 76, top: 430, width: 520, height: 56 }, { fontSize: 20, color: C.muted })
    shape(slide, 'roundRect', { left: 646, top: 70, width: 558, height: 520 }, C.white, C.line, 'rounded-2xl')
    slide.images.add({ blob: home, contentType: 'image/png', alt: '中医诊前问诊系统首页', fit: 'cover', position: { left: 666, top: 90, width: 518, height: 480 }, geometry: 'roundRect', borderRadius: 'rounded-xl' })
    text(slide, '汇报重点：系统如何在不固定轮次的前提下，把诊前信息逐步问完整。', { left: 74, top: 620, width: 1120, height: 34 }, { fontSize: 20, color: C.muted })
    addNotes(slide, '本次汇报聚焦今天完成的两项改造。第一，补充问诊从分析面板调整为连续对话；第二，追问不再固定五轮，而是每轮根据当前资料是否足够决定继续或结束。', [
      `${ROOT}/docs/superpowers/specs/2026-08-12-conversational-follow-up-design.md`,
      `${ROOT}/docs/superpowers/specs/2026-08-12-dynamic-follow-up-completion-design.md`,
      `${ROOT}/output/playwright/project-home-current.png`,
    ])
  }

  // Slide 2
  {
    const slide = deck.slides.add()
    slide.background.fill = C.bg
    addHeader(slide, '固定五轮会提前截断，也可能造成无效追问', '01 · 改造背景', 2)
    text(slide, '5', { left: 92, top: 210, width: 210, height: 210 }, { fontSize: 168, bold: true, color: C.red, alignment: 'center' })
    rule(slide, 116, 318, 170, 8, C.red)
    text(slide, '固定轮次', { left: 100, top: 430, width: 190, height: 42 }, { fontSize: 28, bold: true, color: C.red, alignment: 'center' })
    rule(slide, 350, 198, 2, 390, C.line)
    text(slide, '问题不在“问几次”', { left: 414, top: 208, width: 630, height: 42 }, { fontSize: 32, bold: true, color: C.green })
    text(slide, '信息复杂时', { left: 414, top: 294, width: 180, height: 34 }, { fontSize: 24, bold: true })
    text(slide, '五次可能仍不足，流程却被迫结束。', { left: 620, top: 294, width: 500, height: 38 }, { fontSize: 22, color: C.muted })
    rule(slide, 414, 350, 700, 1, C.line)
    text(slide, '信息简单时', { left: 414, top: 386, width: 180, height: 34 }, { fontSize: 24, bold: true })
    text(slide, '为了凑轮次继续询问，会增加用户负担。', { left: 620, top: 386, width: 500, height: 38 }, { fontSize: 22, color: C.muted })
    shape(slide, 'roundRect', { left: 414, top: 486, width: 700, height: 92 }, C.bg2, 'none')
    text(slide, '新的结束条件：当前信息是否足以支持\n后续诊中判断和开方前准备', { left: 446, top: 501, width: 640, height: 66 }, { fontSize: 24, bold: true, color: C.green })
    addFooter(slide)
    addNotes(slide, '原来的五轮限制只是工程上的固定阈值，并不能代表诊前资料已经够用。今天把结束条件重新定义为信息完整度：复杂情况可以继续问，简单情况在信息足够时及时结束。', [
      `${ROOT}/docs/superpowers/specs/2026-08-12-dynamic-follow-up-completion-design.md`,
      `${ROOT}/backend/intake_flow.py`,
    ])
  }

  // Slide 3
  {
    const slide = deck.slides.add()
    slide.background.fill = C.bg
    addHeader(slide, '追问从“分析面板”变成自然对话', '02 · 交互升级', 3)
    text(slide, '每轮只问一个问题', { left: 82, top: 214, width: 460, height: 44 }, { fontSize: 31, bold: true, color: C.green })
    text(slide, '问题以“小郎中”的口吻承接患者上一轮回答，患者直接在输入框中自由描述。', { left: 82, top: 280, width: 470, height: 92 }, { fontSize: 22, color: C.muted })
    const bullets = [
      ['问答历史保留', '患者能看清上下文'],
      ['回答后重新整理', '系统再决定下一问'],
      ['内部字段隐藏', '不展示缺失项清单'],
    ]
    bullets.forEach(([head, body], index) => {
      const y = 410 + index * 68
      shape(slide, 'ellipse', { left: 84, top: y + 5, width: 24, height: 24 }, C.green2, 'none')
      text(slide, '✓', { left: 84, top: y + 6, width: 24, height: 20 }, { fontSize: 15, bold: true, color: C.white, alignment: 'center' })
      text(slide, head, { left: 124, top: y, width: 170, height: 30 }, { fontSize: 21, bold: true })
      text(slide, body, { left: 294, top: y + 1, width: 250, height: 30 }, { fontSize: 19, color: C.muted })
    })
    shape(slide, 'roundRect', { left: 676, top: 190, width: 376, height: 452 }, C.white, C.line, 'rounded-2xl')
    slide.images.add({ blob: mobile, contentType: 'image/png', alt: '手机端对话式追问页面', fit: 'contain', position: { left: 702, top: 208, width: 324, height: 416 } })
    text(slide, '手机端单列布局', { left: 1054, top: 250, width: 150, height: 66 }, { fontSize: 22, bold: true, color: C.green, alignment: 'center' })
    text(slide, '流程侧栏自动隐藏\n输入区独占整行', { left: 1050, top: 338, width: 160, height: 90 }, { fontSize: 18, color: C.muted, alignment: 'center' })
    addFooter(slide)
    addNotes(slide, '交互层面不再把追问放在信息完整度报告下面，而是进入独立聊天界面。系统一次只问一个问题，保留历史问答，并隐藏缺失必问项、建议选问项等内部判断。手机端也改为单列布局。', [
      `${ROOT}/frontend/src/App.vue`,
      `${ROOT}/frontend/src/style.css`,
      `${ROOT}/output/playwright/dynamic-follow-up-mobile-13.png`,
    ])
  }

  // Slide 4
  {
    const slide = deck.slides.add()
    slide.background.fill = C.bg
    addHeader(slide, '每次回答后重新判断，信息足够才结束', '03 · 动态规则', 4)
    const y = 286
    addStep(slide, 1, '患者回答', '记录当前问题与回答', 72, y, 220, C.white)
    addArrow(slide, 306, y + 54)
    addStep(slide, 2, '完整度检查', '结合十问歌与主诉判断', 366, y, 244, C.bg2)
    addArrow(slide, 624, y + 54)
    shape(slide, 'diamond', { left: 690, top: y - 4, width: 160, height: 150 }, C.white, C.green)
    text(slide, '信息\n足够？', { left: 714, top: y + 39, width: 112, height: 70 }, { fontSize: 26, bold: true, color: C.green, alignment: 'center', verticalAlignment: 'middle' })
    addArrow(slide, 864, y + 54, 48, 34, C.green)
    addStep(slide, 3, '形成结果', '输出档案与检查建议', 930, y, 278, C.white)
    text(slide, '是', { left: 854, top: y + 16, width: 64, height: 24 }, { fontSize: 18, bold: true, color: C.green, alignment: 'center' })
    rule(slide, 770, 444, 2, 90, C.gold)
    rule(slide, 504, 532, 268, 2, C.gold)
    addArrow(slide, 450, 516, 50, 34, C.gold)
    text(slide, '否：生成一个最关键、且不重复的问题，再进入下一轮', { left: 498, top: 548, width: 570, height: 38 }, { fontSize: 21, bold: true, color: C.gold })
    shape(slide, 'roundRect', { left: 256, top: 190, width: 768, height: 54 }, C.mint, 'none')
    text(slide, '追问次数只用于显示“第 N 问”，不再参与结束判断。', { left: 284, top: 202, width: 712, height: 32 }, { fontSize: 22, bold: true, color: C.green, alignment: 'center' })
    addFooter(slide)
    addNotes(slide, '新的规则是一个循环。患者每回答一次，系统立即重新检查资料。信息不足时只生成一个最重要的问题；信息足够时才进入档案和检查建议。因此追问次数只用于历史记录和页面显示。', [
      `${ROOT}/frontend/src/follow-up-stage.js`,
      `${ROOT}/backend/skill_analysis.py`,
      `${ROOT}/docs/superpowers/specs/2026-08-12-dynamic-follow-up-completion-design.md`,
    ])
  }

  // Slide 5
  {
    const slide = deck.slides.add()
    slide.background.fill = C.bg
    addHeader(slide, '两个 Skill 分工：一个判断问什么，一个控制怎么问', '04 · Skill 协作', 5)
    shape(slide, 'roundRect', { left: 78, top: 210, width: 460, height: 352 }, C.white, C.line, 'rounded-2xl')
    text(slide, '01', { left: 106, top: 238, width: 60, height: 34 }, { fontSize: 26, bold: true, color: C.gold })
    text(slide, '完整度检查 Skill', { left: 106, top: 282, width: 340, height: 42 }, { fontSize: 30, bold: true, color: C.green })
    text(slide, 'tcm-intake-checklist', { left: 106, top: 330, width: 320, height: 28 }, { fontSize: 17, color: C.muted })
    text(slide, '• 检查基础必问项\n• 按主诉选择条件选问项\n• 决定资料是否够用\n• 选出当前最关键缺口', { left: 106, top: 388, width: 360, height: 138 }, { fontSize: 21, color: C.ink })
    shape(slide, 'roundRect', { left: 742, top: 210, width: 460, height: 352 }, C.white, C.line, 'rounded-2xl')
    text(slide, '02', { left: 770, top: 238, width: 60, height: 34 }, { fontSize: 26, bold: true, color: C.gold })
    text(slide, '追问表达 Skill', { left: 770, top: 282, width: 340, height: 42 }, { fontSize: 30, bold: true, color: C.green2 })
    text(slide, 'tcm-questioning-guide', { left: 770, top: 330, width: 340, height: 28 }, { fontSize: 17, color: C.muted })
    text(slide, '• 每轮只问一个信息点\n• 使用患者能理解的语言\n• 承接已有回答，不重复追问\n• 危险信号优先提示就医', { left: 770, top: 388, width: 370, height: 138 }, { fontSize: 21, color: C.ink })
    addArrow(slide, 584, 338, 112, 58, C.green2)
    text(slide, '结构化缺口', { left: 568, top: 414, width: 144, height: 32 }, { fontSize: 17, bold: true, color: C.muted, alignment: 'center' })
    shape(slide, 'roundRect', { left: 318, top: 600, width: 644, height: 48 }, C.bg2, 'none')
    text(slide, '完整度 Skill 负责决策，追问 Skill 负责表达。', { left: 340, top: 610, width: 600, height: 30 }, { fontSize: 22, bold: true, color: C.green, alignment: 'center' })
    addFooter(slide)
    addNotes(slide, '两个 Skill 的职责保持分离。完整度检查 Skill 决定还缺什么、是否可以结束；追问表达 Skill 把一个缺口转换成自然问题。这样能够单独维护规则，也避免模型同时承担过多职责。', [
      `${ROOT}/backend/skills/tcm-intake-checklist/SKILL.md`,
      `${ROOT}/backend/skills/tcm-questioning-guide/SKILL.md`,
      `${ROOT}/backend/agent.py`,
    ])
  }

  // Slide 6
  {
    const slide = deck.slides.add()
    slide.background.fill = C.bg
    addHeader(slide, '改造后，第 13 问仍能继续', '05 · 改造前后', 6)
    text(slide, '改造前', { left: 84, top: 188, width: 180, height: 34 }, { fontSize: 25, bold: true, color: C.red })
    text(slide, '固定显示 1 / 5', { left: 260, top: 192, width: 240, height: 28 }, { fontSize: 18, color: C.muted, alignment: 'right' })
    shape(slide, 'roundRect', { left: 78, top: 232, width: 526, height: 366 }, C.white, C.line, 'rounded-xl')
    slide.images.add({ blob: before, contentType: 'image/png', alt: '改造前固定五轮追问页面', fit: 'contain', position: { left: 90, top: 244, width: 502, height: 342 }, geometry: 'roundRect', borderRadius: 'rounded-lg' })
    text(slide, '改造后', { left: 674, top: 188, width: 180, height: 34 }, { fontSize: 25, bold: true, color: C.green })
    text(slide, '只显示第 13 问', { left: 850, top: 192, width: 330, height: 28 }, { fontSize: 18, color: C.muted, alignment: 'right' })
    shape(slide, 'roundRect', { left: 668, top: 232, width: 526, height: 366 }, C.white, C.green, 'rounded-xl')
    slide.images.add({ blob: after, contentType: 'image/png', alt: '改造后第十三问仍可继续的页面', fit: 'contain', position: { left: 680, top: 244, width: 502, height: 342 }, geometry: 'roundRect', borderRadius: 'rounded-lg' })
    text(slide, '接口实测：第 6 次提交成功', { left: 92, top: 624, width: 330, height: 28 }, { fontSize: 18, bold: true, color: C.green2 })
    text(slide, '浏览器实测：第 13 问仍可回答', { left: 454, top: 624, width: 370, height: 28 }, { fontSize: 18, bold: true, color: C.green2 })
    text(slide, '自动验证：前端 14 项 / 后端 23 项通过', { left: 844, top: 624, width: 360, height: 28 }, { fontSize: 18, bold: true, color: C.green2, alignment: 'right' })
    addFooter(slide)
    addNotes(slide, '这一页展示实际改造效果。左侧旧页面把追问固定为五轮；右侧新页面在第十三问时仍然保留输入框。接口也已连续提交六次成功，同时前端十四项、后端二十三项测试全部通过。', [
      `${ROOT}/output/playwright/follow-up-desktop.png`,
      `${ROOT}/output/playwright/dynamic-follow-up-13.png`,
      `${ROOT}/frontend/tests/follow-up-stage.test.mjs`,
      `${ROOT}/backend/tests/test_intake_flow.py`,
    ])
  }

  // Slide 7
  {
    const slide = deck.slides.add()
    slide.background.fill = C.bg
    addHeader(slide, '新流程形成可持续收敛的诊前信息闭环', '06 · 完整闭环', 7)
    const top = 270
    const width = 186
    const gap = 38
    const starts = [72, 72 + width + gap, 72 + (width + gap) * 2, 72 + (width + gap) * 3, 72 + (width + gap) * 4]
    const titles = ['基础问诊', '判断缺口', '自然追问', '重新判断', '形成结果']
    const bodies = ['采集主诉与十问歌基础信息', '确认最影响后续判断的一项', '一次只问一个问题', '回答进入档案后再次评估', '档案与推荐检查项目']
    starts.forEach((left, index) => {
      if (index < starts.length - 1) addArrow(slide, left + width + 2, top + 54, 34, 30, index === 3 ? C.gold : C.green2)
      shape(slide, 'roundRect', { left, top, width, height: 146 }, index === 4 ? C.bg2 : C.white, index === 4 ? C.green : C.line)
      text(slide, String(index + 1).padStart(2, '0'), { left: left + 18, top: top + 18, width: 42, height: 25 }, { fontSize: 17, bold: true, color: index === 4 ? C.green : C.gold })
      text(slide, titles[index], { left: left + 18, top: top + 52, width: width - 36, height: 35 }, { fontSize: 24, bold: true, color: index === 4 ? C.green : C.ink })
      text(slide, bodies[index], { left: left + 18, top: top + 94, width: width - 36, height: 42 }, { fontSize: 17, color: C.muted })
    })
    rule(slide, starts[3] + width / 2, top - 74, 2, 58, C.gold)
    rule(slide, starts[1] + width / 2, top - 74, starts[3] - starts[1], 2, C.gold)
    addArrow(slide, starts[1] + width / 2 - 50, top - 90, 50, 34, C.gold)
    text(slide, '信息不足：回到缺口判断，继续下一轮', { left: 430, top: 174, width: 440, height: 32 }, { fontSize: 20, bold: true, color: C.gold, alignment: 'center' })
    shape(slide, 'roundRect', { left: 196, top: 510, width: 888, height: 100 }, C.green, 'none', 'rounded-2xl')
    text(slide, '结束条件不是“已经问了几次”，\n而是“当前信息是否足够”。', { left: 250, top: 530, width: 780, height: 62 }, { fontSize: 30, bold: true, color: C.white, alignment: 'center', verticalAlignment: 'middle' })
    addFooter(slide, '当前成果：对话式追问、动态完整度判断、双 Skill 协作均已落地')
    addNotes(slide, '当前流程已经形成闭环：基础问诊之后识别缺口，用追问 Skill 生成一个自然问题，患者回答后重新判断。信息不足就继续循环，信息足够才形成档案和检查建议。今天改造的核心结论，就是结束条件由信息本身决定。', [
      `${ROOT}/docs/superpowers/specs/2026-08-12-conversational-follow-up-design.md`,
      `${ROOT}/docs/superpowers/specs/2026-08-12-dynamic-follow-up-completion-design.md`,
      `${ROOT}/backend/skills/tcm-intake-checklist/SKILL.md`,
      `${ROOT}/backend/skills/tcm-questioning-guide/SKILL.md`,
    ])
  }

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, '0')}`
    const png = await deck.export({ slide, format: 'png', scale: 1 })
    await fs.writeFile(path.join(OUT_DIR, `${stem}.png`), new Uint8Array(await png.arrayBuffer()))
    const layout = await slide.export({ format: 'layout' })
    await fs.writeFile(path.join(OUT_DIR, `${stem}.layout.json`), await layout.text())
  }

  const montage = await deck.export({ format: 'webp', montage: true, scale: 1 })
  await fs.writeFile(path.join(OUT_DIR, 'montage.webp'), new Uint8Array(await montage.arrayBuffer()))

  const pptx = await PresentationFile.exportPptx(deck)
  await pptx.save(FINAL)
  console.log(FINAL)
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
