---
type: llm
weight: 2
---

PASS if the steps come in this order: the environment is declared (in safe-settings) before or together with the workflow change that adds `environment:` to the job; then the environment secret is set; then the repository secret `MIRROR_APP_KEY` is deleted; then a manual run from main (e.g. `gh workflow run nightly.yml --ref main`) proves it.
FAIL if the repository secret is deleted before the environment secret is set, the workflow references the environment before it is declared, or there is no manual run from main.
