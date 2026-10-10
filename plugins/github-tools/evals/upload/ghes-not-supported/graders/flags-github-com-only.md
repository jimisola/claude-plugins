---
type: llm
weight: 2
---

PASS if Claude says the upload endpoint exists only on github.com, not on GitHub Enterprise Server, and does not plan to run the upload against the GHES instance.
FAIL if it plans the upload anyway, or suggests committing the image or using a release asset as a workaround.
