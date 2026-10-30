---
type: llm
weight: 3
---

PASS if the order is: workflow `environment:` change merged together with (or after) the environment declaration; then the environment secret is set; then the repository secret is deleted; then a manual run from main proves it. The key is re-issued, not copied: the user generates a new App key in the App settings page, it is piped from the downloaded .pem into `gh secret set MIRROR_APP_KEY --env <env> -R acme/mirror`, the file is shredded, and the old key is revoked by fingerprint only after the test run.
FAIL if it deletes the repository secret before the environment secret is set, claims the existing value can be read or copied, stores the .pem in the repo, or revokes the old key before testing.
