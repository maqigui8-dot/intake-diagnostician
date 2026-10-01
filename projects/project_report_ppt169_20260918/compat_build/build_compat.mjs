import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/Administrator/Desktop/project/intake-diagnostician/projects/project_report_ppt169_20260918";
const skillDir = "C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations";
const pythonExecutable = "C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const pngDir = path.join(workspaceDir, "compat_png");
const notesDir = path.join(workspaceDir, "notes");
const stagingDir = path.join(workspaceDir, "compat_build", ".codex-finalizer");
const finalPath = path.join(workspaceDir, "exports", "中医诊前信息采集与整理系统_兼容版.pptx");
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const files = (await fs.readdir(pngDir)).filter((f) => f.endsWith(".png")).sort();
for (const file of files) {
  const slide = presentation.slides.add();
  slide.background.fill = "#F7F5EF";
  slide.images.add({
    blob: new Uint8Array(await fs.readFile(path.join(pngDir, file))),
    contentType: "image/png",
    alt: file.replace(".png", ""),
    fit: "contain",
    position: { left: 0, top: 0, width: 1280, height: 720 },
  });
  const noteFile = file.replace(".png", ".md");
  const note = await fs.readFile(path.join(notesDir, noteFile), "utf8");
  slide.speakerNotes.textFrame.setText(note);
}

const candidatePath = path.join(stagingDir, "candidate_compat.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);
await finalizePresentation({
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit"],
  explicitTotalSlideCount: 14,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "compat.validation.json"),
});
console.log(finalPath);
