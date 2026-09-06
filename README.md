# Claude Plugins

Personal Claude Code plugins — development standards, quality tools, and GitHub tools.

## Plugins

### dev-standards

Personal development standards that auto-apply based on context.

| Skill | Auto-applies when... |
|---|---|
| `git-workflow` | Creating branches, commits, or pull requests |

### quality

Quality tools. Every skill auto-applies when its description matches, and can also
be invoked explicitly with the slash command shown below.

| Skill | Invocation | Auto-applies when... |
|---|---|---|
| `preflight` | `/quality:preflight` | About to commit or push, or asked for pre-commit checks — validates plugin structure + smoke-tests install (plugin repos), or runs formatter + tests + build (other projects) |
| `create-pr` | `/quality:create-pr` | Creating or updating a PR, or posting the post-deployment comment on a linked issue |
| `full-pr-review` | `/quality:full-pr-review` | Asked for a full or thorough review of a PR — built-in `/review`, `/code-review`, `/security-review` plus inlined cruft check |
| `act-on-pr` | `/quality:act-on-pr` | Asked to act on or address PR review feedback |
| `make-ci-green-again` | `/quality:make-ci-green-again` | Asked to fix failing CI or get the build green |
| `find-smells` | `/quality:find-smells` | Asked what could be cleaned up, refactored, or improved |
| `rubberduck` | `/quality:rubberduck` | Thinking a design through, or asked to rubber-duck a problem |
| `repo-summary` | `/quality:repo-summary` | Asked for a repo summary, recent activity, or what has shipped |
| `gsmp` | `/quality:gsmp` | Asked to go back to main, or to sync main with the remote |
| `grill-me` | `/quality:grill-me` | Asked to stress-test a plan or design |

### github-tools

GitHub tools for the parts of GitHub that have no comfortable CLI.

| Skill | Auto-applies when... |
|---|---|
| `upload` | Attaching images or video to a GitHub PR or issue from the command line |
| `safe-settings` | Setting up, fixing or debugging `github/safe-settings` for an org — App registration via the manifest flow, wiring, and the first sync |
| `renovate-automerge` | Bringing a repo or org onto gated Renovate auto-merge — required checks first, then `platformAutomerge: true`; audit script, checklist and the traps found rolling it out across five orgs |

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
