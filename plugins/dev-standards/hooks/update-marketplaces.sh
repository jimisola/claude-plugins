#!/usr/bin/env bash
# Workaround for https://github.com/anthropics/claude-code/issues/26744
# /reload-plugins fetches but never pulls — this pulls all marketplace repos
# on session start so plugins are always fresh.
set -euo pipefail
shopt -s nullglob

MARKETPLACES_DIR="$HOME/.claude/plugins/marketplaces"

[[ -d "$MARKETPLACES_DIR" ]] || exit 0

for dir in "$MARKETPLACES_DIR"/*/; do
    [[ -d "$dir/.git" ]] || continue
    git -C "$dir" pull --ff-only --quiet 2>/dev/null || true
done
