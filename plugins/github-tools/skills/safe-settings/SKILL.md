---
name: safe-settings
description: Onboard a GitHub organization onto github/safe-settings — register the required GitHub App through the manifest flow, install it, wire the Actions workflow, and reconcile the first sync. Use when asked to set up, fix, or debug safe-settings or settings-as-code for an org, when a safe-settings run fails with "appId option is required", or when a settings-as-code declaration is not actually being applied.
---

GitHub does **not** host safe-settings. `github/safe-settings` is an open-source Probot
app; there is no managed installation to switch to. Both ways of running it authenticate
as a GitHub App you register yourself:

- **Actions mode** (`npm run full-sync` on a schedule) — no infrastructure, batch
  reconciliation. Drift stands until the next run; no dry-run on a settings PR.
- **Self-hosted Probot** — webhook-driven, near-real-time, can comment a plan on a
  settings PR. Costs an always-on service and a webhook endpoint.

Registering the App is a prerequisite either way, so it is never wasted work. Default to
Actions mode and only argue for self-hosting once hand-edits in the UI prove to be a real
habit.

## Onboarding an org

1. **Check whether an App exists at all.** `gh api /orgs/<org>/installations --jq
   '.installations[].app_slug'`. A run failing on `[@octokit/auth-app] appId option is
   required` means `vars.SAFE_SETTINGS_APP_ID` is empty — almost always because no App was
   ever registered, not because the variable was mistyped.
2. **Pick the public `.github` repo as the admin repo** (`ADMIN_REPO=.github`), not a
   private one. On a free plan this is not a preference — see the ruleset rule below.
3. **Register the App via the manifest flow**, never by hand through the UI form. The
   manifest is the record of what was granted, it is reviewable in the PR, and it makes a
   second org an exact copy of the first. See
   [references/manifest-flow.md](references/manifest-flow.md) and
   `scripts/app-manifest-flow.py`.
4. **Install it on _All repositories_.** safe-settings enumerates the org; a repo outside
   the installation is silently unmanaged.
5. **Wire the credentials** on the admin repo:
   variable `SAFE_SETTINGS_APP_ID`, secret `SAFE_SETTINGS_PRIVATE_KEY` (the whole `.pem`,
   `BEGIN`/`END` lines included). `gh variable set` / `gh secret set` do both without a
   browser.
6. **Shred the local `.pem` and the manifest-conversion JSON** once the secret is set. The
   conversion response also contains the client secret and the webhook secret. A new key is
   one click away; a leaked one is not recallable.
7. **Reconcile the first sync deliberately.** If the live configuration was ever applied by
   hand, the first successful run is a migration, not a no-op — it can revert something
   deliberate. Diff intended against live before dispatching.

## Rules that are easy to get wrong

- **`DRY_RUN` does not exist.** safe-settings reads `FULL_SYNC_NOP`. Setting `DRY_RUN`
  silently does nothing and the run writes for real. Expose `FULL_SYNC_NOP` as a
  `workflow_dispatch` input instead of hardcoding it.
- **Set `LOG_LEVEL: debug`.** At the default level a run that reverted a setting and one
  that did nothing produce identical logs — a couple of lines, no repos, no settings. The
  only way to know what a sync did is otherwise to diff the API afterwards. With NOP mode
  crashing, debug logging is the only account of a run you get.
- **NOP mode crashes in 2.1.18** (`lib/settings.js` dereferences `y.action.additions`
  before its own `undefined` guard; disabling `CREATE_PR_COMMENT` only moves the crash).
  Do not promise a preview — diff by hand against the live API.
- **Labels live under the Issues permission**, not a permission of their own.
- **Labels are declarative and destructive.** A label present on a repo but absent from
  `settings.yml` is *deleted* on the next sync unless it matches an `exclude`. Never prune
  the label list to tidy the file.
- **Added permissions need an approval click on the installation; removed ones apply
  immediately.** Widening the config is the change that stalls, so grant a slightly wider
  set up front rather than one permission per plugin.
- **Archived repos fail the whole run** — safe-settings cannot write to them, and it runs
  every plugin regardless of a repo's state. The same goes for a private repo on a free
  plan, where the rulesets read 403s before anything is written. Keep both kinds in
  `restrictedRepos.exclude`, and when an admin repo is folded and archived, rewrite its
  exclusion's reason rather than dropping the entry.
- **Two separate ruleset paywalls, and they bite in different places.** *Org-level*
  rulesets require GitHub Team, so on a free org declare rulesets at **suborg** scope to
  get per-repo rulesets; a top-level `rulesets:` block in the org `settings.yml` fails.
  *Repository* rulesets require the repo to be **public** (or GitHub Pro), so a
  ruleset targeting a private repo answers `403 Upgrade to GitHub Pro or make this
  repository public`. That second one is why the admin repo should be the public
  `.github` and not a private repo: otherwise the repo declaring the org's protection
  is the one repo that cannot be protected by it. Nothing in the config is secret —
  rulesets, labels and repo settings are already world-readable through the API on
  public repos.
- **One plugin error fails the whole run**, not just the offending repo. A single
  unmanageable repo — archived, private-with-a-ruleset — turns the entire sync red while
  everything else has already been written. A red run does not mean nothing applied.
