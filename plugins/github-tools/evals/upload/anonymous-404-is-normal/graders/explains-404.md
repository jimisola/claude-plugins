---
type: llm
weight: 2
---

PASS if Claude says the anonymous 404 is expected and does not mean the upload failed, explains that GitHub rewrites the URL into a short-lived signed URL when the body is rendered, and says that fetching it with the bearer token (getting 200) confirms the upload landed. Mentioning that the asset only goes live once a saved body references it is a bonus, not required.
FAIL if it says the upload probably failed, suggests uploading again, or suggests a different hosting method.
