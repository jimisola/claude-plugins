// PreToolUse hook (Bash matcher): enforcement layer for the /upload skill.
// hooks.json gates this with `if` conditions (permission-rule syntax), so the
// process only spawns for commands mentioning attach.ts or the upload endpoint
// — not on every Bash call. The command checks below are kept anyway: they
// make the hook self-contained if the `if` field is absent or unsupported.
// SKILL.md's constraints are guidance to the model; this hook is what actually
// stops a disguised file from leaving the machine, and it logs every upload
// invocation (timestamp, cwd, files, verification result) to
// ~/.claude/github-tools-uploads.jsonl.
//
// Exit codes: 0 = allow, 2 = block (stderr is shown to the model).

import { appendFileSync, mkdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { isAbsolute, join, resolve } from "node:path";
import process from "node:process";
import { contentTypeFor, matchesMagic, uploadFilesFromCommand } from "../skills/upload/scripts/lib.ts";

interface HookInput {
  tool_name?: string;
  tool_input?: { command?: string };
  cwd?: string;
}

function block(message: string): never {
  console.error(message);
  process.exit(2);
}

let input: HookInput;
try {
  input = JSON.parse(readFileSync(0, "utf8"));
} catch {
  process.exit(0); // malformed input is not this hook's problem
}

const command = input.tool_input?.command ?? "";
if (!command) process.exit(0);

// Raw calls to the upload endpoint bypass the skill's content verification —
// force them through attach.ts, which checks magic bytes and is covered here.
const files = uploadFilesFromCommand(command);
if (files === undefined) {
  if (command.includes("uploads.github.com/user-attachments")) {
    block(
      "Direct calls to uploads.github.com/user-attachments are blocked. " +
        "Use the github-tools /upload skill script (scripts/attach.ts) so the file " +
        "content is verified and the upload is logged.",
    );
  }
  process.exit(0);
}

const cwd = input.cwd ?? process.cwd();
const checked: Array<{ file: string; mime?: string; verified: boolean; reason?: string }> = [];

for (const file of files) {
  if (file.includes("$")) {
    checked.push({ file, verified: false, reason: "unresolved shell variable" });
    continue;
  }
  const path = isAbsolute(file) ? file : resolve(cwd, file);
  const mime = contentTypeFor(path);
  if (!mime) {
    checked.push({ file, verified: false, reason: "extension not allowed" });
    continue; // attach.ts rejects it too; let its error surface
  }
  let bytes: Uint8Array;
  try {
    bytes = readFileSync(path);
  } catch {
    checked.push({ file, mime, verified: false, reason: "unreadable" });
    continue; // attach.ts reports missing files itself
  }
  if (!matchesMagic(bytes, mime)) {
    checked.push({ file, mime, verified: false, reason: "magic-byte mismatch" });
    log("blocked");
    block(
      `${file}: content does not match its extension (claimed ${mime}). ` +
        "Upload blocked — a renamed non-media file must never be attached.",
    );
  }
  checked.push({ file, mime, verified: true });
}

log("allowed");
process.exit(0);

function log(outcome: string): void {
  try {
    const dir = join(homedir(), ".claude");
    mkdirSync(dir, { recursive: true });
    appendFileSync(
      join(dir, "github-tools-uploads.jsonl"),
      JSON.stringify({ ts: new Date().toISOString(), outcome, cwd, command, files: checked }) + "\n",
    );
  } catch {
    // logging must never break the tool call
  }
}
