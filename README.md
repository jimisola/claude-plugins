# Claude Plugins

Personal Claude Code plugins — development standards, quality tools, and GitHub tools.

## Plugins

### dev-standards

Personal development standards that auto-apply based on context.

| Skill | Auto-applies when... |
|---|---|
| `git-workflow` | Creating branches, commits, or pull requests |

### quality

Quality tools — both auto-applied skills and user-invocable commands.

**Skills (auto-applied):**

| Skill | Auto-applies when... |
|---|---|
| `repo-summary` | User asks for repo summary, recent activity, or executive summary |

#### Commands

| Command | Invocation | Purpose |
|---|---|---|
| preflight | `/quality:preflight` | Mandatory pre-commit checks — validates plugin structure + smoke-tests install (plugin repos), or runs formatter + tests + build (other projects) |
| full-pr-review | `/quality:full-pr-review` | Parallel quality checks on PR — built-in `/review`, `/code-review`, `/security-review` plus inlined cruft check |
| act-on-pr | `/quality:act-on-pr` | Analyze & address PR review comments |
| make-ci-green-again | `/quality:make-ci-green-again` | Watch CI, fix failures, re-check until green |
| rubberduck | `/quality:rubberduck` | Staff/Senior-level thinking partner for problem-solving |
| gsmp | `/quality:gsmp` | Switch to main branch and pull latest |
| grill-me | `/quality:grill-me` | Stress-test a plan or design via relentless questioning |

### github-tools

GitHub tools built on undocumented-but-useful endpoints.

| Skill | Auto-applies when... |
|---|---|
| `upload` | Attaching images or video to a GitHub PR or issue from the command line |

## Installation

### 1. Add the marketplace (one-time setup)

```
/plugin marketplace add jimisola/claude-plugins
```

### 2. Install plugins

```
/plugin install dev-standards@claude-plugins
/plugin install quality@claude-plugins
/plugin install github-tools@claude-plugins
```

Or use the interactive UI: `/plugin` → **Discover** tab → select plugins and choose scope (user / project / local).

### Updating

To refresh plugin listings after upstream changes:

```
/plugin marketplace update claude-plugins
```

## Local Testing

```bash
claude --plugin-dir ./plugins/dev-standards --plugin-dir ./plugins/quality-tools --plugin-dir ./plugins/github-tools
```
