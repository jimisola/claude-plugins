---
description: A silent Renovate on a fork is traced to the config not being at root renovate.json.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. You can read the skill's files but cannot call the GitHub API."
---

Renovate hasn't opened a single PR on my fork alex/case-sorter in over a month even though it has a .github/renovate.json5 with forkProcessing enabled. The Mend portal shows it as disabled. What's going on and what do I change?
