#!/usr/bin/env python3
"""Register a safe-settings GitHub App on an org via GitHub's app-manifest flow.

Serves a one-page form on localhost that POSTs an app manifest to GitHub. The
owner clicks "Create GitHub App" in the browser; GitHub redirects back here with
a code, which this script exchanges for the App ID and private key.

    python3 app-manifest-flow.py --org my-org

Writes <out>/app-conversion.json (mode 0600) containing the App ID, the PEM, the
client secret and the webhook secret. Shred it once the secret is wired.

Stdlib only. No token needed: the conversion endpoint is authenticated by the
one-time code, so the browser session is the only credential involved.
"""

import argparse
import html
import http.server
import json
import os
import socketserver
import sys
import threading
import urllib.parse
import urllib.request

# The permission set safe-settings needs for the repository, labels, rulesets and
# environments plugins, plus headroom for variables, custom properties and its
# PR-check mode. Grant the headroom up front: ADDED permissions require an
# approval click on the installation before they take effect, while REMOVED ones
# apply immediately -- so widening later is the change that stalls.
DEFAULT_PERMISSIONS = {
    "actions": "read",                        # environments on a private repo
    "actions_variables": "write",             # `variables` plugin
    "administration": "write",                # repo settings and rulesets
    "checks": "write",                        # PR-check mode
    "contents": "write",                      # reads safe-settings/*.yml
    "environments": "write",                  # `environments` plugin
    "issues": "write",                        # LABELS live under Issues
    "members": "read",                        # suborg membership
    "metadata": "read",                       # mandatory
    "organization_administration": "read",    # enumerating org repos
    "pull_requests": "write",                 # dry-run PR comments
    "repository_custom_properties": "write",  # `custom_properties` plugin
    "statuses": "write",                      # PR-check mode
}


def build_manifest(args):
    home = args.homepage or f"https://github.com/{args.org}/{args.admin_repo}"
    permissions = DEFAULT_PERMISSIONS
    if args.permissions_json:
        with open(args.permissions_json) as f:
            permissions = json.load(f)
    return {
        "name": args.name,
        "url": home,
        "description": f"safe-settings sync for the {args.org} org (run from Actions, no webhook).",
        # Inactive: full-sync polls from Actions and needs no endpoint. The url is
        # still required by the manifest schema even when active is false.
        "hook_attributes": {"url": home, "active": False},
        "redirect_url": f"http://localhost:{args.port}/callback",
        "public": False,
        "default_events": [],
        "default_permissions": permissions,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--org", required=True, help="GitHub organization login")
    p.add_argument("--name", help="App name (default: <org>-safe-settings)")
    p.add_argument("--admin-repo", default=".github-private", help="repo holding safe-settings config")
    p.add_argument("--homepage", help="App homepage URL (default: the admin repo)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--out", default=".", help="directory for app-conversion.json")
    p.add_argument("--permissions-json", help="file overriding default_permissions")
    p.add_argument("--timeout", type=int, default=900, help="seconds to wait for the browser")
    args = p.parse_args()
    args.name = args.name or f"{args.org}-safe-settings"

    manifest = build_manifest(args)
    out_path = os.path.join(os.path.abspath(args.out), "app-conversion.json")
    done = threading.Event()
    state = {"ok": False}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body, code=200):
            b = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            path, _, query = self.path.partition("?")
            if path == "/":
                self._send(f"""<!doctype html><meta charset=utf-8>
<title>Create {html.escape(args.name)}</title>
<body style="font-family:system-ui;max-width:40rem;margin:4rem auto;line-height:1.5">
<h1>Create the safe-settings GitHub App</h1>
<p>Submitting takes you to GitHub with the manifest prefilled. Make sure you are signed in
as an <b>owner of {html.escape(args.org)}</b>, then click
<b>Create GitHub App for {html.escape(args.org)}</b>.</p>
<form action="https://github.com/organizations/{html.escape(args.org)}/settings/apps/new?state=safe-settings" method="post">
  <input type="hidden" name="manifest" value="{html.escape(json.dumps(manifest))}">
  <button type="submit" style="font-size:1rem;padding:.6rem 1rem">Continue to GitHub</button>
</form>
<details style="margin-top:2rem"><summary>Manifest being submitted</summary>
<pre style="overflow:auto">{html.escape(json.dumps(manifest, indent=2))}</pre></details>
</body>""")
            elif path == "/callback":
                code = urllib.parse.parse_qs(query).get("code", [None])[0]
                if not code:
                    self._send("<p>No <code>code</code> in the callback. Start over at /.</p>", 400)
                    return
                req = urllib.request.Request(
                    f"https://api.github.com/app-manifests/{code}/conversions",
                    method="POST",
                    headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "safe-settings-manifest-flow",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )
                try:
                    with urllib.request.urlopen(req) as r:
                        data = json.load(r)
                except Exception as e:  # noqa: BLE001 - surfaced verbatim to both browser and stderr
                    detail = getattr(e, "read", lambda: b"")().decode()
                    self._send(f"<p>Conversion failed: {html.escape(str(e))}<pre>{html.escape(detail)}</pre></p>", 500)
                    print(f"CONVERSION FAILED: {e}\n{detail}", file=sys.stderr)
                    done.set()
                    return
                fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "w") as f:
                    json.dump(data, f, indent=2)
                state["ok"] = True
                print(f"app_id={data['id']} slug={data['slug']} url={data['html_url']}")
                print(f"wrote {out_path} (contains the private key -- shred it once wired)")
                self._send(f"""<!doctype html><meta charset=utf-8>
<body style="font-family:system-ui;max-width:40rem;margin:4rem auto;line-height:1.5">
<h1>App created</h1>
<p><b>{html.escape(data['slug'])}</b> — App ID {data['id']}. Private key captured.</p>
<p>Next: <a href="{html.escape(data['html_url'])}/installations/new">install it on {html.escape(args.org)}</a>
and choose <b>All repositories</b>. You can close this tab.</p>
</body>""")
                done.set()
            else:
                self._send("<p>not found</p>", 404)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as httpd:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print(f"open http://localhost:{args.port}/ as an owner of {args.org}")
        done.wait(timeout=args.timeout)
        httpd.shutdown()

    if not state["ok"]:
        print("no app was created (timed out or the conversion failed)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
