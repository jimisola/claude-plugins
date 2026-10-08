---
type: llm
weight: 2
---

PASS if Claude merges the stack only up to #32 (merging #32, which lands #31 with it, or #31 then #32), leaves #33 open naming the failed 'unit-tests' check, and uses the async merge API rather than `gh pr merge`.
FAIL if it plans to merge #33, merges #32 without #31 being ready, force-pushes a single layer, or uses `gh pr merge` for a stacked PR.
