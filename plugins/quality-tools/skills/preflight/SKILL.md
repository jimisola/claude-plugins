---
name: preflight
description: Run all mandatory checks before committing or pushing. Detects project type automatically — plugin marketplace repos run validate + install test; other projects run formatter, tests, and build.
disable-model-invocation: true
---
# Preflight

Detect project type and run the appropriate mandatory checks before committing or pushing.

## Plugin marketplace repo (`.claude-plugin/marketplace.json` present)

Both steps are required — do not skip either.

### 1. Validate structure

```bash
claude plugin validate .
```

Must exit with `✔ Validation passed`. Fix any errors before continuing.

### 2. Install and smoke-test from `/tmp`

```bash
REPO="$PWD"
ARGS=()
for p in "$REPO"/plugins/*/.claude-plugin/plugin.json; do
  ARGS+=(--plugin-dir "$(dirname "$(dirname "$p")")")
done
cd /tmp && claude "${ARGS[@]}" -p "list all available skills and commands from plugins"
```

Run from the repo root (same as step 1). Every plugin under `plugins/` is
discovered automatically, so newly added plugins are included without editing
this skill.

Verify: both plugins load, all expected skills appear (including any newly added ones), no errors.

---

## Other projects (Gradle, Maven, npm, etc.)

Detect the build tool (`build.gradle` → Gradle, `pom.xml` → Maven, `package.json` → npm/pnpm, etc.) and use the appropriate commands from the project's conventions (loaded via plugin skills).

1. Run the project's formatter/linter auto-fix and resolve any remaining formatting issues.
2. Run unit tests and fix all failures.
3. Run integration tests and fix all failures.
4. Run the full build and fix any remaining errors (lint violations, compilation, etc.).
