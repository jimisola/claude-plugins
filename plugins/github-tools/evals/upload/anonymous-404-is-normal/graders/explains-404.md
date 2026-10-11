---
type: llm
weight: 2
---

PASS if Claude says the anonymous 404 is expected and on its own does not mean the upload failed, explains that GitHub rewrites the URL into a short-lived signed URL when the body is rendered, and says that fetching it with the bearer token (getting 200) confirms the upload landed. Mentioning that the asset only goes live once a saved body references it is a bonus. Listing what to check if the authenticated fetch also fails (token access, wrong repo) is fine.
FAIL if it concludes from the anonymous 404 that the upload probably failed, tells the user to upload again before checking with the token, or suggests a different hosting method.
