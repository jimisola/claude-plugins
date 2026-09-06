# Evidence — why the precondition is not optional

All timestamps UTC, read from the GitHub API after the fact (check-run `completed_at`,
PR `mergedAt`, review `submittedAt`). Repos are named only where the owner's orgs are
public; the pattern is what matters.

## The failure, observed twice

| Where | What | Order of events |
|---|---|---|
| A config repo's own CI, 2026-05 | `platformAutomerge: true`, ruleset with **no** required checks | Three minor/patch PRs merged before `build` ran; three failing builds landed on `main`. |
| An org admin repo, 2026-09-05 | same shape, one path-filtered check, none required | PR created 01:49:05, **merged 01:49:11** (6 s), its only check completed **01:49:34** — 23 s *after* the merge. |

Auto-merge had nothing to wait for. Nothing looked wrong: the PRs were green *eventually*
and showed as merged.

## The fix, observed on the same PR shape

Same admin repo, same bot, same update type, 24 h later, with the check now required:

| Event | Time |
|---|---|
| PR created | 01:25:12 |
| check completed | 01:25:47 |
| **merged** | **01:25:52** — 5 s *after* the check |

## Live proofs across the rollout

| Repo kind | Open → approval | Last required check → merge | Notes |
|---|---|---|---|
| Java/Gradle app (free-plan org) | 27 s | 12 s | 5 required checks incl. DCO; ~10 min end to end |
| same repo, next PR | — | **2 s** | merged with a *non-required* check failing — proof that only the required set gates |
| ESP-IDF firmware fork (user account) | 2 s | 20 s | 8 required checks, firmware build last (~7 min) |
| Java/Spring product repo | seconds | seconds | 13 required checks incl. CodeQL ×4, DCO |

## The manual tier, observed

Five major PRs (an actions bump, setup-java v5, action-gh-release v3, checkstyle v11/v12)
opened on the same visit: all `REVIEW_REQUIRED`, no `renovate-approve` review, no
auto-merge request — because the config never marked them for automerge. The day before,
with a manager rule that carried `automerge: true`, an `actions/checkout` v4→v5 major had
merged unattended.

## Grouping, observed

After removing a `{{groupId}}`-templated catch-all group, the next visit closed the
grouped "update packages" PR and opened one PR per dependency. The same catch-all had
also been overriding the named groups above it, so those had been dead config.
