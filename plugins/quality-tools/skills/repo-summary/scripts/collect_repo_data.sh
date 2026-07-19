#!/usr/bin/env bash
# Collects git commits and merged PRs for a given time period.
# Usage: collect_repo_data.sh [--since "1 week ago"] [--workspaces "dir1,dir2,..."]
#
# Output: structured text with commits grouped by workspace path.

set -euo pipefail

SINCE="1 week ago"
WORKSPACES=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --workspaces) WORKSPACES="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

SINCE_DATE=$(date -j -f "%Y-%m-%d" "$(git log -1 --format=%ci --since="$SINCE" 2>/dev/null | head -1 | cut -d' ' -f1)" "+%Y-%m-%d" 2>/dev/null || true)
ISO_SINCE=$(git log --format=%ci --reverse --since="$SINCE" | head -1 | cut -d' ' -f1)

echo "=== REPO SUMMARY DATA ==="
echo "Period: since $SINCE"
echo "Branch: $(git branch --show-current)"
echo ""

# --- Section 1: Commits ---
echo "=== COMMITS ==="
echo "Total: $(git log --oneline --since="$SINCE" | wc -l | tr -d ' ')"
echo ""

# Group commits by top-level directory changed
git log --since="$SINCE" --pretty=format:"COMMIT|%h|%an|%as|%s" --name-only | awk '
BEGIN { commit=""; hash=""; author=""; date=""; subject="" }
/^COMMIT\|/ {
    split($0, parts, "|")
    hash=parts[2]; author=parts[3]; date=parts[4]; subject=parts[5]
    commit=hash
    next
}
/^$/ { next }
{
    if (commit != "") {
        # Extract workspace path (first two path segments or just first)
        n = split($0, segs, "/")
        if (n >= 2) {
            dir = segs[1] "/" segs[2]
        } else {
            dir = segs[1]
        }
        # Only print once per commit per directory
        key = commit SUBSEP dir
        if (!(key in seen)) {
            seen[key] = 1
            printf "%s|%s|%s|%s|%s\n", dir, hash, author, date, subject
        }
    }
}
'

echo ""

# --- Section 2: Merged PRs ---
echo "=== MERGED PRs ==="
if command -v gh &>/dev/null; then
    gh pr list --state merged --search "merged:>=$(date -v-${SINCE// /}d +%Y-%m-%d 2>/dev/null || echo "$ISO_SINCE")" --limit 50 --json number,title,author,mergedAt,labels 2>/dev/null || echo "(gh cli not available or not authenticated)"
else
    echo "(gh cli not installed — skipping PR data)"
fi

echo ""

# --- Section 3: Contributors ---
echo "=== CONTRIBUTORS ==="
git log --since="$SINCE" --pretty=format:"%an" | sort | uniq -c | sort -rn

echo ""
echo "=== END ==="
