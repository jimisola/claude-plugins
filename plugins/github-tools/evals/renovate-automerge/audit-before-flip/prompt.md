---
description: An audit lists what is missing, with a complete required-check list first and the platformAutomerge flip last.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. You can read the skill's files but cannot call the GitHub API. Here is what the audit found for acme/widgets, a public repo in the acme org, default branch main: GET rules/branches/main returns [] (no rules in force). Workflows triggered by pull_request: ci.yml job `lint` (no path filter) and job `test` with strategy.matrix java: [17, 21]; docs.yml job `docs` with paths: ['docs/**']. Check-runs on the newest Renovate PR head: lint (app 15368), test (17) (app 15368), test (21) (app 15368), DCO (app 1861), renovate/stability-days (app 2740). Repo flags: allow_auto_merge false, squash and merge commits both allowed, delete_branch_on_merge false. renovate.json: extends the org preset, platformAutomerge false, automerge true for minor and patch, no minimumReleaseAge."
---

Audit acme/widgets for the Renovate auto-merge setup we use on the other repos and tell me exactly what is missing before it is safe to turn platformAutomerge on there. Read-only — do not change anything.
