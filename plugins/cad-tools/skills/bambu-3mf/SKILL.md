---
name: bambu-3mf
description: Writes Bambu Studio project 3MFs from STL/OBJ/STEP meshes, with the printer, process and filament presets and setting overrides (supports, infill, walls, brim, temperature) already applied, so the file opens ready to slice. Use when the user asks for a 3MF for Bambu Studio or a Bambu Lab printer (X1, P1, P2S, A1, H2D), wants print settings baked into the file, or gets "The 3mf file has invalid config, load geometry data only" when opening a 3MF.
---

## Why this route

- **Never hand-write the 3MF's config.** A 3MF with `model_settings.config` but no full `project_settings.config` opens with "invalid config, load geometry data only" and drops every setting.
- **List the changed keys, or the GUI drops them.** When the user slices in the Bambu window, it rebuilds each preset from the system preset plus the keys named in `different_settings_to_system`. The CLI leaves that list empty, so the file looks right until it is sliced, and then it slices with stock settings. The script fills the list in. A headless `--slice` reads the full config, so it does not catch this.
- **Bambu Studio's own CLI writes the project** from its presets. The script flattens the preset `inherits` chains (system presets, then the user's own under `~/.config/BambuStudio/user/<id>/`), applies the overrides and runs the CLI headless.
- **Requirements:** Bambu Studio installed (AppImage, PATH, or `BAMBU_STUDIO`/`--bambu`), and Python 3 with the standard library only. It has to have been started once, so the presets are on disk.

## Workflow

1. **Find the preset names** with `python3 ${CLAUDE_SKILL_DIR}/scripts/bambu_3mf.py --list printer --grep P2S`, then the same with `process` and `filament`. Names must match exactly.
2. **Export** with `python3 ${CLAUDE_SKILL_DIR}/scripts/bambu_3mf.py part.stl --printer … --process … --filament … --set KEY=VALUE … -o out.3mf`. Each mesh becomes its own 3MF unless `--one` puts them all on one plate.
3. **Read the result.** The script reads each 3MF back and prints `NOT APPLIED` for any override that did not land. It exits non-zero on that or on a CLI rejection.
4. **Keep the call next to the model.** For a repeatable export, save it as a small script beside the model, not in a scratchpad.

## Rules

- **Keep the modelled orientation.** The default is no auto-orient, because the model is usually already laid out for supportless printing. `--orient` hands it to Bambu.
- **Overrides use Bambu's own keys and values.** Read them from a preset JSON or from `Metadata/project_settings.config` in a Bambu-saved 3MF. Useful ones: `enable_support=0`, `sparse_infill_density=100%`, `sparse_infill_pattern=zig-zag` (Rectilinear), `wall_loops=4`, `brim_type=outer_only`, `brim_width=5`. Use `--set-filament nozzle_temperature=260` for the filament.
- **Bambu validates combinations and refuses bad ones.** For example, "grid doesn't work at 100% density": set `sparse_infill_pattern=zig-zag` with 100% infill. The script prints Bambu's message, so fix the key it names.
- **The OSMesa or thumbnail error in the CLI log is harmless** headless. The project is still complete, though it has no plate preview image.
- **This writes one filament per object.** It does not assign parts of one object to different filaments (logo on filament 2). That needs a `model_settings.config` with a `<part>` per triangle range, built on top of a CLI-written project.
- **Open it for the user** in the Bambu Studio GUI when they ask. Start it detached with the 3MF path as its argument. To stop it, match with a bracketed pattern (`pkill -f "bambu[-]studio"`), because a plain pattern matches your own shell and kills the tool call.
