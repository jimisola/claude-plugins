---
name: turntable-video
description: Renders a looping 360° turntable video (MP4) and optional stills of a 3D model, for example CAD parts, STL/OBJ/GLB meshes, or an enclosure whose lid lifts off to show the board inside. Use when the user asks for a 360, turntable, spinning or rotating video, an exploded view, or renders of a 3D model or 3D print to share in Messenger, WhatsApp, Slack or a PR. Also use when FreeCAD or other GUI screenshots come out blank.
---

## What it makes

- **A square H.264 MP4**, 1080 px by default. It loops without a jump because it always runs whole turns.
- **With `--lift`**, the clip runs: closed for one turn, the named parts lift off, one open turn, they lower, one closed turn. That is 3 turns, 15 s at the defaults.
- **Size and sharing:** about 3–4 MB at 1080 px. It sends directly in Messenger and WhatsApp and plays inline, so the user needs no link.
- **Optional PNG stills** (`--stills DIR`): closed, open, front, back, both sides and top.

## Workflow

1. **Get each part as its own mesh file**, one per colour or per moving part, all in the same coordinate frame. STL, OBJ, PLY, GLB and VTK load directly. For STEP, FCStd, 3MF or a KiCad board, convert first using [converting.md](references/converting.md).
2. **Render** with `uv run --python 3.12 ${CLAUDE_SKILL_DIR}/scripts/turntable.py part.stl=#rrggbb … --lift <stem> -o out.mp4`. Add `--stills DIR` for still images. uv installs PyVista on first use.
3. **Look before handing it over.** Paste a few stills or frames into one contact sheet and Read it. Check the framing, that the colours tell the parts apart, and that the lifted part actually moves.
4. **Deliver the file path.** When the user wants it on their phone, also send it with the file-sending tool.

## Rules

- **Render with this script, not with GUI screenshots.** FreeCAD's `saveImage` and its MCP addon's screenshot both return a blank white image whenever the window is not on screen. Coin's offscreen renderer fails as well. This script renders offscreen through VTK and needs no window.
- **Name parts by file stem.** `--lift` takes stems (`lid` for `lid.stl`), and an unknown stem stops the run.
- **Colour parts by what they are.** Dark grey for connectors, green for PCBs, distinct colours for parts that come apart. When unset, colours come from a fixed palette.
- **Say when parts are stand-ins.** If connectors or modules are placeholder boxes, for example because a KiCad layout has no 3D models, tell the user the video shows stand-ins.
- **Choose the up axis.** Z-up is the default (CAD, STL); use `--up y` for GLB and most game-engine exports.
- **Requirements:** uv and ffmpeg. The script stops with an install hint if ffmpeg is missing. Never pip-install PyVista system-wide.

## Options worth knowing

`--turn-seconds` (default 5), `--turns`, `--fps` (30), `--size` (1080; use 720 to stay under about 2 MB), `--elev` (camera elevation, 28°), `--start-azimuth`, `--lift-mm` (default 1.4 × model height), `--no-edges`, `--bg`.
