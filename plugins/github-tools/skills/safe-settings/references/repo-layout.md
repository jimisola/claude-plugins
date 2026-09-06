# The admin repo and the Actions workflow

safe-settings reads its configuration from one repo in the org (`ADMIN_REPO`). Use the
**public `.github` repo**. The obvious-looking alternative, a private `.github-private`,
costs you the ability to protect the repo that defines the org's protection: repository
rulesets need a public repo (or GitHub Pro), so a ruleset targeting a private admin repo
answers `403` and fails the whole sync. Publishing the config gives nothing away —
rulesets, labels and repo settings are already world-readable through the API on public
repos — and Actions minutes are unmetered there. Nothing else in the org declares settings — a repo-local
`.github/settings.yml` in the older `repository-settings/app` format is a *different* tool
with a different schema, and keeping both is how an org ends up with two competing sources.

```
.github/
├── .github/workflows/safe-settings.yml
└── safe-settings/
    ├── settings.yml            # org-wide repo defaults AND the label set
    ├── deployment-settings.yml # scope: which repos are excluded
    └── suborgs/
        ├── product.yml         # the repos with real CI: rulesets, environments
        └── meta.yml            # the repos without it: no required status checks
```

Split the suborgs by *what CI a repo actually has*, not by what the repos are. A required
status check that a repo never produces blocks every PR on it forever, so one ruleset
covering both a product repo and a meta repo is not possible.

## What each file owns

- **`settings.yml`** — the `repository:` block (merge strategy, squash title/message source,
  branch deletion, `security:` toggles) and `labels:`. Applied to every in-scope repo.
- **`deployment-settings.yml`** — `restrictedRepos.exclude`. Exclude **every archived
  repo**: they are read-only, and one failed write there fails the entire run, not just
  that repo. An empty exclude list is load-bearing and worth a comment — safe-settings
  restores its own defaults (`admin`, `.github`, `safe-settings`) when the file is
  absent, so deleting the file silently unmanages the admin repo.
- **`suborgs/all.yml`** — `rulesets:` and `environments:`. Rulesets belong here, not in
  `settings.yml`: a top-level `rulesets:` block is created as an *organization* ruleset,
  which requires GitHub Team. At suborg scope they are created per repo, which is free.

## The workflow

Checks out the admin repo and `github/safe-settings` at a pinned tag, `npm ci`, then
`npm run full-sync` with:

| Env | Value |
|---|---|
| `GH_ORG` | the org login |
| `APP_ID` | `${{ vars.SAFE_SETTINGS_APP_ID }}` |
| `PRIVATE_KEY` | `${{ secrets.SAFE_SETTINGS_PRIVATE_KEY }}` |
| `ADMIN_REPO` | `.github` |
| `CONFIG_PATH` | `safe-settings` |
| `DEPLOYMENT_CONFIG_FILE` | `${{ github.workspace }}/safe-settings/deployment-settings.yml` |
| `FULL_SYNC_NOP` | `${{ inputs.nop && 'true' || 'false' }}` |
| `LOG_LEVEL` | `debug` — without it a run says nothing about what it changed |

Triggers: push to `main` limited to `safe-settings/**`, a weekly cron for drift correction,
and `workflow_dispatch` with a boolean `nop` input.

`FULL_SYNC_NOP` is the *only* preview knob — there is no `DRY_RUN` variable, and a workflow
setting one is doing nothing while looking careful. In 2.1.18 the NOP path crashes anyway
(`lib/settings.js` dereferences `y.action.additions` before the `undefined` guard below it),
so treat the input as wiring for a future fix, not as a working preview.

## Reading the first sync

If the live configuration was ever applied by hand — the usual case, since something had to
protect `main` before safe-settings worked — the first successful run is a migration. It will
revert anything live that the config does not describe. Before dispatching, diff the intent
against reality:

```bash
gh api /repos/<org>/<repo> --jq '{allow_squash_merge, allow_merge_commit, allow_auto_merge, delete_branch_on_merge, squash_merge_commit_title, squash_merge_commit_message}'
gh api /repos/<org>/<repo>/rulesets
gh api /repos/<org>/<repo>/labels --jq '[.[].name] | sort'
gh api /repos/<org>/<repo>/environments --jq '[.environments[].name]'
```

Labels are the destructive one: any label live but absent from `settings.yml` is deleted, and
issue forms, `actions/labeler` and Renovate all break on a label that no longer exists
(`actions/labeler` errors outright; the other two drop it silently).

## Moving the config out of a private admin repo

The fold copies files; history does not follow. Take a `git bundle` of the old repo first
and prove it restores (`git clone <bundle>`), because once the repo is gone that bundle is
the only copy of the reasoning in its commits.

Order matters, and each step is verified before the next:

1. Bring every repo the old config could not protect (private on a free plan) to a
   state where it can be — make it public, then give it a real ruleset.
2. Move `safe-settings/`, the workflow (`ADMIN_REPO` changed) and the README sections into
   the public `.github`. Keep the old repo in `restrictedRepos.exclude`, reason rewritten
   to "archived". Set `SAFE_SETTINGS_APP_ID` (a variable) and a **new** private key on the
   new home — a GitHub App holds several keys at once, so nothing stops syncing in between;
   delete the old key afterwards.
3. First sync from the new home must be green; then the set diff on every repo.
4. Archive or delete the old repo **before its next scheduled run**: both repos now carry
   the same daily cron and the workflow's concurrency group is per repository, so two syncs
   would run against the org at once. Deleting stops Actions immediately; archiving too.
5. Only then merge the change that empties the exclude list. Merged earlier, the next sync
   tries to manage the still-existing private repo and 403s. Keep the exclude *file* even
   when the list is empty — `DEPLOYMENT_CONFIG_FILE` points at it, and an absent file
   restores safe-settings' defaults.

A public admin repo has one property the private one did not: GitHub disables a
scheduled workflow after 60 days without commits, silently. Renovate's own action-pin PRs
normally keep the repo active; the check that matters is "did the daily sync run", where
zero runs is the bad answer.
