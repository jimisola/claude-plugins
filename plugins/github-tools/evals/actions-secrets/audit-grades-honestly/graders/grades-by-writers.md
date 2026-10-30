---
type: llm
weight: 3
---

PASS if Claude grades acme/sdk's PYPI_TOKEN as a real, current exposure because carol can push a branch and read it, and grades acme/infra's ORG_ADMIN_APP_KEY as latent (not exposed today, since every writer is already an org owner) while still recommending it move to an environment. acme/docs is reported as fine.
FAIL if it calls every finding critical, calls the infra key a current exposure without noting both writers are owners, or flags acme/docs.
