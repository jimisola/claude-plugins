---
name: make-ci-green-again
description: Watch CI checks on the current PR, analyze failures, fix them, and re-check until all checks pass. Use when the user asks to fix failing CI or get the build green.
---
# Make CI Green Again

Watch CI checks on the current PR, analyze failures, fix them, and re-check until all checks pass.

## Instructions

1. Determine the current PR number from the current branch using `gh pr view --json number --jq '.number'`. If no PR exists, stop and tell the user.

2. Watch CI checks using `gh pr checks {number} --watch`. Wait for all checks to finish.

3. If all checks pass, report success and stop.

4. If any checks failed:
   a. Analyze the failure logs — use `gh pr checks {number}` to identify which checks failed, then fetch logs for each failed check.
   b. Diagnose the root cause of each failure.
   c. Fix the issues in the code.
   d. Run the project's formatter (e.g., `./gradlew spotlessApply`) and relevant tests locally to verify the fix.
   e. Commit with: `fix(ci): <description of what was fixed>`
   f. Push the changes.

5. After pushing, go back to step 2 — watch checks again. Repeat until all checks pass or you've attempted 3 fix cycles (to avoid infinite loops).

6. If checks still fail after 3 attempts, summarize the remaining failures and ask the user for guidance.
