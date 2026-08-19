---
name: full-pr-review
description: Run parallel quality checks on a PR, deduplicate findings, present a consolidated summary, then ask the user how to proceed. Use when the user asks for a full, thorough, or complete review of a pull request.
---
# Full PR Review

Run parallel quality checks on a PR, deduplicate findings, present a consolidated summary, then ask the user how to proceed.

## Arguments

- No arguments: detect PR from current branch, run all checks
- PR URL (e.g., `https://github.com/owner/repo/pull/123`): review that PR
- Check IDs (e.g., `review security-review`): run only those checks
- `skip:ID` (e.g., `skip:security-review skip:cruft`): run all checks except those

Arguments can be combined: `https://github.com/owner/repo/pull/42 skip:cruft`

$ARGUMENTS

## Checks

| ID | Skill/Command |
|---|---|
| `review` | `/review` (built-in) |
| `code-review` | `/code-review` (built-in) — bugs, cleanups, code smells |
| `security-review` | `/security-review` (built-in) — security issues in pending changes |
| `cruft` | inlined below — dead code, unused files, stale deps (no built-in equivalent) |

`code-review` and `security-review` are Claude Code's built-in commands — prefer them over
custom skills since they're maintained upstream and already scoped to diffs. `cruft` has no
built-in equivalent (repo-wide dead-code/stale-dependency detection vs. diff-scoped), so its
check criteria are inlined directly below rather than delegated to a separate skill file —
there is no separate `find-cruft` skill — this is the only place the check lives.

## Instructions

### 1. Detect PR

Check if `$ARGUMENTS` contains a GitHub PR URL (matching `https://github.com/.../pull/\d+`).

**If a URL is provided:** extract owner, repo, and PR number from the URL. Use `--repo {owner}/{repo}` on all `gh` commands.

**If no URL:** detect from the current branch:
```
gh pr view --json number,url,headRefName,headRefOid --jq '{number, url, headRefName, headRefOid}'
```
If no PR exists for the current branch, stop and tell the user.

Then fetch full PR metadata:
```
gh pr view {number} [--repo {owner}/{repo}] --json number,url,title,body,headRefName,headRefOid,baseRefName,files,commits,additions,deletions,state,author
```

Detect whether this is the author's own PR:
```
gh api user --jq '.login'
```

Compare the result with `pr.author.login`. Set a flag `own_pr = true` if they match, `false` otherwise.

> **Own PR:** GitHub does not allow submitting a formal review (inline comment threads via the reviews API) on your own PR. Available posting options are limited to summary comments.

### 2. Get the PR diff

Fetch the full PR diff for the checks to review:

```
gh pr diff {number} [--repo {owner}/{repo}]
```

### 3. Parse arguments

Remove the PR URL (if any) from `$ARGUMENTS`. What remains are check selectors:

- If no check selectors remain, run all checks in the table above.
- If `skip:ID` tokens are present, run all checks EXCEPT those IDs.
- Otherwise, treat each word as a check ID and run only those.

### 4. Fetch existing PR comments

Before running checks, fetch all existing review comments on the PR:

```
gh api repos/{owner}/{repo}/pulls/{number}/comments
gh api repos/{owner}/{repo}/pulls/{number}/reviews
gh api repos/{owner}/{repo}/issues/{number}/comments
```

Extract any actionable findings from these comments (e.g., from Copilot, human reviewers, or previous quality gate runs). These will be included in the deduplication step with their original author as provenance (e.g., `Found by: Copilot, code-review`).

### 5. Run checks in parallel

Launch one **background subagent** per selected check. All agents run in parallel.

