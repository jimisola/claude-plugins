# PR Template

## What & Why
<!-- What changed and why. List all relevant changes. -->

<!-- Issue link — pick one:
  Closes: PROJ-XXX      (use when this PR fully resolves the issue)
  Relates to: PROJ-XXX  (use for partial work or follow-ups)
-->

## Author Checklist

- [ ] Ran `/quality:full-pr-review` and addressed findings

## Test Plan

### Before Deployment

**Author**
- [ ] <!-- e.g. ran locally, invoked the skill on a real branch, verified output -->

**Reviewer**
- [ ] <!-- e.g. checked template sections are filled, test plan is non-trivial -->

### After Deployment
<!-- When an issue is linked: omit this section — post-deployment verification
     lives as a comment on the issue instead (see Issue Comment Template below).
     When no issue is linked: keep this section in the PR body. -->
- [ ] <!-- e.g. smoke tested the deployed change, verified monitoring -->

---

# Issue Comment Template — Post-Deployment Verification

> Post this as a comment on the linked issue after deployment.
> Update it in-place as items are verified.

```
## Post-Deployment Verification
PR: {pr_url}

- [ ] <!-- Smoke test / monitoring check -->
- [ ] <!-- Follow-up or rollback check -->

*Last updated: {today}*
```
