---
name: actions-secrets
description: Create, move and audit GitHub Actions secrets so a credential reaches only the refs that need it — an environment secret behind a deployment branch or tag policy rather than a repository or organization secret, declared in safe-settings where that manages environments, and re-issued rather than copied when it moves. Use whenever the user creates or adds an Actions secret, runs or asks for `gh secret set`, sets up a GitHub App or its private key for a workflow, wires publishing credentials (Gradle Plugin Portal, npm, PyPI, Maven Central, Expo, Docker Hub), creates or changes a GitHub environment, or asks to audit, review or rotate a repo's or org's secrets — even if they only say "add the token to the repo".
---

A repository secret is not scoped to the workflow that uses it. GitHub hands it to **every
workflow run triggered from a branch of that repo** — `push`, and `pull_request` from a
same-repo branch — including a workflow file the branch adds itself. Anyone who can push a
branch can therefore read every repository secret, and an organization secret visible to the
repo, with a ten-line workflow. A job-level `if:` or a trigger filter in the workflow that
*legitimately* uses the secret protects nothing: the attacker writes a different workflow.

Fork PRs do not get secrets (outside `pull_request_target`/`workflow_run`, a separate risk).
The exposure here is to **write collaborators**, which is why it is so easy to miss.

## Where a secret goes

- **Grants nothing a write collaborator does not already have** (a read-only API key, a
  webhook for a channel they are in) → a repository secret is fine.
- **Grants more** — an App key with admin or cross-repo scope, a registry publish token, a
  signing key, a cloud deploy role → an **environment secret**, and the job declares
  `environment:`. This is the default for anything new; the question is asked per
  credential, not per repo.
- An **organization secret** follows the same rule, multiplied by every repo it is visible
  to. Prefer an environment secret in the one repo that needs it.

## Environments

- **The deployment branch/tag policy is the protection.** Limit it to the refs that
  legitimately use the credential: `main` for a nightly sync, `v*` tags for publishing. An
  environment with no policy is available to every branch, i.e. a repository secret with
  extra steps. A `pull_request` run's ref is `refs/pull/N/merge`, so it never matches.
- **The policy is only as strong as the ref it names.** `main` must require a reviewed PR
  for writers; a `v*` tag policy needs a tag ruleset restricting who may create matching
  tags. Otherwise a writer pushes the ref and gets the secret.
- **No required reviewer on an environment a scheduled job uses** — the run waits for an
  approval nobody is there to give, and the schedule silently stalls. Reviewers belong on
  release and publish gates, where a human started the run.
- **GitHub creates a missing environment on first use, unprotected.** A workflow change
  that references an environment before it is configured gets an open one. Create and
  protect the environment first or in the same change, never after.

## When safe-settings manages environments

Once any `environments:` list applies to a repo, the environments plugin **deletes every
environment of that repo it does not find in the config — with its secrets**
(`lib/plugins/environments.js`, `sync()` calling `remove()`, at 2.1.18). So the
environment is declared in safe-settings, normally a per-repo override
`repos/<repo>.yml`, in the same PR as the workflow change or earlier. An environment
created only by API or UI survives until the next sync. The YAML, including a tag policy,
is in [references/moving-a-secret.md](references/moving-a-secret.md); the `safe-settings`
skill covers the rest of the config.

## Moving a secret — the order that never breaks a run

1. Merge the workflow change (`environment:` on the job) **together with** the environment
   declaration. The repository secret still resolves meanwhile — a job sees repository
   secrets too — so nothing breaks.
2. Set the environment secret (re-issued, see below).
3. Delete the repository secret.
4. Dispatch a manual run **from the protected ref** and read it green. That run is the only
   proof the environment secret is the one being used.

Secret values cannot be read back, so moving a secret means **re-issuing** it. Commands for
each step, GitHub App keys and third-party tokens:
[references/moving-a-secret.md](references/moving-a-secret.md).

## Handling the value

- **The agent never sees a third-party token.** The user runs
  `! gh secret set NAME --env ENV -R OWNER/REPO` and pastes at the hidden prompt. Never
  `--body` with a literal: it lands in shell history and the transcript.
- **A GitHub App key goes from the download straight into `gh secret set` on stdin**, then
  the file is shredded. App keys are generated in the App's settings page only — there is
  no API — so that step is the user's.
- **Never write a secret into the working tree**, not even a gitignored path. This is the
  user's global rule — *Secrets never live in a repo* in `~/.claude/CLAUDE.md` — follow it
  as written there.
- **Revoke the old App key only after every holder has the new one.** One App key is often
  set in several repos; the audit finds them.

## Auditing

Read-only, over the user's account and every org where they are admin: repository and org
secrets, environments and their policies, who can push, and what each App key's
installation can do. Recipe: [references/audit.md](references/audit.md).

- **Grade exposure honestly.** A repository secret is exposed to the repo's writers, so it
  matters only if they do not already hold what it grants. An org App key where every
  writer is an org owner exposes nothing today — say so, call it latent, and still move it
  before the next collaborator arrives. Do not call everything critical.
- **Do not track findings in public issues.** Use a draft repository security advisory, and
  word the public PR that fixes it neutrally ("move the release token to an environment"),
  not as a description of how to exploit the repo it is merged into.
