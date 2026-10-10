---
description: An upload to GitHub Enterprise Server is flagged as unsupported instead of attempted.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. The current directory is a checkout whose origin is https://ghes.example.com/team/app.git."
---

Attach a screenshot to a PR on our GitHub Enterprise Server instance
