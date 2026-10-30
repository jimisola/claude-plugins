---
description: An App key moves to an environment declared in safe-settings, in the order that never breaks the nightly run.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. You can read the skill's files but cannot call the GitHub API. acme/mirror has .github/workflows/nightly.yml, on schedule (02:00 daily) and workflow_dispatch, one job sync that mints a token with actions/create-github-app-token from vars.MIRROR_APP_ID and the repository secret MIRROR_APP_KEY. The acme-mirror App is installed on all acme repos with contents: write and administration: write. The acme org runs safe-settings from acme/.github, config path safe-settings/, and suborgs/product.yml (which matches acme/mirror) declares environments: [{name: github-pages}]. main on acme/mirror requires a reviewed PR."
---

MIRROR_APP_KEY shouldn't be a plain repo secret. Move it somewhere safer without breaking the nightly run.
