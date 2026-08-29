# Registering the App via the manifest flow

The [app manifest flow](https://docs.github.com/apps/sharing-github-apps/registering-a-github-app-from-a-manifest)
creates a GitHub App from a JSON document instead of a UI form. It matters here for three
reasons: the permission set is reviewable in a PR rather than reconstructed from screenshots,
a second org becomes a byte-for-byte copy of the first, and the private key arrives
programmatically instead of through a download folder.

`scripts/app-manifest-flow.py` runs the whole thing. Stdlib only, no token.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/app-manifest-flow.py" --org my-org --out ./secrets
```

Then hand the user the URL it prints. They must be signed in as an **owner of the org** —
the browser session is the only credential in the flow.

## What happens

1. The script serves a page on `localhost:8765` with a form whose hidden `manifest` field is
   the JSON app definition, posting to `https://github.com/organizations/<org>/settings/apps/new`.
2. The user clicks through and GitHub shows its normal app-creation confirmation, prefilled.
3. On create, GitHub redirects to `http://localhost:8765/callback?code=…`.
4. The script POSTs `/app-manifests/<code>/conversions` — no auth; the one-time code *is* the
   credential — and writes `app-conversion.json` (mode 0600).

The code expires in about an hour and is single-use. If the exchange fails, the App still
exists: generate a private key from its settings page by hand rather than creating a second App.

## Manifest details worth knowing

- **`hook_attributes.url` is required even when `active` is `false`.** Point it at the admin
  repo. Actions mode polls; there is no endpoint to receive webhooks.
- **`public: false`** — an org-owned private App. safe-settings has no marketplace listing to
  install; you are always registering your own.
- **`default_events: []`** — Actions mode subscribes to nothing.
- **`redirect_url` must match** the port the script listens on. Change one, change both
  (`--port`).

## After the redirect

```bash
gh variable set SAFE_SETTINGS_APP_ID -R <org>/.github-private -b "$(jq -r .id app-conversion.json)"
jq -r .pem app-conversion.json | gh secret set SAFE_SETTINGS_PRIVATE_KEY -R <org>/.github-private
```

Installing is the one step with no API: open `<html_url>/installations/new` and choose
**All repositories**.

Verify the result rather than assuming it:

```bash
gh api /orgs/<org>/installations --jq '.installations[] | {app_slug, repository_selection, permissions}'
```

Then **shred `app-conversion.json`**. It holds the PEM, the client secret and the webhook
secret. It is regenerable; a leak is not recallable.

## Copying an existing org's permission set

If another org already runs safe-settings, take its set verbatim instead of re-deriving it —
this is what keeps two orgs from drifting into different grants:

```bash
gh api /orgs/<source-org>/installations \
  --jq '.installations[] | select(.app_slug=="<source-app-slug>") | .permissions' > perms.json
python3 "${CLAUDE_SKILL_DIR}/scripts/app-manifest-flow.py" --org <new-org> --permissions-json perms.json
```

Requires `admin:org` on the source org.
