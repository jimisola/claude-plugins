---
type: llm
weight: 2
---

PASS if Claude explains that the 3MF lacks a full project config, and plans to write a new 3MF from bracket.stl with the skill's bambu_3mf.py script (Bambu Studio's own CLI and presets), after looking up exact preset names with `--list`.
FAIL if it plans to hand-write or patch the 3MF's XML or config files, or tells the user to re-export the settings manually in the GUI instead.
