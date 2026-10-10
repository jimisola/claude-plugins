---
description: A 404 on an anonymous fetch of the returned URL is explained as normal, with the bearer-token check to confirm the upload.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask."
---

I uploaded an image with the script but curl on the returned URL gives 404 — did the upload fail?
