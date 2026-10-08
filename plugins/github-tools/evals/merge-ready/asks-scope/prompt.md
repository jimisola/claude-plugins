---
description: With no arguments, merge-ready asks all three scope questions before acting.
max_turns: 8
allowed_tools: [Skill, Read, AskUserQuestion]
append_system_prompt: "This is a dry run of a merge, in a test harness. You have no shell and must not try to run commands. For each PR in scope, state your decision, the reason, and the exact commands you would run, in order. The repository is acme/widgets, base branch main, and you are logged in to GitHub as alex. Open PRs: #5 by renovate[bot] (bot, ready, green), #6 by alex (ready, green), #7 by sam (draft, green)."
---

/github-tools:merge-ready
