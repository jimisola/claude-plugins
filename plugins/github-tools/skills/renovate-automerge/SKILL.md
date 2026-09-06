---
name: renovate-automerge
description: Bring a GitHub repo or org onto the agreed dependency-automation setup — Renovate (never Dependabot) with GitHub auto-merge for minor, patch and pin updates, gated by a ruleset that requires every check that runs on every PR, declared in safe-settings where the org has it. Use this whenever the user mentions Renovate, auto-merge, automerge, dependency bumps sitting unmerged, platformAutomerge, required status checks, rulesets for bot PRs, "Renovate is silent", renovate-approve, Dependabot vs Renovate, or wants a new repo/org set up "like the others" — even if they do not say "Renovate". Also use it to audit an existing repo before trusting its auto-merge.
---

Renovate can merge its own PRs in two ways, and the difference is the whole skill:

- `platformAutomerge: false` — Renovate merges on its **next visit**, after the branch is
  green outright. Safe by construction, but the hosted app visits on its own schedule, so a
  green PR sits open for hours.
- `platformAutomerge: true` — Renovate arms **GitHub auto-merge** at PR creation and GitHub
  merges seconds after the ruleset is satisfied. GitHub waits for the checks the ruleset
  marks **required** — nothing else. With an incomplete required list a PR merges before
  CI has run, and the failure is silent because the PR looks normal and merged.

So the setup is one rule with a precondition: **every check that runs on every PR is a
required check, then `platformAutomerge: true`.** Never the other way round. The evidence
that this matters, including the same PR shape merging 23 s *before* its check and, a day
later, 5 s *after* it: [references/evidence.md](references/evidence.md).

## The target, in one screen

1. **Ruleset on the default branch** — required checks = every unfiltered PR job (CI,
   CodeQL/`Analyze (<lang>)`, DCO, PR-title, lint…), with `integration_id` pinned
   (GitHub Actions 15368, Advanced Security/CodeQL 57789, DCO App 1861);
   `strict_required_status_checks_policy: false`; `pull_request` rule with 1 approval,
   dismiss-stale, thread resolution, squash only; admin bypass only — **never a bypass for
   Renovate**, a bypass skips the checks too.
2. **Approval** comes from the `renovate-approve` App (approves Renovate's own PRs on
   open, when the body carries `**Automerge**: Enabled`). Majors never get that marker,
   so they park at `REVIEW_REQUIRED` for a human.
3. **Renovate config**: `automergeType: "pr"`, `platformAutomerge: true`, `automerge`
   on minor/patch/pin only — majors and digests manual, GitHub Actions included;
   `minimumReleaseAge` 3 d minor/patch, 7 d major, none for pin; `dependencyDashboard:
   false`; `branchPrefix` ending in `/` if set at all.
4. **Declared in safe-settings** where the org has it (see the `safe-settings` skill to
   install it); user-account repos are API-managed; private repos on the free plan cannot
   have rulesets at all, so they keep Renovate's own merge — `true` falls back harmlessly.
5. **Repo flags**: `allow_auto_merge`, squash only, `delete_branch_on_merge`; every label
   the config references exists; Dependabot *alerts* on (Renovate's security PRs read
   that feed), Dependabot security updates off, no `dependabot.yml`.

Full checklist with YAML: [references/target-setup.md](references/target-setup.md).

## Workflow

Work one repo at a time and verify each step against the live API, not the declaration.

1. **Audit first.** `scripts/audit-repo.sh OWNER/REPO` prints the rules actually in force,
   the PR-triggered jobs, the check-runs on the newest PR head with their app ids, the
   repo flags, and the Renovate-config red flags. Read it before proposing anything.
2. **Make the required list complete** — derive it from the workflows *and* confirm each
   context on a real PR head. Exclude path-filtered jobs (a required check that never
   runs blocks every PR forever) and `renovate/stability-days` (only appears on bot PRs).
   Prove every policy check — branch-naming, PR-title — passes on a Renovate branch
   (`renovate/…`, title `chore(<datasource>): …`) before requiring it.
3. **Declare it** in safe-settings (or apply by API for user repos), sync, then read
   `GET /repos/{o}/{r}/rules/branches/<default>` and compare the enforced
   `(context, integration_id)` set against the declared one as a **set diff** — a count
   cannot catch a misnamed context, and a green sync is not evidence of a correct ruleset.
4. **Only then** flip `platformAutomerge: true` in the preset.
5. **Prove it live.** On the first minor/patch PR record: open → approval delay → last
   required check → merge time. The merge must follow the last check, never precede it.
6. Every change is a PR that states the precondition in its own words. Do not cite other
   orgs' PRs as the pattern source.

## The standing obligation

After the flip, a **new unfiltered CI job is ungated until it is added to the required
list** — Renovate no longer waits for "branch green". A workflow and its required contexts
land in the same PR, always. Renames, matrix changes and CodeQL language toggles are
ruleset changes too. Re-run the in-force set diff whenever something about CI moves.

## Rules that are easy to get wrong

The rollout that produced this skill hit ~40 of these across five orgs; each one cost a
cycle. The full list with the incident behind each is
[references/traps.md](references/traps.md). The ones that bite first:

- A ruleset can list fine and match **nothing** (`conditions.ref_name.include: []`).
  The in-force endpoint is the only proof.
- A **matrix job can never be a stable required check** — GitHub appends the matrix values
  even for one entry. Require a non-matrix aggregator (`needs`, `if: always()`, fail unless
  the leg succeeded). Without `always()` a failed leg *skips* the aggregator, and a
  skipped required check blocks the branch just like a failure.
- A **skipped required check counts as satisfied** in the other direction: a downstream
  job that skips when tests fail passes the gate by not running. Require the job that
  owns the guarantee.
- Forks: the hosted app's fork gate reads only root `renovate.json` (JSONC is fine),
  never `.github/renovate.json5`. A fork with the config elsewhere stays disabled forever.
- Renovate silent with no error → Mend portal: per-repo **silent mode**, or a cached
  *disabled* verdict that needs "Run Renovate scan". No API exists for Community Cloud.
- `groupName: "{{groupId}} packages"` — not a template field, renders as "packages",
  groups every update into one big-bang PR and overrides the groups above it.
- safe-settings: `suborgrepos: ["*"]` skips dot-named repos (`.github`); quote every label
  `color:` (`5319e7` is a YAML float); 2.1.18 is the last release whose full-sync runs.

## Verifying

```bash
scripts/audit-repo.sh OWNER/REPO                       # everything below, in one report
gh api repos/OWNER/REPO/rules/branches/main            # rules actually in force
gh api repos/OWNER/REPO/commits/<sha>/check-runs --jq '.check_runs[]|"\(.app.id)\t\(.name)"'
gh pr view N --json createdAt,mergedAt,reviews,statusCheckRollup   # the live proof
```
