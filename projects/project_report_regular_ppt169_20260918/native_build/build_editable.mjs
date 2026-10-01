import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const W = "C:/Users/Administrator/Desktop/project/pre-diagnosis/intake-diagnostician/projects/project_report_regular_ppt169_20260918";
const SKILL = "C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations";
const PY = "C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const C = { bg:"#F7F5EF", panel:"#EFEEE8", green:"#155348", orange:"#C86A3A", text:"#566762", strong:"#263D38", muted:"#7B8783", line:"#BFCFC9", border:"#D7DEDA", white:"#F7F5EF" };
const FONT = "Microsoft YaHei";
const ppt = Presentation.create({slideSize:{width:1280,height:720}});

function box(slide,x,y,w,h,fill=C.bg,stroke="none",sw=0){return slide.shapes.add({geometry:"rect",position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw}})}
function line(slide,x,y,w,h=1,color=C.line,sw=1){return slide.shapes.add({geometry:"line",position:{left:x,top:y,width:w,height:h},fill:"none",line:{fill:color,width:sw}})}
function circle(slide,x,y,d,fill=C.green,stroke="none",sw=0){return slide.shapes.add({geometry:"ellipse",position:{left:x,top:y,width:d,height:d},fill,line:{fill:stroke,width:sw}})}
function text(slide,s,x,y,w,h,size=20,color=C.text,bold=false,align="left",valign="top"){
  if(size===14) size=15; else if(size===15) size=16; else if(size===16) size=18; else if(size===17) size=18;
  const t=slide.shapes.add({geometry:"textbox",position:{left:x,top:y,width:w,height:h},fill:"none",line:{fill:"none",width:0}});t.text=s;t.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:valign,autoFit:"shrinkText",wrap:"square",insets:{top:0,right:0,bottom:0,left:0}};return t;
}
function base(titleText,no){const s=ppt.slides.add();s.background.fill=C.bg;text(s,titleText,68,42,1040,52,36,C.green,true);box(s,68,110,88,4,C.orange);box(s,156,111,1004,2,C.line);box(s,68,646,1092,1,C.line);text(s,String(no).padStart(2,"0"),1100,658,36,18,12,C.text,false,"right");return s;}
function label(slide,n,titleText,x,y,w){text(slide,String(n).padStart(2,"0"),x,y,34,24,15,C.orange,true);text(slide,titleText,x+44,y-2,w-44,28,21,C.strong,true)}
const notes=[
"各位老师好，我汇报的项目是中医诊前信息采集与整理系统。项目关注诊前资料采集与整理，不承担自动诊断。",
"患者自然表达往往零散，医生仍要重新确认；普通聊天式问诊还会重复追问，停止条件和决策原因也不清楚。",
"项目目标包括自然语言结构化、有限追问、停止判断和结果可追溯。系统不自动诊断、不输出患病概率、不自动开方。",
"系统分为交互、接口、决策和数据四层。Agent负责理解和表达，确定性规则负责完整度、下一问和停止判断。",
"患者端提供信息，医生端查看和理解信息。所有会话和档案绑定patient_id，医生端当前保持只读。",
"每次回答后，系统都会重新完成信息提取、字段更新、完整度判断和下一问选择，因此不依赖固定轮数。",
"每个问题来自字段定义。Agent提取值、原文证据和来源，规则更新字段状态并选择下一目标。",
"完整度由核心字段、安全缺口和冲突共同决定，不要求所有可选字段全部填写。",
"追问优先处理危险信号和核心字段。规则决定问什么，Agent负责把目标字段表达成自然问题。",
"系统根据核心完整度和在线可采集性决定继续、正常结束或保护性结束。保护性结束不代表资料完整。",
"当前版本已经实现核心字段驱动停止、规则约束Agent、尝试次数控制和多患者数据隔离。",
"此页展示身份选择、基础资料和侧栏历史记录。后续可直接用真实截图替换占位框。",
"此页按开放描述、逐项追问和诊前档案三个阶段展示完整操作过程。",
"医生工作台集中展示患者列表、问诊详情和决策解释，使问诊结果更容易理解和追溯。"
];

