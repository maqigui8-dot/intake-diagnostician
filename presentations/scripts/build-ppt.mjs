import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir("output", { recursive: true });

  const presentation = Presentation.create({
    slideSize: { width: 1280, height: 720 },
  });

  const P = { left: 72, top: 48, width: 1136, height: 640 };
  const WHITE = "white";
  const DARK = "slate-900";
  const GRAY = "slate-600";
  const LIGHT = "slate-200";
  const ACCENT = "emerald-600";

  // ============================================================
  // SLIDE 1: Title
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 200, width: 1136, height: 120 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "AI老中医问诊", style: { fontSize: 56, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 340, width: 1136, height: 60 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "中医诊前问诊子智能体 · 项目学习成果汇报", style: { fontSize: 28, color: GRAY } };

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 440, width: 1136, height: 40 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "Vue3 + Vite + FastAPI + LangChain + 千问大模型", style: { fontSize: 20, color: "slate-400" } };

    slide.shapes.add({
      geometry: "rect",
      position: { left: 72, top: 520, width: 120, height: 3 },
      fill: ACCENT,
      line: { style: "solid", fill: "none", width: 0 },
    });
  }

  // ============================================================
  // SLIDE 2: Architecture
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 48, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "系统架构总览", style: { fontSize: 36, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect",
      position: { left: 72, top: 112, width: 1136, height: 1 },
      fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    const boxes = [
      { label: "患者浏览器\nChrome", x: 100, y: 180, w: 280, h: 100, color: "slate-200" },
      { label: "Vite 前端 (5173)\nVue3 + TailwindCSS", x: 500, y: 180, w: 280, h: 100, color: "blue-100" },
      { label: "FastAPI 后端 (8000)\nPython + LangChain", x: 900, y: 180, w: 280, h: 100, color: "emerald-100" },
      { label: "千问云端 API\nqwen-plus", x: 320, y: 380, w: 280, h: 80, color: "amber-100" },
      { label: "Ollama 本地\nqwen3:8b (回退)", x: 680, y: 380, w: 280, h: 80, color: "orange-100" },
      { label: "JSON 病历存档\nbackend/records/", x: 500, y: 540, w: 280, h: 80, color: "slate-100" },
    ];

    for (const b of boxes) {
      const shape = slide.shapes.add({
        geometry: "roundRect",
        position: { left: b.x, top: b.y, width: b.w, height: b.h },
        fill: b.color,
        line: { style: "solid", fill: "slate-300", width: 1 },
        borderRadius: "rounded-lg",
      });
      shape.text = { value: b.label, style: { fontSize: 16, color: DARK } };
    }

    // arrows as simple labels
    slide.shapes.add({
      geometry: "textbox", position: { left: 390, top: 210, width: 100, height: 40 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "HTTP →", style: { fontSize: 18, color: "slate-400" } };

    slide.shapes.add({
      geometry: "textbox", position: { left: 790, top: 210, width: 100, height: 40 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "proxy /api →", style: { fontSize: 18, color: "slate-400" } };

    slide.shapes.add({
      geometry: "textbox", position: { left: 1020, top: 295, width: 180, height: 80 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "API 调用\n↓", style: { fontSize: 14, color: "slate-400" } };
  }

  // ============================================================
  // SLIDE 3: Frontend - App.vue + ChatWindow.vue
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 48, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "前端架构 · App.vue  +  ChatWindow.vue", style: { fontSize: 36, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect", position: { left: 72, top: 112, width: 1136, height: 1 }, fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    // Left: App.vue
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 140, width: 500, height: 36 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "App.vue - 主布局骨架", style: { fontSize: 24, bold: true, color: ACCENT } };

    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 178, width: 500, height: 32 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "frontend/src/App.vue", style: { fontSize: 14, color: "slate-400" } };

    // Code placeholder
    slide.shapes.add({
      geometry: "roundRect",
      position: { left: 72, top: 220, width: 540, height: 280 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-300", width: 1 },
      borderRadius: "rounded-lg",
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 92, top: 230, width: 500, height: 260 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "const sessionId = ref(\n" +
      "  crypto.randomUUID()\n" +
      ")\n\n" +
      "async function onComplete(\n" +
      "  { patient_name,\n" +
      "    collected_info,\n" +
      "    markdown_table }\n" +
      ") {\n" +
      "  await fetch(\n" +
      "    '/api/save_record',\n" +
      "    { method: 'POST', ... }\n" +
      "  )\n" +
      "}\n\n" +
      "// 页面加载即刻生成会话ID\n" +
      "// 问诊完成自动存档",
      style: { fontSize: 14, color: DARK }
    };

    // Right: ChatWindow.vue
    slide.shapes.add({
      geometry: "textbox", position: { left: 660, top: 140, width: 548, height: 36 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "ChatWindow.vue - 对话核心", style: { fontSize: 24, bold: true, color: ACCENT } };

    slide.shapes.add({
      geometry: "textbox", position: { left: 660, top: 178, width: 548, height: 32 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "frontend/src/components/ChatWindow.vue", style: { fontSize: 14, color: "slate-400" } };

    slide.shapes.add({
      geometry: "roundRect",
      position: { left: 660, top: 220, width: 548, height: 280 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-300", width: 1 },
      borderRadius: "rounded-lg",
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 680, top: 230, width: 508, height: 260 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "async function sendMessage() {\n" +
      "  // 1. 添加患者气泡\n" +
      "  messages.value.push({\n" +
      "    role: 'user', content: text\n" +
      "  })\n\n" +
      "  // 2. POST /api/chat\n" +
      "  const data = await fetch(\n" +
      "    '/api/chat', {\n" +
      "      session_id, message: text\n" +
      "    }\n" +
      "  ).then(r => r.json())\n\n" +
      "  // 3. 渲染助手气泡\n" +
      "  // 4. is_complete → emit\n" +
      "  //    → 自动存档",
      style: { fontSize: 14, color: DARK }
    };

    // Bottom note
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 530, width: 1136, height: 60 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "技术要点: Vue3 Composition API · ref/reactive 状态管理 · markdown-it 表格渲染 · fetch 异步通信 · emit 事件传递",
      style: { fontSize: 16, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 4: Frontend - 样式与动画
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 48, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "前端设计 · 中医美学 + 消息交互", style: { fontSize: 36, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect", position: { left: 72, top: 112, width: 1136, height: 1 }, fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    const items = [
      { title: "宣纸底色", file: "src/style.css", code: "background: #F5F0E8;\n/* CSS 网格暗纹 */\nrepeating-linear-gradient(...)", x: 72, y: 150 },
      { title: "消息气泡", file: "ChatWindow.vue :54-68", code: "患者靠右: rgba(255,255,255,0.75)\n助手靠左: linear-gradient(\n  #FFF8E7, #F5E6CC)", x: 640, y: 150 },
      { title: "淡入动画", file: "src/style.css :48-55", code: "@keyframes fadeInUp {\n  from { opacity:0;\n    transform: translateY(12px) }\n  to { opacity:1; ... }\n}", x: 72, y: 360 },
      { title: "中式表格", file: "src/style.css :57-85", code: ".chinese-table thead th {\n  background: #2E7D32;\n  color: #FDFBF7;\n}\n隔行变色、hover高亮", x: 640, y: 360 },
    ];

    for (const item of items) {
      slide.shapes.add({
        geometry: "textbox", position: { left: item.x, top: item.y, width: 420, height: 30 }, fill: "none",
        line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: item.title, style: { fontSize: 18, bold: true, color: ACCENT } };

      slide.shapes.add({
        geometry: "textbox", position: { left: item.x, top: item.y + 28, width: 420, height: 28 }, fill: "none",
        line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: item.file, style: { fontSize: 13, color: "slate-400" } };

      slide.shapes.add({
        geometry: "roundRect",
        position: { left: item.x, top: item.y + 60, width: 540, height: 110 },
        fill: "slate-50",
        line: { style: "solid", fill: "slate-300", width: 1 },
        borderRadius: "rounded-lg",
      });

      slide.shapes.add({
        geometry: "textbox", position: { left: item.x + 20, top: item.y + 70, width: 500, height: 90 }, fill: "none",
        line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: item.code, style: { fontSize: 14, color: DARK } };
    }

    // Loader note
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 600, width: 1136, height: 60 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "加载态: 三个墨绿圆点 CSS animate-pulse · 文本: \"AI老中医正在为您辨证…\" · 无 AI/机器人等字眼",
      style: { fontSize: 16, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 5: Backend - main.py overview
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 48, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "后端架构 · FastAPI + LangChain", style: { fontSize: 36, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect", position: { left: 72, top: 112, width: 1136, height: 1 }, fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 130, width: 1136, height: 32 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "backend/main.py  (约 280 行)", style: { fontSize: 16, color: "slate-400" } };

    // LLM 双通道
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 175, width: 540, height: 36 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "LLM 双通道配置", style: { fontSize: 22, bold: true, color: ACCENT } };

    slide.shapes.add({
      geometry: "roundRect",
      position: { left: 72, top: 220, width: 540, height: 200 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-300", width: 1 },
      borderRadius: "rounded-lg",
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 92, top: 230, width: 500, height: 180 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "def build_llm() -> ChatOpenAI:\n" +
      "  api_key = os.getenv(\n" +
      "    \"DASHSCOPE_API_KEY\", \"\"\n" +
      "  )\n" +
      "  if api_key:\n" +
      "    return ChatOpenAI(\n" +
      "      model=\"qwen-plus\",\n" +
      "      base_url=\"dashscope...\"\n" +
      "    )\n" +
      "  else:  # 回退 Ollama\n" +
      "    return ChatOpenAI(\n" +
      "      model=\"qwen3:8b\",\n" +
      "      base_url=\":11434/v1\"\n" +
      "    )",
      style: { fontSize: 14, color: DARK }
    };

    // JSON 解析
    slide.shapes.add({
      geometry: "textbox", position: { left: 660, top: 175, width: 548, height: 36 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "JSON 三层容错", style: { fontSize: 22, bold: true, color: ACCENT } };

    slide.shapes.add({
      geometry: "roundRect",
      position: { left: 660, top: 220, width: 548, height: 200 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-300", width: 1 },
      borderRadius: "rounded-lg",
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 680, top: 230, width: 508, height: 180 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "def extract_json(text):\n" +
      "  # 1. 直接 json.loads\n" +
      "  try: return json.loads(text)\n" +
      "  except: pass\n\n" +
      "  # 2. 提取 ```json``` 代码块\n" +
      "  match = re.search(\n" +
      "    r\"```(?:json)?\\s*(.*?)```\",\n" +
      "    text)\n\n" +
      "  # 3. 截取首尾 { ... }\n" +
      "  start = text.find(\"{\")\n" +
      "  end = text.rfind(\"}\")\n\n" +
      "  # 全失败 → 兜底回复",
      style: { fontSize: 14, color: DARK }
    };

    // Bottom
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 450, width: 1136, height: 80 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "会话管理: sessions 内存字典 · 病历存档: POST /api/save_record → backend/records/{uuid}.json · CORS 全放行",
      style: { fontSize: 16, color: GRAY }
    };

    // API 端点表
    slide.shapes.add({
      geometry: "table",
      position: { left: 72, top: 540, width: 1136, height: 120 },
      fill: WHITE,
      line: { style: "solid", fill: LIGHT, width: 1 },
    });

    slide.tables.add({
      position: { left: 72, top: 540, width: 1136, height: 120 },
      rows: [
        ["接口", "方法", "说明"],
        ["/api/chat", "POST", "核心对话: 收消息 → 调LLM → 返回reply+table+is_complete"],
        ["/api/save_record", "POST", "问诊完成时存档到 records/*.json"],
        ["/api/records", "GET", "列出所有病历（按时间倒序）"],
      ],
      style: { headerRowFill: "slate-100", bodyRowFill: WHITE, fontSize: 14 },
    });
  }

  // ============================================================
  // SLIDE 6: Backend - System Prompt
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 48, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "核心引擎 · 系统提示词 (SYSTEM_PROMPT)", style: { fontSize: 36, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect", position: { left: 72, top: 112, width: 1136, height: 1 }, fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 122, width: 1136, height: 28 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "backend/main.py :50-95  SYSTEM_PROMPT", style: { fontSize: 14, color: "slate-400" } };

    const sections = [
      { title: "角色定义", body: "自称AI老中医，温和耐心\n避免AI/机器人/大模型等字眼", x: 72, y: 170 },
      { title: "问诊规则", body: "十问歌顺序: 寒热→汗→头身→\n二便→饮食→胸腹→睡眠→渴→\n旧病→病因。一次只问一方", x: 400, y: 170 },
      { title: "信息采集", body: "collected_info JSON:\npatient_name chief_complaint\ncold_heat sweating bowels\nsleep diet ... 共16字段", x: 728, y: 170 },
      { title: "完成判断", body: "≥7个主项有内容→\nis_complete=true\n生成markdown_table", x: 1056, y: 170 },
    ];

    for (const s of sections) {
      slide.shapes.add({
        geometry: "textbox", position: { left: s.x, top: s.y, width: 280, height: 32 }, fill: "none",
        line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: s.title, style: { fontSize: 20, bold: true, color: ACCENT } };

      slide.shapes.add({
        geometry: "roundRect",
        position: { left: s.x, top: s.y + 40, width: 280, height: 140 },
        fill: "slate-50",
        line: { style: "solid", fill: "slate-200", width: 1 },
        borderRadius: "rounded-lg",
      });

      slide.shapes.add({
        geometry: "textbox", position: { left: s.x + 20, top: s.y + 55, width: 240, height: 110 }, fill: "none",
        line: { style: "solid", fill: "none", width: 0 },
      }).text = { value: s.body, style: { fontSize: 15, color: DARK } };
    }

    // Output format
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 370, width: 1136, height: 32 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "输出格式约束 (必须严格遵守)", style: { fontSize: 22, bold: true, color: ACCENT } };

    slide.shapes.add({
      geometry: "roundRect",
      position: { left: 72, top: 415, width: 1136, height: 120 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-300", width: 1 },
      borderRadius: "rounded-lg",
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 92, top: 425, width: 1096, height: 100 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "{\n" +
      '  "thinking": "推理过程...",\n' +
      '  "reply": "对患者说的温润话语...",\n' +
      '  "collected_info": { "patient_name": "张三", "chief_complaint": "头晕乏力", ... },\n' +
      '  "is_complete": false,\n' +
      '  "markdown_table": null\n' +
      "}\n" +
      "→ 每次必须且只能返回这个 JSON，多一个字符都不行 → 三重容错解析 → 解析失败有兜底",
      style: { fontSize: 14, color: DARK }
    };

    // Bottom
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 570, width: 1136, height: 60 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "对话流程: 前端 POST → 后端组装 [SystemMessage + history] → LLM.invoke() → 解析JSON → 返回前端渲染",
      style: { fontSize: 16, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 7: Demo screenshots
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 48, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "成果展示 · 界面截图", style: { fontSize: 36, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect", position: { left: 72, top: 112, width: 1136, height: 1 }, fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    // Screenshot placeholders
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 140, width: 540, height: 24 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "问诊对话界面", style: { fontSize: 18, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect",
      position: { left: 72, top: 175, width: 540, height: 360 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-300", width: 2, dash: "dash" },
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 220, top: 340, width: 250, height: 30 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "【截图位置】", style: { fontSize: 16, color: "slate-400" } };

    slide.shapes.add({
      geometry: "textbox", position: { left: 660, top: 140, width: 548, height: 24 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "四诊档案表格", style: { fontSize: 18, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect",
      position: { left: 660, top: 175, width: 548, height: 360 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-300", width: 2, dash: "dash" },
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 840, top: 340, width: 250, height: 30 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "【截图位置】", style: { fontSize: 16, color: "slate-400" } };

    // How to capture
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 560, width: 1136, height: 80 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "截图方法: Win+Shift+S 框选聊天界面 → 粘贴到此处 · 建议录制一段 30s 对话视频更直观\n" +
      "启动命令: 后端 uvicorn main:app --port 8000 · 前端 npm run dev · 浏览器 localhost:5173",
      style: { fontSize: 16, color: GRAY }
    };
  }

  // ============================================================
  // SLIDE 8: Summary
  // ============================================================
  {
    const slide = presentation.slides.add();
    slide.background.fill = WHITE;

    slide.shapes.add({
      geometry: "textbox",
      position: { left: 72, top: 80, width: 1136, height: 52 },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "技术栈总结", style: { fontSize: 36, bold: true, color: DARK } };

    slide.shapes.add({
      geometry: "rect", position: { left: 72, top: 144, width: 1136, height: 1 }, fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });

    // Tech stack table
    slide.tables.add({
      position: { left: 72, top: 170, width: 1136, height: 160 },
      rows: [
        ["层级", "技术选型", "核心能力"],
        ["前端框架", "Vue 3 + Vite + TailwindCSS", "响应式UI · HMR热更新 · 中文美学设计"],
        ["后端框架", "Python FastAPI", "异步高性能 · Pydantic校验 · CORS中间件"],
        ["AI引擎", "LangChain + ChatOpenAI", "千问云端 / Ollama本地 双通道回退"],
        ["数据存储", "JSON文件 (records/)", "问诊完成自动存档 · 重启不丢失"],
        ["通信", "fetch + Vite proxy", "前端/api → 后端:8000，开发零跨域"],
      ],
      style: { headerRowFill: "slate-100", bodyRowFill: WHITE, fontSize: 16 },
    });

    // File structure
    slide.shapes.add({
      geometry: "textbox", position: { left: 72, top: 360, width: 540, height: 32 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "项目文件结构", style: { fontSize: 22, bold: true, color: ACCENT } };

    slide.shapes.add({
      geometry: "roundRect",
      position: { left: 72, top: 400, width: 540, height: 250 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-200", width: 1 },
      borderRadius: "rounded-lg",
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 92, top: 410, width: 500, height: 230 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "intake-diagnostician/\n" +
      "├── backend/\n" +
      "│   ├── main.py          ← 核心\n" +
      "│   ├── requirements.txt\n" +
      "│   └── records/          ← 病历存档\n" +
      "├── frontend/\n" +
      "│   ├── src/\n" +
      "│   │   ├── App.vue\n" +
      "│   │   ├── style.css\n" +
      "│   │   └── components/\n" +
      "│   │       └── ChatWindow.vue\n" +
      "│   └── vite.config.js\n" +
      "└── README.md",
      style: { fontSize: 16, color: DARK }
    };

    // Learnings
    slide.shapes.add({
      geometry: "textbox", position: { left: 660, top: 360, width: 548, height: 32 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value: "学习收获", style: { fontSize: 22, bold: true, color: ACCENT } };

    slide.shapes.add({
      geometry: "roundRect",
      position: { left: 660, top: 400, width: 548, height: 250 },
      fill: "slate-50",
      line: { style: "solid", fill: "slate-200", width: 1 },
      borderRadius: "rounded-lg",
    });

    slide.shapes.add({
      geometry: "textbox", position: { left: 680, top: 410, width: 508, height: 230 }, fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    }).text = { value:
      "1. Prompt Engineering\n" +
      "   结构化约束LLM输出JSON\n\n" +
      "2. 全栈通信\n" +
      "   Vue fetch ↔ FastAPI ↔ LLM\n\n" +
      "3. 错误防御设计\n" +
      "   JSON三层容错 · 异常兜底\n\n" +
      "4. 中医知识数字化\n" +
      "   十问歌 → 结构化四诊档案\n\n" +
      "5. 工程权衡\n" +
      "   内存会话 vs 持久化\n" +
      "   云端API vs 本地模型回退",
      style: { fontSize: 16, color: DARK }
    };
  }

  // ============================================================
  // Render & Export
  // ============================================================
  const outDir = "output";
  const outputFile = PresentationFile.fromPresentation(presentation, "pptx");
  await writeBlob(`${outDir}/AI老中医问诊-汇报.pptx`, outputFile.blob);

  const rend = presentation.render({
    outputFolder: `${outDir}/slides`,
    montage: true,
    scale: 1,
  });
  for await (const _ of rend) {}

  console.log("Done! PPTX + slides rendered.");
}

main().catch(console.error);
