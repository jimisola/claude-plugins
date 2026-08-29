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
2. **Register the App via the manifest flow**, never by hand through the UI form. The
   manifest is the record of what was granted, it is reviewable in the PR, and it makes a
   second org an exact copy of the first. See
   [references/manifest-flow.md](references/manifest-flow.md) and
   `scripts/app-manifest-flow.py`.
3. **Install it on _All repositories_.** safe-settings enumerates the org; a repo outside
   the installation is silently unmanaged.
4. **Wire the credentials** on the admin repo (conventionally `.github-private`):
   variable `SAFE_SETTINGS_APP_ID`, secret `SAFE_SETTINGS_PRIVATE_KEY` (the whole `.pem`,
   `BEGIN`/`END` lines included). `gh variable set` / `gh secret set` do both without a
   browser.
5. **Shred the local `.pem` and the manifest-conversion JSON** once the secret is set. The
   conversion response also contains the client secret and the webhook secret. A new key is
   one click away; a leaked one is not recallable.
6. **Reconcile the first sync deliberately.** If the live configuration was ever applied by
   hand, the first successful run is a migration, not a no-op — it can revert something
   deliberate. Diff intended against live before dispatching.

## Rules that are easy to get wrong

- **`DRY_RUN` does not exist.** safe-settings reads `FULL_SYNC_NOP`. Setting `DRY_RUN`
  silently does nothing and the run writes for real. Expose `FULL_SYNC_NOP` as a
  `workflow_dispatch` input instead of hardcoding it.
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
- **Archived repos fail the whole run** — safe-settings cannot write to them. Exclude them
  in `deployment-settings.yml`, along with the admin repo itself.
- **Org-level rulesets require GitHub Team.** On a free org, declare rulesets at *suborg*
  scope so they are created as per-repo rulesets. A top-level `rulesets:` block in the
  org `settings.yml` fails.
- **Required status checks pin an `integration_id`** (GitHub Actions is `15368`), and a
  context GitHub has never seen blocks every PR. A new check must have run once on a real
  PR before it is required.
- **Reusable-workflow checks report as `<caller job> / <called job>`.** Renaming either job
  silently renames the context and the requirement stops matching anything.
- Repo settings only. **Org security settings, secret scanning and CodeQL are out of
  scope** for safe-settings and stay manual or API-applied.

Reference layout of the admin repo, the workflow, and what each config file owns:
[references/repo-layout.md](references/repo-layout.md).