// 01
{
 const s=ppt.slides.add();s.background.fill=C.bg;text(s,"中医诊前信息采集与整理系统",140,240,1000,78,58,C.green,true,"center","middle");box(s,500,334,280,4,C.orange);text(s,"项目汇报",490,385,300,32,20,C.strong,false,"center");text(s,"汇报人：________　　日期：________",390,438,500,24,15,C.muted,false,"center");box(s,172,610,936,1,C.line);text(s,"01",1100,658,36,18,12,C.text,false,"right");s.speakerNotes.textFrame.setText(notes[0]);
}
// 02
{
 const s=base("项目背景与问题",2);text(s,"诊前信息采集的现实问题",68,150,500,36,25,C.strong,true);text(s,"患者通常按照自己的感受自然表达，信息真实但零散。医生需要重新确认病程、安全信息和生活方式，才能形成可使用的诊前资料。",68,206,500,150,19,C.text);line(s,610,150,1,420,C.line,1);
 const ys=[160,258,356,454],ts=["描述零散","重复询问","停止条件不清","决策难以解释"],ds=["时间、程度和关联因素分散在多轮回答中","缺少字段状态时，同一信息可能反复确认","可选细节持续阻塞结束，问诊轮数过多","医生看不到问题来源和停止原因"];
 for(let i=0;i<4;i++){label(s,i+1,ts[i],654,ys[i],506);text(s,ds[i],698,ys[i]+34,438,28,16,C.text);if(i<3)line(s,654,ys[i]+76,506,1,C.border,1)}
 box(s,68,568,1092,54,C.panel);text(s,"项目需求：结构化采集、有限追问、及时停止、过程可解释",92,584,1044,24,18,C.green,true);s.speakerNotes.textFrame.setText(notes[1]);
}
// 03
{
 const s=base("项目目标与定位",3);
 text(s,"系统定位",68,154,150,26,18,C.orange,true);text(s,"面向成人肥胖诊前场景，帮助患者把情况说完整，帮助医生更快理解资料。",68,190,1092,38,24,C.strong,true);
 const items=[
  ["01","信息结构化","把患者的自然描述整理为症状、时间、生活方式和安全信息等明确字段。"],
  ["02","有目的追问","根据仍然缺失的核心信息选择下一项问题，减少无关提问和重复确认。"],
  ["03","及时停止","核心资料已经可用时正常结束；无法继续采集或出现风险时保护性结束。"],
  ["04","结果可追溯","保存患者原始回答、字段来源、判断依据和最终诊前档案，供医生查看。"]
 ];
 const pos=[[68,272],[650,272],[68,416],[650,416]];
 for(let i=0;i<4;i++){const [x,y]=pos[i];text(s,items[i][0],x,y,44,26,16,C.orange,true);text(s,items[i][1],x+56,y-2,470,30,23,C.green,true);text(s,items[i][2],x+56,y+42,470,68,18,C.text)}
 box(s,68,576,1092,46,C.panel);text(s,"能力边界：系统不自动诊断、不输出患病概率、不自动开方，最终判断仍由医生完成。",92,589,1044,24,17,C.green,true);s.speakerNotes.textFrame.setText(notes[2]);
}
// 04
{
 const s=base("系统整体架构",4);const yy=[148,248,348,472],hh=[78,78,102,88],labs=["01  交互层","02  接口层","03  决策层","04  数据层"],titles=["Vue 3 患者端　｜　独立医生工作台","FastAPI 服务","Agent 信息抽取　｜　确定性规则引擎","MySQL 完整持久化"],desc=["身份选择、问诊交互、历史档案与多患者查看","患者隔离接口、会话接口、医生查询接口与资源归属校验","Agent负责理解与表达；规则负责字段状态、完整度、下一问和停止判断","患者、会话、字段、问答、档案、归档状态与审计记录"];
 for(let i=0;i<4;i++){text(s,labs[i],68,yy[i]+24,120,24,15,i===2?C.orange:C.muted,true);box(s,210,yy[i],950,hh[i],i===2?C.green:(i%2===0?C.panel:C.bg),i===1?C.border:"none",i===1?1:0);text(s,titles[i],240,yy[i]+15,880,28,21,i===2?C.white:C.strong,true);text(s,desc[i],240,yy[i]+47,880,34,15,i===2?C.white:C.text)}
 text(s,"关键设计：模型负责“理解”，规则负责“决定”。",68,598,800,24,17,C.green,true);s.speakerNotes.textFrame.setText(notes[3]);
}
// 05
{
 const s=base("系统角色与主要功能",5);const colW=530;box(s,68,150,colW,380,C.panel);box(s,630,150,colW,380,C.bg,C.border,1);text(s,"患者端",96,176,474,34,26,C.green,true);text(s,"提供信息",96,216,474,22,15,C.orange,true);const p=["身份选择与患者切换","基础资料与开放描述","逐项追问与回答确认","未完成问诊恢复","查看个人历史档案"];p.forEach((v,i)=>{text(s,String(i+1).padStart(2,"0"),96,260+i*48,32,24,14,C.orange,true);text(s,v,140,258+i*48,420,28,18,C.text)});text(s,"医生端",658,176,474,34,26,C.green,true);text(s,"查看与理解",658,216,474,22,15,C.orange,true);const d=["患者列表与历史问诊","基础资料与问答详情","完整度和关键缺口","追问来源与停止原因","只读查看诊前档案"];d.forEach((v,i)=>{text(s,String(i+1).padStart(2,"0"),658,260+i*48,32,24,14,C.orange,true);text(s,v,702,258+i*48,420,28,18,C.text)});box(s,68,558,1092,60,C.panel);text(s,"数据边界：会话与档案绑定 patient_id；跨患者访问返回 404；医生端当前保持只读。",92,578,1044,24,16,C.green,true);s.speakerNotes.textFrame.setText(notes[4]);
}
// 06
{
 const s=base("完整问诊流程",6);
 text(s,"一次回答会触发一次新的判断，流程并不依赖固定追问轮数。",68,148,1092,30,20,C.text);
 const nx=[76,366,656];const nt=["患者表达","信息提取","完整度判断"];const nd=["选择患者并补充基础资料\n用自己的语言描述最关心的问题","Agent提取字段值与原文证据\n规则更新字段状态和信息来源","检查核心字段、安全缺口与冲突\n判断是否仍适合在线追问"];
 for(let i=0;i<3;i++){circle(s,nx[i],228,52,i===2?C.orange:C.green);text(s,String(i+1).padStart(2,"0"),nx[i],241,52,22,15,C.white,true,"center");text(s,nt[i],nx[i]+66,224,198,30,22,C.strong,true);text(s,nd[i],nx[i]+66,270,198,96,15,C.text);if(i<2){box(s,nx[i]+250,252,50,3,C.line)}}
 box(s,960,206,200,72,C.green);text(s,"继续追问",976,225,168,28,21,C.white,true,"center");text(s,"选择下一项有价值的问题",960,294,200,48,15,C.text,false,"center");
 box(s,960,388,200,72,C.bg,C.orange,2);text(s,"生成诊前档案",974,406,172,28,20,C.orange,true,"center");text(s,"正常结束或保护性结束",960,476,200,48,15,C.text,false,"center");
 box(s,902,252,40,3,C.line);box(s,940,252,3,174,C.line);box(s,940,424,20,3,C.orange);text(s,"仍需补充",844,216,92,22,15,C.green,true,"right");text(s,"可以结束",844,420,92,22,15,C.orange,true,"right");
 box(s,68,548,1092,74,C.panel);text(s,"循环关系",92,566,120,24,17,C.orange,true);text(s,"继续追问后，患者的新回答再次进入“信息提取—完整度判断”；满足结束条件后才生成档案。",214,564,922,40,18,C.green,true);s.speakerNotes.textFrame.setText(notes[5]);
}
// 07
{
 const s=base("结构化字段与信息来源",7);box(s,68,150,500,430,C.panel);text(s,"结构化字段",92,176,440,30,24,C.strong,true);const fs=["基础测量：年龄、身高、体重、腰围","病程信息：变化经过、相关因素、管理经历","中医症状：食欲口渴、二便、睡眠情绪","生活方式：饮食、运动、作息、压力进食","安全信息：过敏、用药、病史、危险信号"];fs.forEach((v,i)=>{text(s,String(i+1).padStart(2,"0"),92,230+i*62,34,22,14,i===4?C.orange:C.green,true);text(s,v,136,228+i*62,392,44,17,C.text)});box(s,600,150,560,430,C.bg,C.border,1);text(s,"问题来源",624,176,500,30,24,C.strong,true);const st=["字段预先定义","Agent 提取证据","规则更新状态","规则选择目标字段"];const sd=["标准问题、优先级、核心属性、尝试次数","字段值、患者原文、信息来源、回答质量","确认、部分获取、无法提供、不适用或冲突","Agent只负责把目标字段表达成自然问题"];st.forEach((v,i)=>{const y=226+i*78;box(s,624,y,512,58,i===3?C.green:(i%2?C.bg:C.panel),i===1?C.border:"none",i===1?1:0);text(s,v,644,y+8,470,22,18,i===3?C.white:C.strong,true);text(s,sd[i],644,y+32,470,20,14,i===3?C.white:C.text)});text(s,"问题顺序可以变化，但目标和来源始终可追踪。",68,602,1092,22,16,C.green,true);s.speakerNotes.textFrame.setText(notes[6]);
}
// 08
{
 const s=base("资料完整度如何判断",8);const cw=336;box(s,68,150,cw,402,C.panel);box(s,472,150,cw,402,C.bg,C.border,1);box(s,824,150,cw,402,C.panel);text(s,"字段状态",92,176,288,28,23,C.strong,true);["尚未询问","部分获取","已经确认","无法提供","不适用"].forEach((v,i)=>text(s,`${String(i+1).padStart(2,"0")}　${v}`,92,230+i*52,288,26,18,i===2?C.green:C.text,i===2));text(s,"判断条件",496,176,288,28,23,C.strong,true);["基础测量是否完成","核心字段是否缺失","安全信息是否确认","冲突是否已经解决","剩余信息是否适合在线采集"].forEach((v,i)=>text(s,`• ${v}`,496,230+i*52,288,26,17,C.text));text(s,"判断结果",848,176,288,28,23,C.strong,true);const rr=["继续追问","正常结束","保护性结束"],rd=["关键缺口仍可采集","核心信息可用且无阻塞项","在线采集失效，交由医生补充"];rr.forEach((v,i)=>{box(s,848,228+i*96,288,72,i===1?C.green:C.bg,i===2?C.orange:C.border,i===2?2:1);text(s,v,864,240+i*96,256,24,19,i===1?C.white:(i===2?C.orange:C.strong),true);text(s,rd[i],864,270+i*96,256,20,14,i===1?C.white:C.text)});box(s,68,576,1092,48,C.panel);text(s,"完整不等于所有字段填满，而是核心信息可用、安全缺口已处理、没有阻塞性冲突。",92,590,1044,22,17,C.green,true);s.speakerNotes.textFrame.setText(notes[7]);
}
// 09
{
 const s=base("追问优先级与决策机制",9);text(s,"优先级",68,148,160,28,23,C.strong,true);text(s,"目标字段",258,148,350,28,23,C.strong,true);text(s,"选择依据",650,148,510,28,23,C.strong,true);const a=["01","02","03","04","05"],b=["危险信号与安全字段","尚未完成的核心字段","存在冲突的字段","高优先级普通字段","可选补充信息"],c=["优先处理安全边界","决定档案基本使用价值","先澄清前后不一致","补充医生常用信息","轮数允许时继续采集"];
 for(let i=0;i<5;i++){const y=196+i*66;box(s,68,y,1092,54,i===0?C.panel:C.bg,i===0?"none":C.border,i===0?0:1);text(s,a[i],88,y+16,40,20,15,C.orange,true);text(s,b[i],258,y+13,350,26,18,C.strong,true);text(s,c[i],650,y+13,470,26,16,C.text)}
 box(s,68,548,1092,76,C.panel);text(s,"示例：用药信息与运动情况同时缺失时，规则先选择安全相关的“用药信息”；Agent再生成自然问题。",92,566,1044,42,16,C.green,true);s.speakerNotes.textFrame.setText(notes[8]);
}
// 10
{
 const s=base("何时停止追问",10);box(s,352,150,576,72,C.green);text(s,"当前信息是否仍需要并适合在线追问？",376,170,528,30,22,C.white,true,"center");line(s,640,222,1,40,C.line,2);line(s,238,262,804,1,C.line,2);const xs=[68,472,876],tt=["继续追问","正常结束","保护性结束"],dd=[["核心字段仍缺失","安全信息尚未确认","冲突仍可在线澄清"],["核心字段已经完整","无关键安全缺口","无未解决冲突"],["多次无法回答或问题重复","剩余内容不宜在线采集","AI暂不可用或出现风险"]];
 for(let i=0;i<3;i++){line(s,xs[i]+142,262,1,38,i===2?C.orange:C.line,2);box(s,xs[i],300,284,230,i===1?C.panel:C.bg,i===2?C.orange:C.border,i===2?2:1);text(s,tt[i],xs[i]+20,326,244,30,23,i===2?C.orange:C.green,true,"center");dd[i].forEach((v,j)=>text(s,`• ${v}`,xs[i]+24,382+j*40,236,26,16,C.text));if(i===2)text(s,"停止追问不代表资料完整",xs[i]+20,496,244,20,14,C.orange,true,"center")}
 text(s,"系统依据核心完整度和在线可采集性决定结束时机，不使用固定追问轮数。",68,590,1092,24,17,C.green,true);s.speakerNotes.textFrame.setText(notes[9]);
}
// 11
{
 const s=base("项目实现中的关键难点",11);text(s,"关键难点",68,148,240,26,20,C.strong,true);text(s,"解决方式",330,148,620,26,20,C.strong,true);text(s,"当前状态",1010,148,150,26,20,C.strong,true);const q=["追问轮数过多","Agent输出不稳定","“不知道”导致重复","多患者数据隔离"],sol=["核心字段驱动停止，可选字段不无限阻塞","Agent提供证据，确定性规则统一决策","记录尝试次数与回答质量，达到上限后转医生","显式patient_id与资源归属校验，跨患者返回404"];
 for(let i=0;i<4;i++){const y=190+i*84;box(s,68,y,1092,66,i%2===0?C.panel:C.bg,i%2===0?"none":C.border,i%2===0?0:1);text(s,q[i],88,y+20,220,26,18,C.strong,true);text(s,sol[i],330,y+18,640,30,16,C.text);text(s,"已实现",1010,y+20,126,24,16,C.green,true,"center")}
 box(s,68,554,1092,70,C.panel);text(s,"当前边界：演示身份不等于正式鉴权；真实临床效果、规则覆盖范围和权限体系仍需进一步验证。",92,574,1044,36,16,C.text);s.speakerNotes.textFrame.setText(notes[10]);
}
// 12
{
 const s=base("项目操作展示：身份选择与患者端",12);box(s,68,148,690,390,C.panel,C.green,2);text(s,"01  身份选择首页",88,168,300,24,15,C.orange,true);text(s,"放置主截图",238,308,350,32,22,C.green,true,"center");box(s,790,148,370,184,C.panel,C.border,1);text(s,"02  基础资料",810,168,300,24,15,C.orange,true);text(s,"放置截图",870,235,210,28,18,C.green,true,"center");box(s,790,354,370,184,C.panel,C.border,1);text(s,"03  侧栏与历史记录",810,374,320,24,15,C.orange,true);text(s,"放置截图",870,441,210,28,18,C.green,true,"center");text(s,"演示重点：多患者入口、数据隔离、侧栏折叠、未完成问诊恢复、独立历史记录。",68,584,1092,28,16,C.text);s.speakerNotes.textFrame.setText(notes[11]);
}
// 13
{
 const s=base("项目操作展示：问诊过程",13);const xs=[68,444,820],names=["开放描述","逐项补充追问","完成后的诊前档案"];for(let i=0;i<3;i++){box(s,xs[i],154,340,340,C.panel,i===1?C.green:C.border,i===1?2:1);text(s,`${String(i+1).padStart(2,"0")}  ${names[i]}`,xs[i]+20,176,300,24,15,C.orange,true);text(s,"放置截图",xs[i]+70,306,200,30,20,C.green,true,"center")};line(s,68,548,1092,1,C.line,1);text(s,"自由描述　→　信息抽取　→　单项追问　→　完整度更新　→　生成档案",68,574,1092,26,17,C.strong,true,"center");s.speakerNotes.textFrame.setText(notes[12]);
}
// 14
{
 const s=base("项目操作展示：医生工作台与总结",14);box(s,68,146,1092,338,C.panel,C.green,2);text(s,"医生三栏工作台 / 放置完整截图",92,168,500,24,15,C.orange,true);text(s,"患者列表　｜　问诊详情　｜　决策解释",300,300,680,34,23,C.green,true,"center");const xs=[68,432,796],tt=["患者列表","问诊详情","决策解释"],dd=["档案数量与快速切换","基础资料、描述和逐轮问答","完整度、缺口、来源和停止原因"];for(let i=0;i<3;i++){text(s,String(i+1).padStart(2,"0"),xs[i],526,34,22,14,C.orange,true);text(s,tt[i],xs[i]+44,524,260,26,18,C.strong,true);text(s,dd[i],xs[i]+44,558,300,38,14,C.text)}text(s,"项目通过规则约束 Agent，完成安全、可追踪、可解释的诊前信息整理。",68,612,1092,26,17,C.green,true);s.speakerNotes.textFrame.setText(notes[13]);
}

const buildDir=path.join(W,"native_build",".codex-finalizer");await fs.mkdir(buildDir,{recursive:true});await fs.mkdir(path.join(W,"exports"),{recursive:true});
const candidate=path.join(buildDir,"candidate_regular.pptx");await(await PresentationFile.exportPptx(ppt)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,"container_tools/artifact_tool_utils.mjs")).href);
await finalizePresentation({workspaceDir:W,candidatePath:candidate,finalPath:path.join(W,"exports","project_report_regular_editable_v2.pptx"),pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,"container_tools/inspect_presentation_package_integrity.py"),layoutValidatorPath:path.join(SKILL,"container_tools/inspect_presentation_layout_geometry.py"),layoutArgs:["--expected-slide-size-emu","12192000,6858000","--validate-heading-fit"],explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:"design",families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(buildDir,"project_report_regular_editable_v2.validation.json")});
