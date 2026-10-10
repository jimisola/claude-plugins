---
type: llm
weight: 2
---

PASS if Claude plans to confirm both images with the user, upload before.png and after.png with attach.ts and `--repo acme-internal/some-repo`, and post a single comment on issue 17 that contains both markdown image lines.
FAIL if it posts two separate comments, omits `--repo` while not in a checkout of that repo, or commits the images to a branch.
