---
name: git-workflow
description: Personal git workflow conventions - branch naming, Conventional Commits, PR title format. Auto-applies when planning or creating a branch, writing commits, or opening/updating a pull request.
---

# Git Workflow

## Hard Rules - Never Skip

- **Branch name** MUST be `<type>/<kebab-case-description>` before any `git checkout -b` or `git switch -c`. Only lowercase alphanumeric and hyphens after the slash - no uppercase, no underscores, no issue-tracker keys. Invalid: `my-feature`, `feat/PROJ-123-add-auth`, `feature_add_auth`. Valid: `feat/add-auth`, `fix/null-pointer`, `chore/update-deps`.
- **Worktree branches** MUST be renamed immediately on worktree entry, before any commits. Claude Code auto-generates names like `worktree-feat+add-foo` - rename with `git branch -m <auto-name> <type>/<kebab-case-description>` (strip `worktree-` prefix, replace `+` with `/`) so all commits land on the correct branch name from the start.
- **PR body** MUST use `/quality:create-pr`. Never call `gh pr create` with a freeform body or the default Claude Code template - the PR template has mandatory sections that a generic template omits.

---

## Branch Naming

Format: `<type>/<kebab-case-description>` - all lowercase alphanumeric + hyphens, no uppercase, no underscores.

If CI enforces branch naming in your repo, typical rules look like:

**Valid prefixes:** `feat/`, `feature/`, `fix/`, `bugfix/`, `chore/`

**Whitelisted (skip validation):** `main`, `master`, `release/*`, `hotfix/*`, `dependabot/*`, `copilot/*`

Examples: `feat/add-logging-starter`, `fix/null-pointer-in-config`, `chore/update-spring-boot`

### Worktree Branches

Claude Code's `isolation: "worktree"` generates names like `worktree-feat+add-foo`. These fail CI. Rename immediately on worktree entry - before any commits:

```bash
git branch -m worktree-feat+add-foo feat/add-foo
```

Pattern: strip `worktree-` prefix, replace `+` with `/`.

## Commit Conventions

**All commits must follow [Conventional Commits](https://www.conventionalcommits.org/).**

Format: `<type>(<scope>): <description>`

**Allowed types:** `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `perf`, `refactor`, `revert`, `style`, `test`

**Scopes:** freeform (optional) - use module names, infrastructure areas, or whatever fits the project.

**Breaking changes:** use `!` suffix or `BREAKING CHANGE:` footer (e.g. `feat!: change API response format`)

## Pull Request Conventions

**PR titles must follow Conventional Commits format.**

The PR title becomes the squash-merge commit message, so it must be a valid conventional commit.

Examples:
- `feat: add user authentication`
- `fix(ci): resolve workflow permission issues`
- `refactor: simplify error handling logic`

## Workflow Rules

- **Always work on a branch** - never commit directly to `main` or `master`
- **Create PRs for review** before merging
- **Never merge PRs from CLI** - merging is always done manually via the GitHub Web UI
- **Always assign PRs** to the current GitHub user
- **After pushing, invoke `/quality:create-pr`** - this is the only approved way to create or update a PR; it fills the PR template, infers title, issue link, and context from the branch and commits (requires the `quality` plugin). Do not substitute bare `gh pr create` calls.

## Test Plan Hygiene

A checked box (`[x]`) is a claim that the item was verified. Never tick an item speculatively.

**Automated items** (build, tests, lint, CI checks):
- Run the command yourself before ticking
- Only tick `[x]` after seeing a passing result

**Manual items** (e.g. "Manual: post event and verify..."):
- Leave as `[ ]` - only the human can verify these
- Do not tick them even if the code change looks correct

**When creating a PR**, split the test plan into automated and manual sections so it's unambiguous which items Claude is responsible for completing.
