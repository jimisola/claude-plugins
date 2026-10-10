---
type: llm
weight: 3
---

PASS if all three hold:
1. Claude says the ruleset matches no branch because `conditions.ref_name.include` is empty, so GitHub auto-merge had no required checks to wait for.
2. The fix is to the ruleset declaration in safe-settings (include `~DEFAULT_BRANCH` or `refs/heads/main`), followed by a sync.
3. It verifies afterwards against GET rules/branches/main, comparing the (context, integration_id) pairs with the declared ones rather than trusting the green sync.

Offering to set `platformAutomerge: false` as a temporary stop-gap, with the user's agreement, while the ruleset is fixed is fine.
FAIL if it blames Renovate's config or the CI workflow, makes turning platformAutomerge off the fix instead of correcting the ruleset, or verifies only from the ruleset listing or the sync result.
