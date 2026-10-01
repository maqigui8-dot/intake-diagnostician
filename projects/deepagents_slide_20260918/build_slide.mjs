import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/Administrator/Desktop/project/pre-diagnosis/intake-diagnostician";
const SOURCE = path.join(ROOT, "presentations", "前期学习与项目实践汇报.pptx");
const WORK = path.join(ROOT, "projects", "deepagents_slide_20260918");
const OUTPUT = path.join(ROOT, "presentations", "前期学习与项目实践汇报_DeepAgents新增页.pptx");
const SKILL = "C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations";
const PY = "C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const C = { bg:"#F7F5EF", panel:"#EEF1EA", green:"#155348", green2:"#4D8F7D", orange:"#D66B42", text:"#566762", strong:"#263D38", line:"#CAD7D1", white:"#FFFFFF" };
const FONT = "Microsoft YaHei";

const ppt = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
ppt.slides.insert({ after: 18 });
const slide = ppt.slides.getItem(19);

function box(x,y,w,h,fill=C.bg,stroke="none",sw=0){return slide.shapes.add({geometry:"rect",position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw}})}
function circle(x,y,d,fill=C.green){return slide.shapes.add({geometry:"ellipse",position:{left:x,top:y,width:d,height:d},fill,line:{fill:"none",width:0}})}
function text(value,x,y,w,h,size=20,color=C.text,bold=false,align="left",valign="top"){
  const t=slide.shapes.add({geometry:"textbox",position:{left:x,top:y,width:w,height:h},fill:"none",line:{fill:"none",width:0}});
  t.text=value;t.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:valign,autoFit:"shrinkText",wrap:"square",insets:{top:0,right:0,bottom:0,left:0}};return t;
}

box(0,0,1280,720,C.bg);
text("Agent 学习实践",68,34,220,20,13,C.green,true);
text("基于 DeepAgents 构建中医复诊智能体",68,64,760,50,31,C.strong,true);
box(68,124,86,4,C.orange);box(154,125,1058,2,C.line);

text("工作链路",68,158,190,28,18,C.orange,true);
const steps=[["01","患者输入"],["02","查询历史"],["03","辨证分析"],["04","保存记录"],["05","对比报告"]];
for(let i=0;i<steps.length;i++){
  const x=68+i*96;
  circle(x,206,42,i===2?C.orange:C.green);
  text(steps[i][0],x,217,42,18,12,C.white,true,"center");
  text(steps[i][1],x-14,258,70,22,15,C.strong,true,"center");
  if(i<steps.length-1) box(x+42,225,54,2,C.line);
}

text("实现要点",68,316,180,28,18,C.orange,true);
const points=[
  ["01","框架编排","create_deep_agent 统一配置模型、工具、提示词与状态"],
  ["02","工具调用","查询历史、检索知识、保存记录并生成复诊对比"],
  ["03","状态持久化","SqliteSaver 保存会话；PostgreSQL 不可用时回退 SQLite"]
];
for(let i=0;i<3;i++){
  const y=358+i*70;
  text(points[i][0],68,y,32,22,14,C.orange,true);
  text(points[i][1],112,y-2,120,24,17,C.strong,true);
  text(points[i][2],112,y+26,420,34,14,C.text);
}

box(586,158,626,410,C.panel,C.green,2);
text("DeepAgent 运行效果",610,180,330,26,16,C.orange,true);
text("在此放置终端运行结果或复诊对比报告截图",650,338,498,32,20,C.green,true,"center");
box(624,388,550,1,C.line);
text("截图说明：测试患者 / 输入场景 / 输出结果",624,532,550,22,14,C.text,false,"center");

box(68,590,1144,48,C.panel);
text("项目定位：用于学习 DeepAgents 的工具调用、状态记忆与任务编排，不替代医生诊断或临床决策。",92,604,1096,22,16,C.green,true);
text("20",1166,670,36,18,11,C.text,false,"right");
slide.speakerNotes.textFrame.setText("本页展示基于 DeepAgents 框架实现的中医复诊智能体原型。左侧说明框架如何查询历史、结合当前症状与舌象完成分析，并保存记录生成复诊对比；右侧预留实际运行截图位置。该项目仅用于学习与原型验证，不替代医生诊断。");

// 插入新页后，将原第20—31页右下角的旧页码覆盖并顺延为21—32。
for (let index = 20; index < 32; index++) {
  const target = ppt.slides.getItem(index);
  target.shapes.add({geometry:"rect",position:{left:1152,top:656,width:76,height:42},fill:C.bg,line:{fill:"none",width:0}});
  const pageNo = target.shapes.add({geometry:"textbox",position:{left:1166,top:670,width:36,height:18},fill:"none",line:{fill:"none",width:0}});
  pageNo.text=String(index+1).padStart(2,"0");
  pageNo.text.style={typeface:FONT,fontSize:11,color:C.text,alignment:"right",verticalAlignment:"top",autoFit:"shrinkText",wrap:"square",insets:{top:0,right:0,bottom:0,left:0}};
}

await fs.mkdir(path.join(WORK,".codex-finalizer"),{recursive:true});
const candidate=path.join(WORK,".codex-finalizer","candidate.pptx");
await (await PresentationFile.exportPptx(ppt)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,"container_tools/artifact_tool_utils.mjs")).href);
await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:OUTPUT,pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,"container_tools/inspect_presentation_package_integrity.py"),layoutValidatorPath:path.join(SKILL,"container_tools/inspect_presentation_layout_geometry.py"),layoutArgs:["--expected-slide-size-emu","12192000,6858000","--validate-heading-fit"],explicitTotalSlideCount:32,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:"design",families:["Arial",FONT]},verifyArtifactToolImport:true,receiptPath:path.join(WORK,".codex-finalizer","validation.json")});
