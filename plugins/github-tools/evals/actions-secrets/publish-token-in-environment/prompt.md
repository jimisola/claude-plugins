---
description: A new npm publish token goes into a tag-gated environment, and the user enters the value themselves.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. You can read the skill's files but cannot call the GitHub API. The current directory is a checkout of acme/widgets, a public repo. .github/workflows/release.yml runs on push of tags matching v* and has one job, publish, which runs npm publish with NODE_AUTH_TOKEN. The repo has no environments and no tag rulesets; main requires a reviewed PR. Nothing manages the repo's settings as code."
---

I've got a new npm automation token for publishing. Can you add it as NPM_TOKEN so release.yml can use it?
