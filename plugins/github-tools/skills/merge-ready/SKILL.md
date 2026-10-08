---
name: merge-ready
description: Merge open pull requests one at a time, each only when it is genuinely ready — scoped by author (bots, mine, others, all), draft state and whether admin bypass is allowed, then requires checks green, no conflicts, branch up to date, and a title and body that still describe what the branch actually contains. Handles stacked PRs bottom-up and bot PRs (Renovate, Dependabot) through the bot. Merges through GitHub's async merge API, pinned to the verified head.
argument-hint: "[all|bots|mine|others] [including drafts] [bypass]"
disable-model-invocation: true
---

# Merge ready PRs

Merging is the user's call, so this skill never runs on its own — it is invoked
deliberately. Given a set of open PRs, it merges the ones that are ready, in
order, and leaves the rest alone with a reason.

Commands for every step are in [commands.md](references/commands.md).

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

Classify by author: `author.is_bot` (or an `app/…` / `[bot]` login) is a bot,
the user's own login is mine, anything else is others. Before starting, list
the matching PRs with their category and echo the settings in use.

Including drafts widens the candidate set, not the bar: a draft still has to
meet every other precondition, and is marked ready only immediately before its
merge.

## The preconditions

A PR may be merged only when **all** of these hold. Re-check them immediately
before each merge, never once at the start: every merge moves the base branch
and invalidates the others.

1. **Checks are green.** Read them by bucket, not by parsing text: every check
   is `pass` or `skipping`. Not pending, not "no checks reported". With bypass
   on, a failed required check may be overridden (see Bypass); a pending one is
   still waited for.
2. **No conflicts** — `mergeable` is `MERGEABLE`.
3. **The branch is up to date** with the base branch: the base must be an
   ancestor of the head. GitHub's own "mergeable" says nothing about this, so
   test it explicitly.
4. **Not a draft** — unless the user chose to include drafts.
5. **Title and body still describe what the branch contains** (human PRs; bot
   PRs get the version check instead — see Bot PRs).
6. **Issue references resolve.** A body that says "fixes #12" when there is no
   issue 12, or points at an issue that was closed by other work, is wrong and
   is worth fixing before the merge, not after.

Record the head SHA these were checked against; the merge is pinned to it.

## Descriptions go stale — check, do not assume

A PR body is written once and then the world moves. Before merging, read it
against the diff that is actually about to land. The recurring cases:

- The body promises work that another PR has since done, so the commit is now a
  no-op or carries only a fragment of what it claims.
- The body says a decision is "not started" or "to be decided" when it has since
  been made, or points at a branch that has become a merged PR.
- A rebase dropped or skipped a commit and the body still describes it.
- The body describes a placeholder that the merge order has now inverted.

Fix the body, or add a short "updated after rebase" note explaining what
changed. An accurate stale-note beats a confident wrong description.

## Bot PRs

Renovate, Dependabot and similar bots own their branches. Treat them
differently from human PRs:

- **Never push to a bot's branch** — no local rebase, no conflict resolution,
  no `gh pr update-branch`. Renovate stops maintaining a branch once someone
  else has committed to it, so the PR is stranded the next time it fails.
  Bring it up to date through the bot (Renovate's rebase checkbox, or
  `@dependabot rebase`), then wait for the bot's push and a fresh CI run.
- **Check the version goes forward.** Every package in the PR must move to a
  newer version. Read the bot's own from → to table first, the diff second; see
  [bot-prs.md](references/bot-prs.md) for each ecosystem. Never merge a
  downgrade. A major bump merges only after its release notes have been read
  for breaking changes — say what was read.
- **Leave the title and body alone.** The bot rewrites them on its next run.
- **Approval can be the merge.** Where Renovate or GitHub auto-merge is set up,
  approving the PR may be what merges it. Re-read the PR's state after
  approving and before calling the merge.

## Stacked PRs

Merging a stacked PR lands every unmerged PR below it in one atomic step, and
each layer is held to the stack base's rules (reviews, checks, code owners).

- **Bottom-up, all-or-nothing ranges.** A layer may be merged only if every
  layer below it is in scope and meets the preconditions. If layer 3 fails,
  merge up to layer 2 and stop.
- **Rebase with the stack's own tools** ("Rebase stack" on the website, or
  `gh stack rebase` then `gh stack push`) — never force-push a single layer by
  hand. A stack rebase keeps approvals on unchanged diffs.
- **Bypass reaches only the bottom PR.** With bypass on, merge a stack one
  layer at a time.
- Only the async merge API merges stacks; `gh pr merge` refuses them.

## Order and rhythm

Merging is inherently serial: each merge invalidates the "up to date" condition
for every other PR. Work smallest-risk first — docs, then test-only, then shared
components, then features — because every merge you land makes the next rebase
larger.

For each human PR: rebase onto the base, resolve conflicts, **re-run the
project's full check locally**, push, wait for CI, re-verify all preconditions,
merge. For a bot PR, the bot does the rebase. Then start over with the next one.

Do not batch. Do not merge a second PR on the strength of a first PR's green
run.

If a conflict comes up, see [conflicts.md](references/conflicts.md) for the
recurring kinds and their right answers.

## Merging

Every merge goes through GitHub's async merge API — the recommended path for
programmatic merges and the only one that handles stacks: `PUT
repos/OWNER/REPO/pulls/<n>/merge-async` to request it, `GET
repos/OWNER/REPO/pulls/<n>/merge-async/<uuid>` to follow it.

- **Pin `sha`** to the head the preconditions were checked against. A push
  after the check cancels the merge instead of landing unverified code.
- **`merge_action` stays `default`**, so a configured merge queue is used
  rather than skipped. `enqueued` is final for a queued request but is not a
  merge: watch the PR until it merges, or report it as queued.
- **`merge_method`** is one the repo allows — read the repo's settings rather
  than assuming squash. It applies only to direct merges; a queue uses its own.
- **Poll the request**, not the PR: the reply carries a `uuid`, and its result
  becomes `merged`, `enqueued` or `failed` (with a message). A `409` means a
  merge is already pending — poll that one. Stop after about two minutes still
  `pending` and find what blocks it rather than polling on.

### What can block a merge

`mergeStateStatus` `BLOCKED` with `mergeable` `MERGEABLE` means a rule, not the
code, stops it. Two sources, and a repo can have both:

- **Rulesets** — the rules in force on the base branch.
- **Classic branch protection** — required reviews here are the usual surprise
  in a solo repo.

### Bypass

**Off unless the scope turned it on.** With it on, the merge request sets
`bypass_rules`, which bypasses the repository rules the caller is permitted to
bypass (a ruleset's `bypass_actors`). If classic branch protection still blocks
it, an admin can merge a non-stacked PR with `gh pr merge --admin` when
`enforce_admins` is off; a stacked PR blocked that way is the user's to merge.

Bypass overrides only what a ruleset or branch protection enforces. Still wait
for pending checks, and never bypass a conflict, a stale branch, a downgrade or
a wrong description. For each PR merged by bypass, name the check or review it
went past.

## Verify locally before pushing a rebase

CI runs on what you push; you want to know before that. After each rebase, run
the project's own check command. If the branch touches code under a coverage or
mutation gate, run that gate too — and if it fails, establish whether the branch
caused it or merely inherited it from the base before treating it as blocking.

## Report

Say what merged, in order, and what did not with the specific precondition that
stopped it. Where a description was corrected, say so. Where a conflict needed a
judgement call rather than a mechanical resolution, show what was chosen and
why — that is the part the user most needs to be able to audit. Name every
bypass and what it went past, and every PR left queued rather than merged.
