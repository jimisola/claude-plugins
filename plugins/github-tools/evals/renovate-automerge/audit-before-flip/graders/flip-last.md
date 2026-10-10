---
type: llm
weight: 3
---

PASS if Claude's ordered plan creates a ruleset on main with a complete required-check list before turning on platformAutomerge, and makes the flip the last step. The required list must include `DCO` and `lint`, and must not require `docs` (path-filtered) or `renovate/stability-days` (bot PRs only). It must say that `test (17)` and `test (21)` come from a matrix and need a non-matrix aggregator job (with `if: always()`) to require instead.
FAIL if it turns platformAutomerge on first or alongside, requires `docs` or `renovate/stability-days`, requires the matrix legs directly, or proposes a bypass for Renovate.
