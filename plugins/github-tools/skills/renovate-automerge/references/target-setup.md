# Target setup — the full checklist

Everything here is the state a repo is brought *to*. Verify each item against the live
API; declarations are what you intend, the API is what is true.

## 1. Renovate preset / config

Shared org preset (`<org>/.github/.github/renovate.json5`, which also serves as that
repo's own config), or a per-repo config where the org has no preset:

```json5
{
  extends: ["config:recommended", ":semanticCommits"],
  semanticCommits: "enabled",
  semanticCommitType: "chore",
  semanticCommitScope: "{{datasource}}",   // resolves to the DATASOURCE (github-tags), not the manager
  branchPrefix: "renovate/",               // trailing slash — Renovate concatenates
  rangeStrategy: "pin",
  dependencyDashboard: false,
  prConcurrentLimit: 5,                    // 10 saturates a free-plan org's 20 runner slots
  prHourlyLimit: 5,
  packageRules: [
    { matchUpdateTypes: ["major"], addLabels: ["renovate-version-major"], minimumReleaseAge: "7 days" },
    { matchUpdateTypes: ["minor"], addLabels: ["renovate-version-minor"], minimumReleaseAge: "3 days", automerge: true },
    { matchUpdateTypes: ["patch"], addLabels: ["renovate-version-patch"], minimumReleaseAge: "3 days", automerge: true },
    { matchUpdateTypes: ["pin"],   addLabels: ["renovate-version-pin"],   automerge: true },   // a pin installs nothing new
    { matchUpdateTypes: ["digest"], addLabels: ["renovate-version-digest"] },
    // GitHub Actions: commit metadata only. The tier rules above decide automerge, so a
    // major action bump (input renames, node runtime changes) waits for a human like any major.
    { matchManagers: ["github-actions"], semanticCommitScope: "github-actions" },
  ],
  automergeType: "pr",
  platformAutomerge: true,
}
```

- No `automerge: true` on any rule that can match a major — every org audited had a
  "v3→v4 is routine" exception on `github-actions`; all were removed.
- Keep only groups whose members *release in lock-step* (a Spring Boot family, a Java
  runtime pin). Groups by *kind* ("maven plugins") let one broken update block six good
  ones. Never a catch-all.
- The default `internalChecksFilter: strict` means a PR is only opened for a version
  already past `minimumReleaseAge` — so `renovate/stability-days` is never required.
- Managers by their real names: `pip_requirements`, not `pip`.
- Forks under an "All repositories" install: `forkProcessing: "enabled"` in **root
  `renovate.json`** (JSONC allowed: `//` comments, double-quoted keys, no trailing commas).

## 2. Ruleset on the default branch (safe-settings suborg file)

```yaml
suborgrepos:
  - myrepo                     # name repos literally; "*" does not match .github
rulesets:
  - name: protect-main
    target: branch
    enforcement: active
    conditions:
      ref_name: { include: ["~DEFAULT_BRANCH"], exclude: [] }   # an empty include matches nothing
    bypass_actors:
      - actor_id: 1            # or RepositoryRole 5; both converge on 2.1.18
        actor_type: OrganizationAdmin
        bypass_mode: always
      # never Renovate: a bypass exempts its PRs from every rule, checks included
    rules:
      - type: deletion
      - type: non_fast_forward
      - type: pull_request
        parameters:
          required_approving_review_count: 1
          dismiss_stale_reviews_on_push: true
          require_code_owner_review: false
          require_last_push_approval: false
          required_review_thread_resolution: true
          allowed_merge_methods: ["squash"]
      - type: required_status_checks
        parameters:
          strict_required_status_checks_policy: false
          required_status_checks:
            - { context: "Build & gates",     integration_id: 15368 }   # GitHub Actions
            - { context: "CodeQL",            integration_id: 57789 }   # Advanced Security default setup
            - { context: "Analyze (actions)", integration_id: 15368 }
            - { context: "DCO",               integration_id: 1861 }    # DCO App
```

- Required = **every** job that runs on **every** PR. Excluded: path-filtered workflows,
  `renovate/stability-days`, anything that only runs on some PRs.
- `require_extra_approval_for_unattributed_changes: true` is fine — bot commits are
  attributed; verified merging `CLEAN` with only the App's approval.
- A `repos/<name>.yml` override cannot supply `required_status_checks` (nested arrays
  concatenate and the PUT 422s); a repo with its own list gets a whole suborg file.
- Two suborg files claiming one repo → "Multiple suborg configs" error.
- The plugin **deletes** any repository ruleset not declared. List hand-made rulesets
  before onboarding and either declare them or accept the deletion in the PR.

## 3. Approvals

- `required_approving_review_count: 1` with the `renovate-approve` App installed on the
  org (or the user account). It approves within seconds of open when the body carries
  `**Automerge**: Enabled` (minor/patch/pin); majors and digests stay `REVIEW_REQUIRED`.
  It re-approves after a stale-review dismissal.
- A solo maintainer cannot approve their own PR; those merge with `--admin` or, for a
  stack, the `merge-async` endpoint — see the `merge-ready` skill.

## 4. Where it is declared

| Repo kind | Rulesets | Declared in |
|---|---|---|
| Org repo, public | yes | safe-settings suborg file |
| Org admin repo (`.github`) | yes — required list is the checks that run on *every* PR there (usually DCO + CodeQL); unfilter `ci.yml`'s `pull_request` trigger if CI should gate | its own suborg file, named literally |
| User-account repo, public | yes | API (`gh api repos/{o}/{r}/rulesets`) — safe-settings is org-only |
| Private repo on a free plan | **no** (API 403) | nothing; Renovate keeps merging itself |

## 5. Repo flags and labels

```bash
gh api repos/O/R --jq '{allow_auto_merge,allow_squash_merge,allow_merge_commit,allow_rebase_merge,delete_branch_on_merge}'
gh api -i repos/O/R/vulnerability-alerts | head -1        # 204 = alerts on; PUT to enable
gh api repos/O/R/automated-security-fixes --jq .enabled   # Dependabot security PRs: false
```

Labels the preset references (`bot-renovate`, `bot-renovate-stop`, `bot-renovate-rebase`,
`renovate-version-*`, `renovate-type-*`, `security`) must exist; declare them in
safe-settings with **every `color:` quoted**.

## 6. Admin repo hygiene (safe-settings workflow)

- `ref: 2.1.18` — last release whose full-sync runs (2.1.19–2.1.21 crash at startup on
  probot 14, upstream github-community-projects/safe-settings#1073). Not Renovate-annotated
  on purpose until a fixed release exists.
- `repository: github-community-projects/safe-settings` (the project moved; the old path
  redirects). `permissions: contents: read` is free hardening — the sync authenticates as
  the App.
- Public admin repo: a scheduled workflow is disabled after 60 days without commits, with
  no red run. Renovate's own action pins usually keep it alive; check that a daily run
  actually happened rather than assuming.
- Folding an admin repo: copy files (history does not follow — take a `git bundle`),
  keep the exclude file (the workflow points at it), archive/delete the old repo **before**
  merging the exclude removal, and before its next cron fires (the concurrency group is
  per repo, two crons in one org race).
