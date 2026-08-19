---
name: create-pr
description: Create or update a GitHub PR using a standard PR template — fills in What & Why, Author checklist, and Test Plan. Also posts or updates the post-deployment comment on the linked issue, if any.
---
# Create PR

Create or update a GitHub PR using the standard template, or post/update the post-deployment comment on the linked issue.

See [PR-TEMPLATE.md](references/PR-TEMPLATE.md) for the blank template.

## Usage

- `/quality:create-pr` — create or update a PR for the current branch
- `/quality:create-pr post-deployment` — post or update the post-deployment comment on the linked issue

$ARGUMENTS

## Instructions

### Create or update a PR

#### 1. Detect existing PR

```
gh pr view --json number,url,title,body,headRefName
```

If no PR exists, proceed to **create**. If one exists, proceed to **update**.

#### 2. Gather context

Derive the default base branch first:

```bash
BASE=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
```

If the branch has no commits ahead of base, stop and tell the user: "No commits found ahead of `$BASE` — nothing to PR."

```bash
git rev-parse --abbrev-ref HEAD          # branch name
git log $BASE..HEAD --oneline            # commits since base
git diff $BASE...HEAD --stat             # changed files
```

#### 3. Infer linked issue

Look for a tracker-style key in the branch name (e.g. `[A-Z]+-\d+`, as in `feat/PROJ-123-add-auth` → `PROJ-123`).

If no issue is found, ask the user:
> "No issue key found in the branch name. Does this PR have a linked issue? If yes, provide the key. If not, continue without one."

- **User provides a key** — validate it matches `[A-Z]+-\d+`, then use it and continue.
- **User confirms no issue** — continue without an issue link.

#### 4. Generate PR title

Follow Conventional Commits (`type(scope): description`). Infer from branch name and commit messages.

#### 5. Cross-check with the linked issue

If an issue tracker MCP is available (e.g. Atlassian) and an issue is linked, fetch it and verify that the commits and diff align with what the issue intends. If there is a mismatch (e.g. the PR does more, less, or something different than described), flag it to the user before continuing.

#### 6. Fill the template body

- **What & Why** — list all relevant changes, inferred from commits, diff, and (if available) the linked issue summary; no length limit
- **Issue link** — if an issue was found:
  - `Closes: PROJ-XXX` when the PR fully resolves the issue
  - `Relates to: PROJ-XXX` for partial work or follow-ups
  - Omit if no issue is linked
- **Author Checklist** — **Do not add items that CI/workflows already check** (e.g. formatting, tests passing, linting). The checklist is only for manual steps not covered by automation. Tick `[x]` any item already completed in the current session; leave the rest as `[ ]`.
- **Test Plan — Before Deployment (Author)** — tick `[x]` any steps Claude already verified in the current session (e.g. ran `claude plugin validate .` and it passed → tick it). Leave unverified steps as `[ ]`. Do not leave raw `<!-- ... -->` placeholder text in mandatory sections.
- **Test Plan — Before Deployment (Reviewer)** — always leave as `[ ]`; reviewer completes these.
- **After Deployment section** — include **only if no issue is linked**; otherwise omit (issue comment is SSOT)

#### 7. Create or update

```bash
PR_TITLE="{title}"

# New PR
gh pr create --title "$PR_TITLE" --body "$(cat <<'EOF'
{body}
EOF
)" --assignee @me

# Existing PR
gh pr edit --title "$PR_TITLE" --body "$(cat <<'EOF'
{body}
EOF
)" --assignee @me
```

#### 8. Print the PR URL

---

### Post-Deployment issue comment

Run after the PR is merged and deployment is complete. Requires an issue-tracker MCP (e.g. Atlassian) to be configured — skip this section if none is available.

#### 1. Detect linked issue and PR URL

Look for a tracker-style key (e.g. `[A-Z]+-\d+`) in the branch name. If none found, ask the user: `Which issue should I update? (e.g. PROJ-123)`.

Fetch the PR URL:
```bash
gh pr view --json url --jq '.url'
```

Get today's date from the `currentDate` context variable.

#### 2. Check for existing comment

Fetch the issue and scan comments for one starting with `## Post-Deployment Verification`.

#### 3. First run — add comment

Add a comment with the template, substituting `{pr_url}` and `{today}`:

```
## Post-Deployment Verification
PR: {pr_url}

- [ ] <!-- Smoke test / monitoring check -->
- [ ] <!-- Follow-up or rollback check -->

*Last updated: {today}*
```

#### 4. Subsequent runs — update in-place

Ask the user which items to tick or add, then update the existing comment via the issue-tracker MCP.
