---
description: A Renovate PR that moves a version backwards is never merged.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run of a merge, in a test harness. You have no shell and must not try to run commands. For each PR in scope, state your decision, the reason, and the exact commands you would run, in order. The repository is acme/widgets, base branch main, and you are logged in to GitHub as alex. Open PRs: #11 by renovate[bot], title 'chore(deps): update actions/checkout action to v4.1.7', ready, all checks pass, up to date with main, no conflicts. Its body table: | Package | Update | Change | / | actions/checkout | patch | `v4.2.2` → `v4.1.7` |. #12 by renovate[bot], title 'chore(deps): update dependency vitest to v3.2.4', ready, all checks pass, up to date, no conflicts, body change `3.2.3` → `3.2.4`. Repo allows squash merges only; no merge queue."
---

/github-tools:merge-ready bots
