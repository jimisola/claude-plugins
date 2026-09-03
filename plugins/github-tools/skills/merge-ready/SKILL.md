---
name: merge-ready
description: Merge open pull requests one at a time, each only when it is genuinely ready — checks green, no conflicts, branch up to date, not a draft, and a title and body that still describe what the branch actually contains. Rebases and re-verifies between merges.
disable-model-invocation: true
---

# Merge ready PRs

Merging is the user's call, so this skill never runs on its own — it is invoked
deliberately. Given a set of open PRs, it merges the ones that are ready, in
order, and leaves the rest alone with a reason.

## The preconditions

A PR may be merged only when **all** of these hold. Re-check them immediately
before each merge, never once at the start: every merge moves the base branch
and invalidates the others.

1. **Checks are green.** Not "pending", not "no checks reported" — actually
   passed.
2. **No conflicts** — `mergeable` is `MERGEABLE`.
3. **The branch is up to date** with the base branch: the base must be an
   ancestor of the head. GitHub's own "mergeable" says nothing about this, so
   test it explicitly.
4. **Not a draft.**
5. **Title and body still describe what the branch contains.** This is the one
   a machine cannot check for you — see below.
6. **Issue references resolve.** A body that says "fixes #12" when there is no
   issue 12, or points at an issue that was closed by other work, is wrong and
   is worth fixing before the merge, not after.

```bash
gh pr view <n> --json isDraft,mergeable,statusCheckRollup
git fetch origin && git merge-base --is-ancestor origin/<base> origin/<head> \
  && echo up-to-date || echo behind
```

## Descriptions go stale — check, do not assume

A PR body is written once and then the world moves. Before merging, read it
against the diff that is actually about to land. The recurring cases:

- The body promises work that another PR has since done, so the commit is now a
  no-op or carries only a fragment of what it claims.
- The body says a decision is "not started" or "to be decided" when it has since
  been made, or points at a branch that has become a merged PR.
- A rebase dropped or skipped a commit and the body still describes it.
- The body describes a placeholder ("derived from content until the column
  exists") that the merge order has now inverted.

Fix the body, or add a short "updated after rebase" note explaining what
changed. An accurate stale-note beats a confident wrong description.

## Order and rhythm

Merging is inherently serial: each merge invalidates the "up to date" condition
for every other PR. Work smallest-risk first — docs, then test-only, then shared
components, then features — because every merge you land makes the next rebase
larger.

For each PR: rebase onto the base, resolve conflicts, **re-run the project's
full check locally**, push, wait for CI, re-verify all preconditions, merge. Then
start over with the next one.

Do not batch. Do not merge a second PR on the strength of a first PR's green
run.

## Merging

`gh pr merge` refuses stacked PRs ("Merging stacked PRs via this endpoint is not
supported"), and `--admin` is a flag on that same command, so it never gets the
chance to help. The asynchronous endpoint works for both stacked and ordinary
PRs:

```bash
gh api --method PUT repos/OWNER/REPO/pulls/<n>/merge-async \
  -f merge_method=squash -f merge_action=direct_merge
```

It answers `{"status":"pending"}` and lands a few seconds later — poll rather
than reading that as failure:

```bash
until [ "$(gh pr view <n> --json state -q .state)" = "MERGED" ]; do sleep 4; done
```

`merge_action` also takes `merge_queue` and `default`; `direct_merge` means now.

**Never bypass a failing check.** Bypass authority comes from the ruleset's
`bypass_actors`, not from a flag, and using it means merging something the
project said was not ready. If the user has explicitly approved an override for
a specific PR, say plainly which precondition is being overridden and why.

## Conflicts that recur

Most conflicts in an active repo are mechanical, but each has a right answer:

- **Decision-log and changelog rows** (`plan.md` and friends): both sides added
  different rows. Keep both — dropping either loses a decision. Strip the
  markers, re-run the formatter, verify the row count grew.
- **i18n / JSON resources**: both sides added keys to the same object. Keep both
  sets, then **validate the file parses** — the seam between two added blocks
  routinely loses a comma, and a broken JSON resource is not caught by a type
  check. Then confirm key-set parity across languages if the project enforces it.
- **A file the base branch now owns**: if a branch created its own copy of
  something that has since landed on the base, take the base's version and
  **skip** the branch's later commit that deletes it — replaying that deletion
  removes the real file. Verify afterwards that the branch leaves no diff on it.
- **Migration numbering**: two branches both adding `NNNN_*` is invisible to git
  (different filenames) and fatal to the migration runner. The second one to
  merge must renumber — prefer regenerating with the migration tool over hand
  editing, because a hand-edited snapshot chain breaks silently, and re-run the
  migration's verification against a **populated** database afterwards, not a
  fresh one.
- **A formatter that will not converge**: if `format --write` followed by
  `format --check` keeps failing, the file has a construct the formatter is not
  idempotent on (deeply indented nested lists are a common one). Restructure the
  content rather than reformatting again.

## Verify locally before pushing a rebase

CI runs on what you push; you want to know before that. After each rebase, run
the project's own check command. If the branch touches code under a coverage or
mutation gate, run that gate too — and if it fails, establish whether the branch
caused it or merely inherited it from the base before treating it as blocking.

## Report

Say what merged, in order, and what did not with the specific precondition that
stopped it. Where a description was corrected, say so. Where a conflict needed a
judgement call rather than a mechanical resolution, show what was chosen and
why — that is the part the user most needs to be able to audit.