- **Required status checks pin an `integration_id`** (GitHub Actions is `15368`), and a
  context GitHub has never seen blocks every PR. A new check must have run once on a real
  PR before it is required.
- **Reusable-workflow checks report as `<caller job> / <called job>`.** Renaming either job
  silently renames the context and the requirement stops matching anything.
- Repo settings only. **Org security settings, secret scanning and CodeQL are out of
  scope** for safe-settings and stay manual or API-applied.
- **`suborgrepos: ["*"]` does not match `.github`.** Patterns go through minimatch with no
  options, so `dot` is false and every dot-named repo is silently skipped. A per-repo
  `repos/.github.yml` then has no suborg ruleset to merge into, POSTs a bare rule without
  `enforcement`, GitHub answers 422, the run exits 1 — and the repo is left on whatever
  classic protection it had, with no required checks. Name dot-repos literally or list
  `["*", ".github"]`. Dot-named per-repo files *are* read.
- **Quote every label `color:`.** YAML reads `5319e7` as the float 5319×10⁷ and `008672`
  as an integer; the label PATCH 422s and the whole sync fails. Which values are at risk
  depends on their digits (`0e8a16` survives only because an `a` follows the `e`), so
  quote all of them rather than the ones that look dangerous.
- **A `repos/<name>.yml` override cannot change `required_status_checks`.** Nested arrays
  concatenate (the deepmerge options are never passed), so the override appends a second
  rule and the PUT 422s, taking the ruleset with it. A repo that needs its own list gets a
  whole suborg file. Two suborg files claiming one repo fail with "Multiple suborg
  configs".
- **The rulesets plugin deletes any repository ruleset that is not declared.** List a
  repo's hand-made rulesets before onboarding it, and either declare them or say in the
  PR that the deletion is intended — a ruleset vanishing after a sync is alarming when
  found rather than approved.
- **A ruleset can be active and match nothing.** `conditions.ref_name.include: []` is
  accepted and enforces nothing. The ruleset listing does not tell you; only
  `GET /repos/{o}/{r}/rules/branches/<default>` shows what is in force.
- **Pin `ref: 2.1.18`.** 2.1.19, 2.1.20 and 2.1.21 all crash at startup in Actions mode
  (probot 14 leaves `probot.log` null until init; `full-sync.js` dereferences it first —
  github-community-projects/safe-settings#1073). The predictor for any future tag is its
  probot major, not the version number. Node was not the cause. The pin is deliberately
  not Renovate-annotated: there is no fixed release to move to, so an annotation would
  only propose broken ones. The project moved to `github-community-projects/`; the old
  `github/safe-settings` path redirects.
- **`OrganizationAdmin` bypass actors read back with `actor_id: null`.** Upstream #1034
  reports rulesets rewritten on every sync because of it; on 2.1.18 it did not reproduce
  across three orgs (`updated_at` moved only on real changes). Check `updated_at` against
  sync times before believing either. `RepositoryRole: 5` returns a real id and converges
  by construction.
- **Pushing to a public admin repo publishes the config.** Review content for anything
  that must not be world-readable — including a comment describing a repo as unprotected
  — *before* the push, not in the PR.

## Verifying a sync

A green run and a config that matches the live state are two different claims; make both
separately.

- **Read what was written.** With `LOG_LEVEL: debug` the job log lists every request.
  Grep the non-GET ones (`PATCH`, `POST`, `PUT`) with their status codes: that is the
  complete account of what the sync changed. "No drift afterwards" is weak evidence when
  the config declares what was already live — an aborted run and an idempotent success
  look identical from the outside.
- **Compare declared vs enforced as a set**, per repo, of `(context, integration_id)`
  pairs plus the approval count, read from `/rules/branches/<default>`. A count or a
  glance cannot catch a substituted or misnamed context. A parameter that has never
  round-tripped through a safe-settings *write* (a newer one such as
  `require_extra_approval_for_unattributed_changes`) is only proven when a real ruleset
  change goes through — check it field by field then.
- **A red run does not mean nothing applied**, and a green run does not mean the ruleset
  is right. Run the set diff after every sync that touched rulesets.

## Rulesets and bots

A `bypass_actors` entry for a bot is almost always a mistake worth arguing about, because
a ruleset bypass is not granular: `bypass_mode: pull_request` exempts that actor's PRs
from **every** rule, required status checks included, not just the review requirement.
Combined with a Renovate config that auto-merges, it means dependency bumps merge without
CI ever having been green — and the failure is silent, because the PRs look normal and
merged.

- Satisfy a review requirement with the **renovate-approve** App (it only approves PRs
  authored by Renovate), not with a bypass.
- Renovate's `platformAutomerge: true` hands the merge to GitHub, which waits only for the
  checks the ruleset marks **required**. `false` makes Renovate merge it, waiting for the
  branch to be green **outright** — but only on the hosted app's next visit, so green PRs
  sit for hours. The `renovate-automerge` skill is the procedure for making every PR check
  required and then flipping to `true`; do not flip before the required list is complete.
- renovate-approve reacts to `pull_request` events, so it does not retroactively approve
  PRs that were already open when it was installed. Tick the `rebase-check` box in a
  PR body to make Renovate rebase, which fires the event.

Reference layout of the admin repo, the workflow, and what each config file owns:
[references/repo-layout.md](references/repo-layout.md).
