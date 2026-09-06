#!/usr/bin/env bash
# audit-repo.sh OWNER/REPO [default-branch]
#
# Read-only audit of one repository against the renovate-automerge target setup.
# Prints, in order: rules actually in force on the default branch, PR-triggered jobs
# parsed from the workflows, the check-runs on the newest PR head with their app ids,
# repo flags (auto-merge, merge methods, Dependabot alerts/updates, dependabot.yml),
# and Renovate-config red flags. It changes nothing.
#
# Needs: gh (authenticated), jq, python3 with PyYAML (workflow parsing degrades to a
# note without it).
set -euo pipefail
R=${1:?usage: audit-repo.sh OWNER/REPO [default-branch]}
B=${2:-$(gh api "repos/$R" --jq .default_branch)}
hr(){ printf '\n== %s ==\n' "$1"; }

hr "repo $R (default branch: $B)"
gh api "repos/$R" --jq '"visibility=\(.visibility) archived=\(.archived) fork=\(.fork) allow_auto_merge=\(.allow_auto_merge) squash=\(.allow_squash_merge) merge_commit=\(.allow_merge_commit) rebase=\(.allow_rebase_merge) delete_branch_on_merge=\(.delete_branch_on_merge)"'
code=$(gh api -i "repos/$R/vulnerability-alerts" 2>/dev/null | head -1 | awk '{print $2}')
case "${code:-}" in 204) a=ON;; 404) a=OFF;; *) a="?${code:-}";; esac
sf=$(gh api "repos/$R/automated-security-fixes" --jq .enabled 2>/dev/null || echo '?')
echo "dependabot_alerts=$a dependabot_security_updates=$sf"
if gh api "repos/$R/contents/.github/dependabot.yml" --jq .name >/dev/null 2>&1; then
  echo "FLAG: .github/dependabot.yml present — Renovate owns every ecosystem; remove it"
fi

hr "rules IN FORCE on $B (GET /rules/branches — the only view that counts)"
rules=$(gh api "repos/$R/rules/branches/$B" 2>/dev/null || echo '[]')
if [ "$(echo "$rules" | jq length)" = "0" ]; then
  echo "NONE — no ruleset matches $B (rulesets may still be listed; check conditions.ref_name.include)"
else
  echo "$rules" | jq -r '.[]|.type' | sort | tr '\n' ' '; echo
  echo "$rules" | jq -r '.[]|select(.type=="pull_request")|.parameters|"approvals=\(.required_approving_review_count) dismiss_stale=\(.dismiss_stale_reviews_on_push) thread_resolution=\(.required_review_thread_resolution) merge_methods=\(.allowed_merge_methods // "any")"'
  echo "$rules" | jq -r '.[]|select(.type=="required_status_checks")|.parameters|"strict=\(.strict_required_status_checks_policy)", (.required_status_checks[]|"  required: \(.context)\t@\(.integration_id // "null")")'
fi
echo "-- rulesets listed on the repo (declared, not necessarily in force):"
gh api "repos/$R/rulesets" --jq '.[]|"  \(.name)\tid=\(.id)\tenforcement=\(.enforcement)"' 2>/dev/null || echo "  (403: private repo on a free plan — rulesets unavailable)"
for id in $(gh api "repos/$R/rulesets" --jq '.[].id' 2>/dev/null); do
  gh api "repos/$R/rulesets/$id" --jq '"  \(.name): include=\(.conditions.ref_name.include) bypass=\([.bypass_actors[]?|"\(.actor_type):\(.actor_id)"]|join(",")) updated_at=\(.updated_at)"'
done

hr "PR-triggered jobs from .github/workflows (unfiltered = candidate for the required list)"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for p in $(gh api "repos/$R/contents/.github/workflows" --jq '.[]|select(.name|test("\\.ya?ml$"))|.path' 2>/dev/null); do
  gh api "repos/$R/contents/$p" --jq .content | base64 -d > "$tmp/$(basename "$p")"
