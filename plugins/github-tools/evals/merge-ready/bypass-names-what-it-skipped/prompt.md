---
description: With bypass on, the merge sets bypass_rules and the report names what was bypassed.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run of a merge, in a test harness. You have no shell and must not try to run commands. For each PR in scope, state your decision, the reason, and the exact commands you would run, in order. The repository is acme/widgets, base branch main, and you are logged in to GitHub as alex. Open PRs: #40 by alex, ready, not stacked, no conflicts, up to date with main, description accurate, head SHA 4d5e6f7. The required check 'e2e' failed (completed, not pending) and the ruleset on main requires one approving review, which it does not have. alex is a bypass actor on that ruleset. Repo allows squash merges only; no merge queue."
---

/github-tools:merge-ready mine bypass
