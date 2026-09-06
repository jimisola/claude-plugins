# Traps — every one of these cost a cycle during the 2026-09 rollout

Grouped by where they bite. Each entry says what happens, why, and what to do instead.

## Required checks

- **A required check that never runs blocks the branch forever.** Path-filtered workflows,
  `renovate/stability-days` (bot PRs only), a job that only fires on some PRs — never
  required. A context GitHub has never seen has the same effect: observe a new context on a
  real PR head before requiring it.
- **The ruleset listing lies; the in-force endpoint does not.** A ruleset with
  `conditions.ref_name.include: []` is "active" and matches nothing. Only
  `GET /repos/{o}/{r}/rules/branches/<default>` shows what is enforced.
- **Compare as a set, not a count.** Declared vs enforced `(context, integration_id)`
  pairs, resolved through safe-settings' first-glob-match-wins order. A misnamed context
  is invisible to a count and to a glance.
- **A matrix job never has a stable context.** GitHub appends the matrix values even for a
  single entry (`Tests (3.13)`), so a version-free `name:` fixes nothing. Require a
  non-matrix aggregator:
  ```yaml
  tests:
    name: Tests
    needs: test
    if: always()                      # load-bearing, see next item
    steps:
      - if: needs.test.result != 'success'
        run: exit 1
  ```
- **A skipped required check counts as satisfied — in both directions.** Without
  `if: always()` a failed leg *skips* the aggregator and the branch blocks; a downstream
  job that skips when tests fail (`needs: test`) *passes* the gate by not running. For
  every required context ask what it reports when its job does not run, and require the
  job that owns the guarantee.
- **Job names are byte-exact.** Em dashes, a literal `$/`, `<caller> / <called>` for
  reusable workflows. Renaming a required job is a ruleset change in the same PR.
- **Policy checks must pass on a bot PR before they are required.** A branch-naming regex
  without `renovate` blocks every Renovate PR; a PR-title check with a fixed scope list
  rejects `chore(github-tags): …` (`{{datasource}}` resolves to the datasource, not the
  manager). Test on a real `renovate/…` branch first.
- **`pull_request` runs the workflow from the merge commit**, so a regex fix in an open PR
  does not apply to PRs opened before it merges. Require after merge.
- **CodeQL default-setup contexts have no PR behind them.** Disabling a language in the
  repo settings leaves a required `Analyze (<lang>)` that never reports again. Treat a
  language change as a ruleset change; check `code-scanning/default-setup` in audits.
- **Double reports**: a workflow with an unfiltered `pull_request` and a path-filtered
  `push` reports every job twice on PRs touching the filtered paths. Add
  `branches: [main]` to `push`.

## Renovate config

- **`branchPrefix: "renovate"` without the slash** yields `renovatejunit-5.x` — Renovate
  concatenates. Migrating existing branches needs `branchPrefixOld` for one cycle, and
  only rewrites a branch whose content changes; the rest orphan and are closed by hand.
- **`groupName: "{{groupId}} packages"`** — `groupId` is not a template field; it renders
  empty, the group becomes literally "packages", every update lands in one PR, and being
  last it overrides every named group above it. Group only what releases in lock-step.
- **Automerging majors through a manager rule.** `matchManagers: ["github-actions"],
  automerge: true` placed after the major rule automerges `v4→v5` action bumps. Keep
  manager rules to commit metadata.
- **`pip` is not a manager** — `pip_requirements`. Config validation catches it; a dry-run
  against the wrong config does not.
- **Validate from the branch, with the file staged.** `renovate --platform=github` reads
  the default branch's config and validates the old one; `--platform=local` takes its file
  list from git, so an unstaged new config "succeeds" on onboarding defaults
  (`repoIsOnboarded=false`).
- **Forks**: the hosted app's fork gate (`validateIncludeForks`) reads only the default
  file name at the repo root — `renovate.json` — before normal discovery. A config at
  `.github/renovate.json5` is never consulted for a fork. JSONC works (`parseJson` tries
  JSONC before the deprecated JSON5 fallback); pre-commit's `check-json` rejects it, so
  exclude the file in the same PR.
