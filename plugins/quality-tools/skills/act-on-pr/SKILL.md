---
name: act-on-pr
description: Fetch PR review comments, analyze each one, present a summary, let the user choose what to fix, apply fixes, and reply to all comments.
disable-model-invocation: true
---
# Act on PR

Fetch PR review comments, analyze each one, present a summary, let the user choose what to fix, apply fixes, and reply to all comments.

## Instructions

### 1. Find the PR

Determine the current PR from the current branch:

```bash
gh pr view --json number,url,headRefName,headRefOid --jq '{number, url, headRefName, headRefOid}'
```

If no PR exists for the current branch, stop and tell the user.

### 2. Fetch all review comments

Fetch file-level review comments:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '.[] | "---\nID: \(.id)\nFile: \(.path):\(.line // .original_line)\nAuthor: \(.user.login)\nBody: \(.body)\n"'
```

Fetch issue-level comments:

```bash
gh api repos/{owner}/{repo}/issues/{number}/comments --jq '.[] | "---\nAuthor: \(.user.login)\nBody: \(.body)\n"'
```

Fetch review submissions for context:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews
```

Focus on unresolved comments and conversation threads.

### 3. Analyze each comment

For each comment, determine:

- **Is it valid?** Does it identify a real issue in the code?
- **Category:** code fix / docs fix / style-preference / false positive / already handled
- **Severity:** bug (would cause runtime issues) / improvement (better but not broken) / nit (minor style/preference)
- **Suggested fix:** What change would address it?

### 4. Present analysis table

Show the user a summary table:

| # | File | Issue | Valid? | Severity | Suggested Fix |
|---|------|-------|--------|----------|---------------|

Group by: actionable fixes first, then docs, then false positives/nits.

### 5. Ask the user what to fix

Present options:

1. **Fix all** — fix all valid comments
2. **Bugs + improvements only** — skip nits
3. **Let me pick** — user selects specific items by number
4. **Skip fixes** — just reply to comments without code changes

Wait for the user's choice before proceeding.

### 6. Apply fixes

For each comment the user wants fixed:
- Read the relevant file and understand context
- Make the code change
- Verify no new issues are introduced

After all fixes:
- Run the project's formatter (e.g., `./gradlew spotlessApply`)
- Run tests to verify nothing is broken

### 7. Commit and push

Stage all changes and commit with: `fix(review): address PR review feedback`

Push the changes.

### 8. Reply to all comments

Reply to every comment on the PR:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -f body="<reply>"
```

Reply format:
- **Fixed:** "Valid — <brief description of what was changed>. Fixed in <commit_sha>."
- **Rejected/false positive:** "Not applicable — <brief explanation of why>."
- **Already handled:** "Already addressed — <reference to where/when>."

### 9. Resolve fixed threads

For each fixed comment, resolve the conversation thread:

```bash
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) { thread { isResolved } } }'
```

Do NOT resolve threads for rejected or false-positive comments — leave those for the reviewer.

### 10. Summarize

Report:
- How many comments were addressed
- How many threads were resolved vs left open
- Any comments that need the user's input
