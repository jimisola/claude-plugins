---
description: A patch PR that merged before CI is traced to a ruleset that matches nothing, verified against the rules in force.
max_turns: 8
allowed_tools: [Skill, Read]
append_system_prompt: "This is a dry run in a test harness. You have no shell and must not try to run commands, and files the user mentions are in their checkout but not available to you here. Describe what you would do and the exact commands you would run, in order. Where you would stop to ask the user something, say so and what you would ask. You can read the skill's files but cannot call the GitHub API. Facts: safe-settings declares a ruleset `main-protection` for acme/widgets with required checks lint (15368), test (15368) and DCO (1861), and the last safe-settings sync run was green. GET repos/acme/widgets/rulesets lists `main-protection` as active. GET repos/acme/widgets/rulesets/<id> shows conditions.ref_name.include: [] and exclude: []. GET repos/acme/widgets/rules/branches/main returns []. renovate.json has platformAutomerge true."
---

Our org's safe-settings config declares required checks for acme/widgets but a Renovate patch PR just merged 20 seconds after it opened, before CI finished. Figure out why and fix it.
