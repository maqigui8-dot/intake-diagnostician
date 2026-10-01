import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/Administrator/Desktop/project/intake-diagnostician/projects/project_report_redesign_ppt169_20260918";
const skillDir = "C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations";
const pythonExecutable = "C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const sourcePath = path.join(workspaceDir, "exports", "project_report_redesign_20260918_142844.pptx");
const buildDir = path.join(workspaceDir, "editable_repair", ".codex-finalizer");
const candidatePath = path.join(buildDir, "candidate_normalized.pptx");
const finalPath = path.join(workspaceDir, "exports", "project_report_redesign_editable_fixed.pptx");

await fs.mkdir(buildDir, { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const snapshot = await presentation.inspect({ kind: "slide,textbox,shape,notes,layout", maxChars: 2000 });
await fs.writeFile(path.join(buildDir, "import_snapshot.ndjson"), snapshot.ndjson, "utf8");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const { finalizePresentation } = await import(pathToFileURL(
  path.join(skillDir, "container_tools/artifact_tool_utils.mjs"),
).href);
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
  fontPolicy: { basis: "design", families: ["Arial"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "editable_fixed.validation.json"),
});
console.log(finalPath);
