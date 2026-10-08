---
description: A stack merges bottom-up and stops below the first layer that is not ready.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run of a merge, in a test harness. You have no shell and must not try to run commands. For each PR in scope, state your decision, the reason, and the exact commands you would run, in order. The repository is acme/widgets, base branch main, and you are logged in to GitHub as alex. Open PRs, all by alex and ready: #31, #32 and #33 form one stacked-PR stack, #31 at the bottom (base main), #32 on #31, #33 on #32. #31 and #32: all checks pass, no conflicts, up to date, descriptions accurate. #33: the required check 'unit-tests' failed. Repo allows squash merges only; no merge queue."
---

/github-tools:merge-ready mine
