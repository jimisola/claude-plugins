---
type: llm
focus: trace
weight: 2
---

PASS if, before deciding to merge any PR, Claude asks the user (with AskUserQuestion or in its reply) three things: whose PRs (bots / mine / others, with an All option), ready only or including drafts, and whether admin bypass is allowed.
FAIL if it merges or plans merges without asking, assumes a scope, or asks only some of the three.
