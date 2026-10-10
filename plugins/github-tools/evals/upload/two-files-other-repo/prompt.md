---
description: Two images for an issue in another repository go up with --repo and land in one comment.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. The current directory is not a git checkout of acme-internal/some-repo. You are logged in to github.com with gh, with push access to the repositories named."
---

Attach before.png and after.png to a comment on issue 17 in acme-internal/some-repo
