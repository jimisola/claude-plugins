# Moving a secret into an environment

`OWNER/REPO`, `ENV` and `NAME` throughout. Each step is verified before the next.

## 1. The workflow and the environment, in one PR

The job that uses the secret declares the environment:

```yaml
jobs:
  sync:
    runs-on: ubuntu-latest
    environment: ENV
```

**Where safe-settings manages environments**, declare it in `repos/<repo>.yml` under the
admin repo's config path. Branch policies are plain strings; tags take an object
(`lib/plugins/environments.js` expands both at 2.1.18):

```yaml
environments:
  - name: ENV                      # lowercase; the plugin lowercases names anyway
    deployment_branch_policy:
      protected_branches: false
      custom_branch_policies:
        - main                     # a nightly sync
```

A publishing environment takes the tag form instead: `- {type: tag, names: ["v*"]}`.

No `reviewers:` on an environment a schedule uses. If a suborg file also declares
`environments:` for the repo, the two lists concatenate; an environment in neither is deleted.

**Where nothing manages environments**, create it by API before merging, so the workflow
never meets an auto-created open one:

```bash
gh api -X PUT repos/OWNER/REPO/environments/ENV --input - <<'EOF'
{"deployment_branch_policy": {"protected_branches": false, "custom_branch_policies": true}}
EOF
gh api -X POST repos/OWNER/REPO/environments/ENV/deployment-branch-policies -f name=main -f type=branch
# release tags instead:  -f name='v*' -f type=tag
```

Verify what is in force, not what was sent:

```bash
gh api repos/OWNER/REPO/environments/ENV --jq '{protection_rules, deployment_branch_policy}'
gh api repos/OWNER/REPO/environments/ENV/deployment-branch-policies --jq '.branch_policies[] | {name, type}'
```

## 2. Re-issue the value into the environment

Nothing can read a secret back, from the UI or the API. Moving one means issuing a new value.

### A GitHub App private key

1. The user generates a new key: App settings → *Private keys* → *Generate a private key*
   (`https://github.com/organizations/ORG/settings/apps/SLUG`, or
   `https://github.com/settings/apps/SLUG` for a user-owned App). There is no API for this.
   The browser downloads a `.pem`.
2. Record its fingerprint, pipe it into the secret, shred it — the file never moves into a
   repo, not even briefly:

   ```bash
   pem=~/Downloads/SLUG.YYYY-MM-DD.private-key.pem
   openssl rsa -in "$pem" -pubout -outform DER | openssl sha256 -binary | openssl base64   # new key's fingerprint
   gh secret set NAME --env ENV -R OWNER/REPO < "$pem"
   shred -u "$pem"
   ```

3. Test (step 4 below), then delete the **old** key on the same settings page — the one whose
   `SHA256:` fingerprint is not the one just printed. Only after every repo holding the old
   key has moved; an App can hold several keys at once, so there is no gap.

### A third-party token (Gradle Plugin Portal, npm, PyPI, Maven Central, Expo, Docker Hub…)

The agent never handles the value. Prefer issuing a **new** token scoped as narrowly as the
registry allows (one package, publish only), so the old one can be revoked rather than
shared between two stores. The user runs, at the Claude Code prompt or in their own terminal:

```
! gh secret set NAME --env ENV -R OWNER/REPO
```

and pastes at the hidden prompt. Then confirm the timestamp moved:

```bash
gh secret list --env ENV -R OWNER/REPO
```

## 3. Remove the repository secret

```bash
gh secret delete NAME -R OWNER/REPO
```

Now a job without `environment: ENV` sees no `NAME` at all. If another workflow still needed
it, this is where it fails — which is the point; `grep -rn 'secrets.NAME' .github/` first.

## 4. Prove it from the protected ref

```bash
gh workflow run WORKFLOW.yml -R OWNER/REPO --ref main
gh run watch -R OWNER/REPO "$(gh run list -R OWNER/REPO -w WORKFLOW.yml -L1 --json databaseId -q '.[0].databaseId')"
```

A green run here is the only evidence the environment secret is the one being used. For a
tag-gated publish, a dry-run or pre-release tag is the equivalent. Then revoke the old
App key or registry token.