done
if ls "$tmp"/*.y*ml >/dev/null 2>&1; then
python3 - "$tmp" <<'EOF' 2>/dev/null || echo "  (python3+PyYAML unavailable — read the workflows by hand)"
import sys, glob, os, yaml
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.y*ml'))):
    try: d = yaml.safe_load(open(f))
    except Exception as e: print(f"  {os.path.basename(f)}: unparsable ({e})"); continue
    on = d.get(True, d.get('on')) if isinstance(d, dict) else None
    if on is None: continue
    trig = on if isinstance(on, dict) else {k: {} for k in (on if isinstance(on, list) else [on])}
    pr = next((trig[k] or {} for k in ('pull_request', 'pull_request_target') if k in trig), None)
    if pr is None: continue
    paths = pr.get('paths') or pr.get('paths-ignore')
    branches = pr.get('branches')
    tag = 'PATH-FILTERED (never require)' if paths else ('branch-filtered' if branches else 'unfiltered')
    print(f"  {os.path.basename(f)}: {tag}")
    for jid, j in (d.get('jobs') or {}).items():
        name = j.get('name') or jid
        notes = []
        if 'uses' in j: notes.append('reusable → context is "<caller> / <called>"')
        if 'strategy' in j and 'matrix' in (j.get('strategy') or {}): notes.append('MATRIX → context gets "(values)" suffix; require an aggregator instead')
        if isinstance(name, str) and '${{' in name: notes.append('interpolated name → unstable context')
        if 'if' in j: notes.append(f"if: {j['if']}")
        print(f"     job: {name}" + (f"   [{'; '.join(notes)}]" if notes else ''))
EOF
else
  echo "  no workflows"
fi

hr "check-runs and statuses on the newest PR head (context → app id)"
pr=$(gh pr list -R "$R" --state all --limit 1 --json number,headRefOid,author,createdAt --jq '.[0]')
if [ -n "$pr" ] && [ "$pr" != "null" ]; then
  n=$(echo "$pr" | jq -r .number); sha=$(echo "$pr" | jq -r .headRefOid)
  echo "PR #$n by $(echo "$pr" | jq -r .author.login) ($(echo "$pr" | jq -r .createdAt))"
  gh api "repos/$R/commits/$sha/check-runs?per_page=100" --jq '.check_runs[]|"  \(.name)\t@\(.app.id) \(.app.slug)\t\(.conclusion // .status)"' | sort -u
  gh api "repos/$R/commits/$sha/status" --jq '.statuses[]|"  \(.context)\t(commit status)\t\(.state)"' 2>/dev/null
else
  echo "  no PRs yet — required contexts cannot be confirmed on a real head"
fi
gh api "repos/$R/code-scanning/default-setup" --jq '"code-scanning default setup: \(.state) languages=\(.languages)"' 2>/dev/null || true

hr "Renovate config"
cfg=""
for f in renovate.json renovate.json5 .github/renovate.json .github/renovate.json5 .renovaterc .renovaterc.json; do
  if c=$(gh api "repos/$R/contents/$f" --jq .content 2>/dev/null); then cfg=$f; printf '%s' "$c" | base64 -d > "$tmp/renovate-config"; break; fi
done
if [ -z "$cfg" ]; then echo "  none found (repo runs on Renovate defaults, or the org preset does not apply)"; else
  echo "  file: $cfg"
  isfork=$(gh api "repos/$R" --jq .fork)
  [ "$isfork" = "true" ] && [ "$cfg" != "renovate.json" ] && echo "  FLAG: fork with config at $cfg — the hosted app's fork gate reads only root renovate.json"
  grep -nE 'extends|platformAutomerge|automergeType|dependencyDashboard|branchPrefix|internalChecksFilter' "$tmp/renovate-config" | sed 's/^/  /'
  grep -nE 'branchPrefix:?\s*["'"'"']renovate["'"'"']' "$tmp/renovate-config" >/dev/null && echo "  FLAG: branchPrefix without trailing slash"
  grep -nE '\{\{groupId\}\}' "$tmp/renovate-config" >/dev/null && echo "  FLAG: {{groupId}} is not a template field — renders empty, groups everything"
  grep -nE 'matchManagers.*github-actions' -A3 "$tmp/renovate-config" | grep -q 'automerge: *true' && echo "  FLAG: github-actions rule carries automerge — majors would automerge"
  grep -nE '"pip"|\bpip\b\s*[],]' "$tmp/renovate-config" >/dev/null && echo "  FLAG: manager 'pip' does not exist (pip_requirements)"
fi
echo "-- recent Renovate PRs (marker = body carries **Automerge**: Enabled):"
gh pr list -R "$R" --author app/renovate --state all --limit 5 --json number,createdAt,mergedAt,mergedBy,body,reviewDecision,autoMergeRequest --jq '.[]|"  #\(.number) created=\(.createdAt[0:16]) merged=\(.mergedAt[0:16] // "-") by=\(.mergedBy.login // "-") review=\(.reviewDecision) autoMerge=\(.autoMergeRequest != null) marker=\(.body|test("\\*\\*Automerge\\*\\*: Enabled"))"' 2>/dev/null || echo "  none"
