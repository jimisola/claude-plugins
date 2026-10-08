# merge-ready commands

`OWNER/REPO`, `<n>`, `<base>` and `<head>` are placeholders.

## Scope

```bash
gh api user -q .login
gh pr list --state open --json number,title,author,isDraft,baseRefName,headRefName \
  -q '.[] | [.number, .author.login, .author.is_bot, .isDraft, .title] | @tsv'
```

## Preconditions

```bash
# 1. checks: every bucket is pass or skipping (add --required to see the gate)
gh pr checks <n> --json name,bucket -q '.[] | select(.bucket != "pass" and .bucket != "skipping")'

# 2, 4, head SHA, and whether a rule blocks it
gh pr view <n> --json isDraft,mergeable,mergeStateStatus,headRefOid,baseRefName

# 3. up to date
git fetch origin && git merge-base --is-ancestor origin/<base> origin/<head> \
  && echo up-to-date || echo behind
```

`gh pr checks` exits non-zero when any check is failing or pending, so read the
JSON rather than the exit code.

Mark a draft ready only immediately before its merge: `gh pr ready <n>`.

## Merge methods the repo allows

```bash
gh api repos/OWNER/REPO \
  -q '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'
```

## Merge

```bash
gh api --method PUT repos/OWNER/REPO/pulls/<n>/merge-async \
  -f sha=<checked head SHA> -f merge_method=squash -f merge_action=default
# add -F bypass_rules=true only when the scope turned bypass on
```

Replies: `202` accepted (`details.uuid` to poll), `200` already merged or
already queued, `400` not mergeable (closed, draft), `409` a request is already
pending (its `uuid` is in the reply), `422` validation failed.

`merge_method`, `commit_title` and `commit_message` apply to direct merges only.

## Poll the request

```bash
for i in $(seq 30); do
  s=$(gh api repos/OWNER/REPO/pulls/<n>/merge-async/<uuid> -q .status)
  [ "$s" != pending ] && break; sleep 4
done
gh api repos/OWNER/REPO/pulls/<n>/merge-async/<uuid>
```

`merged` carries the merge commit, `failed` a message, `enqueued` means it sits
in the merge queue. Results are kept 24 hours; after that the `uuid` is a 404.

## What blocks it

```bash
gh api repos/OWNER/REPO/rules/branches/<base>          # rulesets in force
gh api repos/OWNER/REPO/rulesets/<id> -q .bypass_actors
gh api repos/OWNER/REPO/branches/<base>/protection     # classic; 404 = none
```

Classic-protection fallback with bypass on, non-stacked PRs only:
`gh pr merge <n> --squash --admin --match-head-commit <checked head SHA>`.

## Stacks

```bash
gh stack view                  # layers of the current stack
gh stack rebase && gh stack push
```

## Bot PRs

```bash
# Renovate: tick the rebase/retry checkbox in the body
gh pr view <n> --json body -q .body \
  | sed 's/- \[ \] <!-- rebase-check -->/- [x] <!-- rebase-check -->/' \
  | gh pr edit <n> --body-file -

# Dependabot
gh pr comment <n> --body "@dependabot rebase"
```
