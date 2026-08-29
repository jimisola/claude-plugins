# The admin repo and the Actions workflow

safe-settings reads its configuration from one repo in the org, conventionally
`.github-private` (`ADMIN_REPO`). Nothing else in the org declares settings — a repo-local
`.github/settings.yml` in the older `repository-settings/app` format is a *different* tool
with a different schema, and keeping both is how an org ends up with two competing sources.

```
.github-private/
├── .github/workflows/safe-settings.yml
└── safe-settings/
    ├── settings.yml            # org-wide repo defaults AND the label set
    ├── deployment-settings.yml # scope: which repos are excluded
    └── suborgs/all.yml         # rulesets and environments
```

## What each file owns

- **`settings.yml`** — the `repository:` block (merge strategy, squash title/message source,
  branch deletion, `security:` toggles) and `labels:`. Applied to every in-scope repo.
- **`deployment-settings.yml`** — `restrictedRepos.exclude`. Exclude the admin repo, the
  public `.github` repo, and **every archived repo** — archived repos are read-only and a
  failed write there fails the entire run.
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
| `ADMIN_REPO` | `.github-private` |
| `CONFIG_PATH` | `safe-settings` |
| `DEPLOYMENT_CONFIG_FILE` | `${{ github.workspace }}/safe-settings/deployment-settings.yml` |
| `FULL_SYNC_NOP` | `${{ inputs.nop && 'true' || 'false' }}` |

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
