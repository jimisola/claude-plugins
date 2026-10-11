---
type: llm
weight: 2
---

PASS if Claude says Bambu rejects the grid pattern at 100% density and uses `sparse_infill_pattern=zig-zag` (or asks the user which non-grid pattern to use), passing overrides with `--set` to the bambu_3mf.py script.
FAIL if it keeps grid at 100% without comment, or hand-writes the 3MF config.
