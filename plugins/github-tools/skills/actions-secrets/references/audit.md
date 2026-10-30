# Auditing Actions secrets across an account

Read-only throughout. Names of secrets are listable; values never are, and are not needed.

## Scope

The user's own account plus every org where they are admin, non-archived and non-fork repos:

```bash
owners=$( { gh api user --jq .login
            gh api user/memberships/orgs --paginate --jq '.[] | select(.role=="admin") | .organization.login'; } )
for o in $owners; do
  gh repo list "$o" --no-archived --source -L 1000 --json nameWithOwner -q '.[].nameWithOwner'
done > repos.txt
```

## Per repo

```bash
r=OWNER/REPO
gh api "repos/$r/actions/secrets" --jq '.secrets[] | {name, updated_at}'                 # repo-level: flag every one
gh api "repos/$r/actions/organization-secrets" --jq '.secrets[] | {name, visibility}'     # org secrets this repo can read
gh api "repos/$r/environments" --jq '.environments[] | {name, deployment_branch_policy,
  rules: [.protection_rules[].type]}'
gh api "repos/$r/environments/ENV/deployment-branch-policies" --jq '.branch_policies[] | {name, type}'
gh api "repos/$r/environments/ENV/secrets" --jq '.secrets[].name'
gh api "repos/$r/collaborators" --paginate --jq '.[] | select(.permissions.push) | "\(.login)\t\(.role_name)"'
gh api "repos/$r/dependabot/secrets" --jq '.secrets[].name'                              # separate store, same question
```

For each repository secret, find what uses it: `gh search code "secrets.NAME" --repo $r`
(default branch only), or grep a checkout's `.github/workflows/`.

Flag:

- every **repository secret** and every **org secret visible to the repo** — reachable from
  any branch;
- every environment holding secrets with `deployment_branch_policy: null` — same exposure;
- a branch or tag policy naming a ref that writers can push without review (read
  `repos/$r/rules/branches/main`, and the tag rulesets);
- a scheduled workflow whose environment has `required_reviewers` — it is stalling.

## What an App key grants

A key's reach is its App's installation, not the repo it sits in:

```bash
gh api orgs/ORG/installations --jq '.installations[] | {app_slug, app_id, repository_selection, permissions}'
```

For an App installed on the user account, read the same from Settings → Applications →
Installed GitHub Apps; that listing needs the App's own credentials through the API.

Match a secret to its App through the workflow (`app-id:` / `vars.*_APP_ID`) or the
secret's name. The same App id appearing in several repos means one key in several stores —
all of them move before the old key is revoked.

## Grading

Exposure today = what the credential grants **minus** what the repo's writers already hold.

```bash
gh api "orgs/ORG/members?role=admin" --paginate --jq '.[].login'   # org owners
```

- Every writer is an org owner, and the key is an org-scoped App → **latent**: nothing is
  exposed now, the next outside collaborator inherits it. Fix, but say it is latent.
- A writer who is not an owner can reach a key with org-wide `administration: write`, or a
  publish token for a package they do not maintain → **real**, fix first.
- A token granting what a writer already has → **none**; leave it a repository secret.

Report the grade with the reason for it. A list where everything is critical gets ignored.

## Recording findings

Never in a public issue. A draft repository security advisory is private to admins and
whoever is added to it:

```bash
gh api --method POST repos/OWNER/REPO/security-advisories --input - <<'EOF'
{
  "summary": "Workflow credential reachable from any branch",
  "description": "What the credential grants, who can reach it today, the grade and why, the fix.",
  "severity": "low",
  "vulnerabilities": [{"package": {"ecosystem": "actions", "name": "OWNER/REPO"}}]
}
EOF
```

The fix PR is public: describe the change ("move the release token to a tag-gated
environment"), not the exposure it closes.
