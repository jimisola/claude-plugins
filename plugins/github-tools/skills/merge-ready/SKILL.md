---
name: merge-ready
description: Merge open pull requests one at a time, each only when it is genuinely ready — scoped by author (bots, mine, others, all), draft state and whether admin bypass is allowed, then requires checks green, no conflicts, branch up to date, and a title and body that still describe what the branch actually contains. Rebases and re-verifies between merges.
argument-hint: "[all|bots|mine|others] [including drafts] [bypass]"
disable-model-invocation: true
---

# Merge ready PRs

Merging is the user's call, so this skill never runs on its own — it is invoked
deliberately. Given a set of open PRs, it merges the ones that are ready, in
order, and leaves the rest alone with a reason.

## Settle the scope first

Three settings, taken from the arguments where given:

| Setting | Values | Argument words |
|---|---|---|
| Whose PRs | all, or any of bots / mine / others | `all`; `bots`/`bot`; `mine`/`author`/`personal`; `others` |
| Which state | ready only, or ready + drafts | `drafts`, `including drafts` |
| Admin bypass | off, or on | `bypass`, `admin` |

"Others" means human authors who are not the user: collaborators and outside
contributors.

- **No arguments**: ask all three in one `AskUserQuestion` call. Whose PRs is
  multi-select with `All` as its first option.
- **Arguments given**: they are the answer. A missing state means ready only and
  a missing bypass means off; ask only if whose PRs is missing.

Classify by the author in `gh pr list --json number,title,author,isDraft`:
`author.is_bot` (or an `app/…` / `[bot]` login) is a bot, `author.login` equal
to `gh api user -q .login` is mine, anything else is others. Before starting,
list the matching PRs with their category and echo the settings in use.

Including drafts widens the candidate set, not the bar: a draft still has to
meet every other precondition, and is marked ready (`gh pr ready <n>`) only
immediately before its merge.

## The preconditions

A PR may be merged only when **all** of these hold. Re-check them immediately
before each merge, never once at the start: every merge moves the base branch
and invalidates the others.

1. **Checks are green.** Not "pending", not "no checks reported" — actually
   passed. With bypass on, a failed required check may be overridden (see
   Merging); a pending one is still waited for.
2. **No conflicts** — `mergeable` is `MERGEABLE`.
3. **The branch is up to date** with the base branch: the base must be an
   ancestor of the head. GitHub's own "mergeable" says nothing about this, so
   test it explicitly.
4. **Not a draft** — unless the user chose to include drafts (see above).
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
than reading that as failure, but with a limit: a merge a rule still blocks is
accepted as pending too, and then never lands.

```bash
for i in $(seq 30); do
  [ "$(gh pr view <n> --json state -q .state)" = MERGED ] && break; sleep 4
done
gh pr view <n> --json state,mergeStateStatus
```

Still open after two minutes with `mergeStateStatus` `BLOCKED` means a rule is
in the way: stop, find it (below) and report it rather than polling on.

`merge_action` also takes `merge_queue` and `default`; `direct_merge` means now.

### What can block a merge

Check `mergeStateStatus` before calling `merge-async`; `BLOCKED` with
`mergeable` `MERGEABLE` means a rule, not the code, stops it. Two sources, and
a repo can have both:

- **Rulesets** — `gh api repos/OWNER/REPO/rules/branches/<base>` lists every
  rule in force on the base branch.
- **Classic branch protection** — `gh api repos/OWNER/REPO/branches/<base>/protection`
  (404 means none). Required reviews here are the usual surprise in a solo repo.

**Admin bypass is off unless the scope turned it on.** How it works depends on
the source:

- **Ruleset**: authority comes from its `bypass_actors`, not a flag — check
  `gh api repos/OWNER/REPO/rulesets/<id>`. `merge-async` merges past ruleset
  blocks when the caller is a bypass actor.
- **Classic protection**: admins may bypass only when `enforce_admins` is off,
  and `merge-async` does not do it — it enqueues with `"bypass_rules": false`
  and stays pending. Use `gh pr merge <n> --squash --admin` instead; that
  cannot merge a stacked PR, so a stacked PR blocked this way is the user's to
  merge.

With bypass on, it overrides only what a ruleset or branch protection enforces. Still wait for
pending checks to finish, and never bypass a conflict, a stale branch or a
wrong description. For each PR merged by bypass, name the check or review it
went past.

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