Each agent receives:
- The PR diff
- The check-specific instructions:
  - `review` → run `/review`
  - `code-review` → run `/code-review`
  - `security-review` → run `/security-review`
  - `cruft` → use the [Cruft Check Criteria](#cruft-check-criteria) below
- Instructions to **scope the review to the PR diff only** (not the entire repo)
- Instructions to produce a markdown report with findings including **file path and line number** for each finding

**Important:** Each agent must return its findings as structured markdown text. The agent should NOT post comments itself.

#### Cruft Check Criteria

Find pieces of cruft in the PR diff — leftover artifacts that are unneeded, unused, or obsolete:

- **Dead code** — unused classes/methods/functions/fields, unreachable branches, commented-out code left behind after refactors, unused framework beans/components
- **Orphaned files** — source files never imported or used, test files for removed features, config for removed tools, empty/near-empty files
- **Stale dependencies** — dependencies added but never imported, dev/test dependencies unused by any test, duplicate dependencies serving the same purpose
- **Leftover files & build artifacts** — generated files checked in, old migration/seed data, unused resources, build reports/test output committed
- **Obsolete configuration** — properties never read, config for removed features, outdated build tasks, stale `.gitignore` entries
- **Remnants of removed features** — entities/repositories for unused tables, endpoints/DTOs/services for deleted features, stale comments/docs/names referencing removed features

Report each finding with category, location (file + line/path), description, and recommendation
(delete/consolidate/other). Do not report things that look unused but are used dynamically
(component scanning, reflection, framework conventions). Do NOT fix — only report.

### 6. Collect and deduplicate

Wait for all agents to complete. Then **merge all findings — from both agents AND existing PR comments (step 4) — into a single deduplicated report**:

1. **Group by location/topic** — if multiple sources flag the same file, class, or pattern, merge them into one finding.
2. **Track provenance** — for each unique finding, record ALL sources that flagged it. Example: `Found by: Copilot, review, code-review`.
3. **Use the highest severity** — if sources disagree on severity, use the most critical.
4. **Preserve unique findings** — if only one source found something, include it as-is.
5. **Order by severity** — Critical → High → Medium → Low → Info.
6. **Map each finding to a file and line** — every finding must be tied to a specific file path and line number in the PR diff.

### 7. Present summary

Present the consolidated findings to the user:

| # | Prio | Input? | Location | Finding | Fix |
|---|------|--------|----------|---------|-----|

Where:
- **#** — sequential ID
- **Prio** — severity: Critical / High / Medium / Low / Info
- **Input?** — `yes` if you need the user's input/decision to proceed, `no` if the fix is straightforward
- **Location** — `filename:line`
- **Finding** — concise description of the issue
- **Fix** — proposed fix

Order by severity (Critical → Info).

### 8. Ask how to proceed

After presenting the summary, ask the user:

**"How would you like to proceed?"**

**If `own_pr = true`** (GitHub blocks formal reviews on your own PR):

1. **Post as summary comment** — post the consolidated summary as a single PR comment
2. **Fix** — fix all findings without posting comments
3. **Done** — no further action

**If `own_pr = false`:**

1. **Post as summary comment** — post the consolidated summary as a single PR review comment
2. **Post as inline comments** — post each finding as an individual inline review comment (resolvable threads)
3. **Post and fix** — post inline comments, then fix CI and address all comments
4. **Done** — do nothing further, the summary was enough

Wait for the user's choice before proceeding.

### 9a. Post as summary comment

If the user chose option 1:

```
gh pr review {number} [--repo {owner}/{repo}] --comment --body "$(cat <<'EOF'
{consolidated summary}
EOF
)"
```

### 9b. Post as inline comments

If the user chose option 2 or 3:

Post findings as a **GitHub pull request review** using the REST API. This makes every finding a **resolvable conversation thread**.

Use `gh api repos/{owner}/{repo}/pulls/{number}/reviews -X POST --input payload.json` with this structure:

```json
{
  "commit_id": "{headRefOid}",
  "body": "## Full PR Review — Consolidated Findings\n\n{summary}\n\n---\n*Automated — `/quality:full-pr-review`*",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/main/java/.../SomeFile.java",
      "line": 42,
      "side": "RIGHT",
      "body": "**[{severity}]** {finding title}\n\n{description}\n\n**Found by**: `source1`, `source2`"
    }
  ]
}
```

**Comment body requirements:**
- Each comment body must be **3-6 sentences minimum** — never a one-liner.
- **What was wrong** — describe the problem or gap concretely
- **What changed and where** — describe the fix, with cross-references
- **Why it matters** — explain the impact or risk if left unfixed

**Key rules:**
- Each finding = one inline comment on the relevant file/line → creates a resolvable thread
- `"event": "COMMENT"` — don't approve or request changes, just comment
- `"side": "RIGHT"` — comment on the new version of the file
- Write the JSON payload to a temp file and pass via `--input`

After posting inline comments, resolve any already-fixed findings using the GraphQL API.

### 10. Run fix workflow (only if user chose fix/post-and-fix)

First, run `/quality:make-ci-green-again` to fix any failing CI checks — this ensures `act-on-pr` works on a green baseline and can resolve comments already fixed by CI.

Then, run `/quality:act-on-pr` to:
- Analyze and categorize all review comments
- Fix findings and resolve the corresponding threads
- Address any other reviewer comments

### 11. Tick author checklist (after any fixing)

After findings have been addressed (whenever a fix option was chosen), check the PR body for:

```
- [ ] Ran `/quality:full-pr-review` and addressed findings
```

If the item exists and is unchecked, update the PR body to tick it:

```bash
gh pr edit {number} [--repo {owner}/{repo}] --body "{updated_body}"
```

Replace only `- [ ] Ran \`/quality:full-pr-review\` and addressed findings` → `- [x] Ran \`/quality:full-pr-review\` and addressed findings`. Leave all other content unchanged.

---

## Related skills

| Skill | Purpose |
|-------|---------|
| `/quality:create-pr` | Create or update a PR using the standard template |
| `/quality:act-on-pr` | Fetch and apply PR review comments |
| `/quality:make-ci-green-again` | Watch and fix failing CI checks |
| `/quality:preflight` | Mandatory pre-commit checks (plugin repos: validate + smoke-test; other projects: formatter + tests + build) |
| `/quality:grill-me` | Stress-test a plan or design via relentless questioning |
| `/quality:find-smells` | Find code smells repo-wide (surface-level to architectural) and plan a fix |
