---
description: A bot PR behind its base is brought up to date by the bot, never by pushing to its branch.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run of a merge, in a test harness. You have no shell and must not try to run commands. For each PR in scope, state your decision, the reason, and the exact commands you would run, in order. The repository is acme/widgets, base branch main, and you are logged in to GitHub as alex. Open PRs: #21 by dependabot[bot], title 'Bump lodash from 4.17.20 to 4.17.21', ready, all checks pass, no conflicts, but 3 commits behind main (main is not an ancestor of the head). Head SHA 9f1c2ab. Repo allows squash merges only; no merge queue."
---

/github-tools:merge-ready bots
