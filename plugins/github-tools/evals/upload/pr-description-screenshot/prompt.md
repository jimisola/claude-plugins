---
description: A screenshot for a PR description is uploaded with attach.ts and saved into the PR body, after the user has confirmed it.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. The current directory is a checkout of acme/widgets. You are logged in to github.com with gh, with push access to the repositories named."
---

Add this screenshot to the description of PR #42: ./shot.png
