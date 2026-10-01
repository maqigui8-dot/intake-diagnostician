import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir("ppt-output", { recursive: true });

  const presentation = Presentation.create({
    slideSize: { width: 1280, height: 720 },
  });

  const WHITE  = "white";
  const DARK   = "slate-800";
  const GRAY   = "slate-500";
  const LIGHT  = "slate-100";
  const ACCENT = "indigo-500";
  const TAG_BG = "indigo-50";

  // 辅助函数：画分隔线
  function divider(slide, top) {
    slide.shapes.add({
      geometry: "rect",
      position: { left: 72, top, width: 1136, height: 1 },
      fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });
  }

  // 辅助函数：画标题
  function title(slide, text, top = 48) {
    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: text, style: { fontSize: 34, bold: true, color: DARK } };
    divider(slide, top + 62);
  }

  // 辅助函数：画卡片
  function card(slide, x, y, w, h, body, label) {
    const shape = slide.shapes.add({
      geometry: "roundRect",
      position: { left: x, top: y, width: w, height: h },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-200", width: 1 },
      borderRadius: "rounded-lg",
    });
    shape.text = { value: body, style: { fontSize: 15, color: DARK } };
    if (label) {
      slide.shapes.add({
        geometry: "textbox",
        position: { left: x, top: y - 26, width: w, height: 24 },
        fill: "none",
        line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: label, style: { fontSize: 16, bold: true, color: ACCENT } };
    }
  }

  // ============================================================
  // SLIDE 1: 封面
  // ============================================================
  {
    const s = presentation.slides.add();
    s.background.fill = WHITE;

    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 180, width: 1136, height: 100 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "AI 老中医问诊 · 本周进展", style: { fontSize: 48, bold: true, color: DARK } };

    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 300, width: 1136, height: 56 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "前端风格焕新  ·  中医知识 Skill 体系", style: { fontSize: 28, color: GRAY } };

    s.shapes.add({
      geometry: "rect",
      position: { left: 72, top: 390, width: 100, height: 3 },
      fill: ACCENT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 430, width: 1136, height: 40 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "2026.07.22  ·  Deep Agents v4.0", style: { fontSize: 20, color: "slate-400" } };
  }

  // ============================================================
  // SLIDE 2: 本周概览
  // ============================================================
  {
    const s = presentation.slides.add();
    s.background.fill = WHITE;
    title(s, "本周概览");

    const rows = [
      ["维度", "进展"],
      ["前端",  "整体视觉风格升级：暖调古风 → 现代中式融合"],
      ["技能",  "新增 2 个中医 Skill：tcm-intake（问诊指南）+ tcm-zhengxing（辨证速查）"],
      ["架构",  "Deep Agents 框架稳定运行，4 个子智能体按需并行辨证"],
    ];

    s.tables.add({
      position: { left: 72, top: 150, width: 1136, height: 200 },
      rows,
      style: { headerRowFill: "slate-100", bodyRowFill: WHITE, fontSize: 18 },
    });
  }

  // ============================================================
  // SLIDE 3: 前端风格对比
  // ============================================================
  {
    const s = presentation.slides.add();
    s.background.fill = WHITE;
    title(s, "前端 · 风格对比");

    // Before
    card(s, 72, 140, 540, 320,
      "Before（旧版）\n\n" +
      "▸ 宣纸黄背景 (#F5F0E8)\n" +
      "▸ 居中单栏聊天\n" +
      "▸ 暖黄色聊天气泡\n" +
      "▸ 翠绿强调色 (#2E7D32)\n" +
      "▸ 全楷体字体\n" +
      "▸ 无侧边导航",
      "旧风格"
    );

    // After
    card(s, 668, 140, 540, 320,
      "After（新版）\n\n" +
      "▸ 薰衣草蓝白渐变背景\n" +
      "▸ 260px 左侧导航栏 + 主聊天区\n" +
      "▸ 白卡片 + 蓝灰边框气泡\n" +
      "▸ 薰衣草蓝强调色 (#6B7DB3)\n" +
      "▸ 标题楷体 + 正文系统无衬线\n" +
      "▸ 侧边栏功能导航 + 十问歌速览",
      "新风格"
    );

    // Arrow
    s.shapes.add({
      geometry: "textbox", position: { left: 590, top: 270, width: 100, height: 40 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "→", style: { fontSize: 36, bold: true, color: ACCENT } };

    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 500, width: 1136, height: 60 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = {
      value: "配色思路：保留楷体标题的中医辨识度，用薰衣草蓝 + 白色卡片营造干净现代的质感，侧边栏提升功能可见性",
      style: { fontSize: 16, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 4: 前端布局结构
  // ============================================================
  {
    const s = presentation.slides.add();
    s.background.fill = WHITE;
    title(s, "前端 · 新布局结构");

    // Layout diagram
    s.shapes.add({
      geometry: "roundRect",
      position: { left: 100, top: 150, width: 220, height: 480 },
      fill: "indigo-50",
      line: { style: "solid", fill: "slate-300", width: 1 },
      borderRadius: "rounded-lg",
    });

    s.shapes.add({
      geometry: "textbox", position: { left: 120, top: 170, width: 180, height: 440 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = {
      value: "侧边栏\n\n🍂 AI老中医\n中医诊前助手\n\n────────\n💬 开始问诊\n📋 问诊档案\nℹ️ 关于系统\n\n────────\n十问歌\n一问寒热二问汗\n三问头身四问便\n五问饮食六问胸\n七聋八渴俱当辨\n\n────────\n🟢 Deep Agents v4.0",
      style: { fontSize: 13, color: DARK }
    };

    // Right content
    s.shapes.add({
      geometry: "roundRect",
      position: { left: 350, top: 150, width: 858, height: 60 },
      fill: WHITE,
      line: { style: "solid", fill: "slate-200", width: 1 },
      borderRadius: "rounded-lg",
    });

    s.shapes.add({
      geometry: "textbox", position: { left: 370, top: 162, width: 818, height: 36 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "顶栏  🍂 小郎中问诊  [诊前采集]                                   🕐 实时问诊中", style: { fontSize: 14, color: DARK } };

    // Chat area
    s.shapes.add({
      geometry: "roundRect",
      position: { left: 350, top: 230, width: 858, height: 280 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-200", width: 1 },
      borderRadius: "rounded-lg",
    });

    s.shapes.add({
      geometry: "textbox", position: { left: 370, top: 250, width: 400, height: 100 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "🏺 助手消息\n白卡片 + 蓝灰细边框\n圆角左下小角标", style: { fontSize: 14, color: GRAY } };

    s.shapes.add({
      geometry: "textbox", position: { left: 720, top: 340, width: 400, height: 60 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "🌿 用户消息\n蓝紫渐变底 + 白色字\n圆角右下小角标  →", style: { fontSize: 14, color: GRAY, align: "right" } };

    // Input
    s.shapes.add({
      geometry: "roundRect",
      position: { left: 350, top: 530, width: 858, height: 56 },
      fill: WHITE,
      line: { style: "solid", fill: "slate-200", width: 1 },
      borderRadius: "rounded-lg",
    });

    s.shapes.add({
      geometry: "textbox", position: { left: 370, top: 542, width: 400, height: 32 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "✍️ 输入区  ·  蓝紫发送按钮", style: { fontSize: 14, color: GRAY } };

    // Bottom note
    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 620, width: 1136, height: 50 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = {
      value: "TailwindCSS + 内联样式 · Vue 3 Composition API · markdown-it 表格渲染 · fetch + Vite proxy 前后端通信",
      style: { fontSize: 15, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 5: Skill ① 十问歌深度问诊指南
  // ============================================================
  {
    const s = presentation.slides.add();
    s.background.fill = WHITE;
    title(s, "Skill ①  十问歌深度问诊指南");

    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 115, width: 600, height: 30 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "skills/tcm-intake/SKILL.md", style: { fontSize: 14, color: "slate-400" } };

    // 12 topics as small tags
    const tags = ["寒热", "汗出", "头身", "二便", "饮食", "胸腹", "睡眠", "口渴", "旧病", "病因", "经期", "舌象"];
    let tx = 72, ty = 160;
    for (let i = 0; i < tags.length; i++) {
      const tag = s.shapes.add({
        geometry: "roundRect",
        position: { left: tx, top: ty, width: 85, height: 32 },
        fill: TAG_BG,
        line: { style: "solid", fill: "slate-200", width: 1 },
        borderRadius: "rounded-full",
      });
      tag.text = { value: tags[i], style: { fontSize: 13, color: ACCENT } };
      tx += 96;
      if (tx > 600) { tx = 72; ty += 42; }
    }

    // Left: what's inside
    card(s, 72, 260, 540, 240,
      "每项追问结构\n\n" +
      "▸ 主问题：一句温和的提问\n" +
      "▸ 追问方向：3-6 个细分追问路径\n" +
      "  例：头痛 → 追问痛感/位置/持续时间/诱因\n" +
      "▸ 记录要点：该项需记录的关键信息\n\n" +
      "红旗信号（6 种需建议立即就医）\n" +
      "▸ 剧烈头痛伴呕吐 | 胸痛彻背 | 突然半身麻木\n" +
      "▸ 高热不退 | 剧烈腹痛拒按 | 呕血便血",
      "每个主题包含"
    );

    // Right: before/after example
    card(s, 668, 260, 540, 240,
      "Before（无 Skill）\n" +
      "\"好的，头疼我记下了。接下来你出汗多吗？\"\n" +
      "（跳下一题，无追问）\n\n" +
      "After（有 Skill 自动查阅）\n" +
      "\"这个头痛，是胀痛还是刺痛？两边太阳穴还是\n" +
      "后脑勺？每天什么时候最明显？有没有想吐？\"\n" +
      "（专业追问，信息密度大幅提升）",
      "效果对比"
    );

    // Stats
    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 540, width: 1136, height: 50 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = {
      value: "12 个追问维度  ·  60+ 细分追问方向  ·  6 种红旗信号  ·  按需加载，不占用启动上下文",
      style: { fontSize: 16, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 6: Skill ② 辨证速查表
  // ============================================================
  {
    const s = presentation.slides.add();
    s.background.fill = WHITE;
    title(s, "Skill ②  辨证速查表");

    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 115, width: 600, height: 30 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "skills/tcm-zhengxing/SKILL.md  ·  供 4 个子智能体并行分析时查阅", style: { fontSize: 14, color: "slate-400" } };

    const systems = [
      { name: "八纲辨证", count: "10+ 证型", items: "表里 · 寒热 · 虚实 · 阴阳", x: 72, y: 165 },
      { name: "脏腑辨证", count: "30+ 证型", items: "心系 · 肝系 · 脾系 · 肺系 · 肾系", x: 416, y: 165 },
      { name: "气血津液", count: "11 种病证", items: "气虚 · 气滞 · 血瘀 · 痰证 · 水停", x: 760, y: 165 },
      { name: "病因病机", count: "六淫 + 七情", items: "风 · 寒 · 暑 · 湿 · 燥 · 火  |  怒 · 喜 · 忧 · 思 · 悲 · 恐 · 惊", x: 72, y: 365 },
      { name: "复合证型", count: "7 种常见组合", items: "肝郁脾虚 · 心肾不交 · 脾肾阳虚 · 气阴两虚 · 痰瘀互结 · 肝阳上亢 · 上热下寒", x: 416, y: 365 },
    ];

    for (const sys of systems) {
      card(s, sys.x, sys.y, 312, 170,
        `${sys.count}\n\n${sys.items}`,
        sys.name
      );
    }

    // Right side: usage flow
    s.shapes.add({
      geometry: "textbox", position: { left: 760, top: 365, width: 448, height: 36 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "使用方式", style: { fontSize: 16, bold: true, color: ACCENT } };

    card(s, 760, 405, 448, 130,
      "子智能体分析流程\n\n" +
      "1. 八纲辨证 → 定大方向（寒热虚实表里阴阳）\n" +
      "2. 脏腑辨证 → 定位病变脏腑\n" +
      "3. 气血津液 → 分析物质基础\n" +
      "4. 病因病机 → 推断病因\n" +
      "→ 综合输出：病位 + 病性 + 核心病机 + 证型",
      null
    );

    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 580, width: 1136, height: 50 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = {
      value: "覆盖 50+ 常见证型  ·  每证型含主症 + 关键鉴别点  ·  子智能体分析时有据可查，结果更一致",
      style: { fontSize: 16, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 7: 总结
  // ============================================================
  {
    const s = presentation.slides.add();
    s.background.fill = WHITE;
    title(s, "总结");

    // Done
    const done = [
      "前端全新视觉风格 — 薰衣草蓝白 + 侧边栏 + 现代卡片",
      "tcm-intake Skill — 十二维度深度追问指南 + 红旗信号",
      "tcm-zhengxing Skill — 四大辨证体系速查表 50+ 证型",
      "Deep Agents 框架稳定运行 — 4 子智能体并行辨证",
      "Skills 按需加载 — 不触发不加载，不占启动上下文",
    ];

    done.forEach((text, i) => {
      s.shapes.add({
        geometry: "textbox", position: { left: 72, top: 150 + i * 48, width: 1136, height: 36 },
        fill: "none", line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: `✅  ${text}`, style: { fontSize: 18, color: DARK } };
    });

    // Divider
    s.shapes.add({
      geometry: "rect",
      position: { left: 72, top: 410, width: 1136, height: 1 },
      fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    // Next
    s.shapes.add({
      geometry: "textbox", position: { left: 72, top: 430, width: 1136, height: 36 },
      fill: "none", line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "下一步", style: { fontSize: 22, bold: true, color: ACCENT } };

    const next = [
      "药膳食疗 Skill — 基于证型推荐食疗方案",
      "舌象识别 — 拍照自动分析舌色/苔色/苔质",
      "问诊档案检索与体质追踪",
    ];

    next.forEach((text, i) => {
      s.shapes.add({
        geometry: "textbox", position: { left: 72, top: 480 + i * 36, width: 1136, height: 30 },
        fill: "none", line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: `🔜  ${text}`, style: { fontSize: 16, color: GRAY } };
    });
  }

  // ============================================================
  // Export
  // ============================================================
  const outName = "AI老中医问诊-本周进展.pptx";
  const outputFile = PresentationFile.fromPresentation(presentation, "pptx");
  await writeBlob(`ppt-output/${outName}`, outputFile.blob);
  console.log(`Done → ppt-output/${outName}`);
}

main().catch(console.error);
