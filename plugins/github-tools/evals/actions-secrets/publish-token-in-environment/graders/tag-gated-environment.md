---
type: llm
weight: 3
---

PASS if Claude puts NPM_TOKEN in an environment (not a repository secret), has the `publish` job declare `environment:`, limits the environment's deployment policy to `v*` tags, and points out that a tag ruleset is needed so a writer cannot push a matching tag. The environment is created and protected before or together with the workflow change.
FAIL if it sets NPM_TOKEN as a repository or organization secret, leaves the environment without a tag policy, or references the environment in the workflow before the environment is configured.
