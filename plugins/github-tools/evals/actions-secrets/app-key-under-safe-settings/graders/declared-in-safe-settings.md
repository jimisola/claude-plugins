---
type: llm
weight: 3
---

PASS if Claude declares the new environment in safe-settings (e.g. `safe-settings/repos/mirror.yml` in acme/.github, or the suborg file) with a deployment branch policy of `main` and no required reviewers, and explains that otherwise the environments plugin would delete the environment and its secret on the next sync.
FAIL if it creates the environment only by API or UI, adds required reviewers to it, or leaves it without a branch policy.
