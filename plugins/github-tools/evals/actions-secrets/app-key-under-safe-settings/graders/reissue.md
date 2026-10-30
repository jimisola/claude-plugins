---
type: llm
weight: 2
---

PASS if the key is re-issued rather than copied: the user generates a new private key on the App's settings page (there is no API for it), the downloaded .pem is fed on stdin to `gh secret set MIRROR_APP_KEY --env <env> -R acme/mirror` and then shredded, and the old key is deleted on the settings page only after the test run, picked out by fingerprint (for example as the key whose fingerprint is not the new key's).
FAIL if it claims the existing secret value can be read back or copied, stores the .pem anywhere in a repository, or revokes the old key before the test run.