- **`renovate/stability-days` appears on bot PRs only** and only as a commit status.

## The hosted app (Mend)

- **Silent mode** is a per-repo portal setting: Renovate runs, opens nothing, reports
  nothing. Zero PRs *and* zero issues with a valid config is the signature.
- **A cached "disabled" verdict is never re-evaluated.** A fork scanned before its config
  existed stays disabled until someone clicks *Actions → Run Renovate scan* in the portal.
- **No API** for Community Cloud logs or settings — browser only. The job log is the only
  place a skip reason is visible with `dependencyDashboard: false`.
- **Archived repos** are read-only for Renovate; the portal marks them disabled on the
  next visit. Nothing to configure.
- The App must be installed on **All repositories**; forks are then off by default and
  opt in per repo.

## renovate-approve

- Fires on `pull_request.opened`; approves only when the body carries
  `**Automerge**: Enabled` (minor/patch/pin). Majors and digests get no approval — that is
  the manual tier working, not a fault.
- Re-approves after `dismiss_stale_reviews_on_push` dismisses it on a rebase (observed).
- "No reviews on N PRs" is not "App not installed" — check merged minor/patch PRs that
  carry the marker. `GET /user/installations` is closed to user tokens.

## safe-settings

- **`suborgrepos: ["*"]` skips dot-named repos** — minimatch runs with no options, so
  `dot: false`. A `repos/.github.yml` then POSTs a bare rule with no `enforcement`,
  GitHub 422s, the run exits 1, and the repo is left on classic protection with no checks.
  Name `.github` literally or use `["*", ".github"]`.
- **Quote every label `color:`.** `5319e7` is the float 5319×10⁷ to YAML; `008672` is an
  int; `0e8a16` survives only because an `a` follows the `e`. One unquoted value 422s the
  whole sync.
- **The rulesets plugin deletes undeclared repository rulesets.** List hand-made ones
  before onboarding.
- **Archived or private-on-free-plan repos fail the whole run** — every plugin runs
  regardless of state, one 403 fails everything. Keep them in `restrictedRepos.exclude`
  and rewrite the reason when an admin repo is folded.
- **2.1.19, 2.1.20 and 2.1.21 crash at startup** in Actions mode (`probot.log` is null on
  probot 14 until init; `full-sync.js` dereferences it first). 2.1.18 is the last working
  2.1.x; the predictor for any tag is its probot major. Upstream
  github-community-projects/safe-settings#1073. Node version was not the cause.
- **NOP mode crashes in 2.1.18**, so there is no preview: every config change is tested by
  applying it. Verify afterwards by reading the in-force rules.
- **"No drift" is weak evidence** when the config declares what is already live — an
  aborted run and an idempotent success both show zero drift. Read the run's non-GET
  request list (PATCH/POST/PUT and status codes) to know what was written.
- **`OrganizationAdmin` bypass actors read back with `actor_id: null`.** Upstream #1034
  reports rulesets rewritten on every sync because of it; on 2.1.18 this did **not**
  reproduce (`updated_at` moved only on real changes across three orgs). Check
  `updated_at` against sync times before assuming either way. `RepositoryRole: 5` returns
  a real id and converges by construction.
- **A stale local clone of an admin repo** (deleted upstream) can make you "fix" things
  already gone. Verify the remote exists; read the live API.
- **Public admin repo**: pushing a branch publishes the config immediately — review
  content before the push, not in the PR.

## Process

- **Big-bang PRs** are usually a grouping bug, not a preference. Ask which rule groups.
- **Rate limit**: sweeping ~200 repos × several calls burns the shared 5000/h budget for
  every session on the token. Batch, and use `search/issues` sparingly.
- **Repeat a status only after re-querying it.** PRs merge between messages; a stale
  "open" list reads as not paying attention.
- **Nothing gets published under the user's identity outside their own orgs** — upstream
  issues, comments, PRs — without their explicit yes for that action.
- Safety-relevant firmware: an automerged toolchain minor that builds clean can still
  change runtime behaviour. Raise it; the owner decides.
