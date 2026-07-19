# Claude Plugins — Development Guide

## Hard Rules — Never Skip

Before **every commit or PR**, complete all mandatory steps in [Local Testing](#local-testing).

Use `/quality:preflight` to run both steps in one go.

---

## Structure

This repo follows the Claude Code plugin marketplace format:

```
claude-plugins/
├── .claude-plugin/marketplace.json    # Marketplace index
├── plugins/
│   ├── dev-standards/                 # Personal development standards
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/                    # Auto-applied skills
│   └── quality-tools/                 # Quality tools (plugin name: quality)
│       ├── .claude-plugin/plugin.json
│       └── skills/                    # Auto-applied + user-invocable skills
```

## Versioning

- Follow [Conventional Commits](https://www.conventionalcommits.org/) for all commits
- Plugin content changes use `feat:` or `fix:` types
- Structural/config changes use `chore:` or `refactor:` types

## Local Testing

**Both steps below are mandatory before committing or raising a PR.**

1. Validate the marketplace structure:

```bash
claude plugin validate .
```

2. Install locally and verify from a neutral directory (use `/tmp` to
   avoid picking up project-local config):

```bash
cd /tmp && claude --plugin-dir /path/to/claude-plugins/plugins/dev-standards --plugin-dir /path/to/claude-plugins/plugins/quality-tools -p "list all available skills and commands from plugins"
```

## Editing Skills

- **SKILL.md files** must have YAML frontmatter with `name` and `description`
- The `description` field controls when a skill auto-applies — write it carefully
- Keep skill content concise and actionable (rules, not prose)

## Skill Reference Files

- Only `SKILL.md` is auto-loaded into context. Keep it concise.
- Move detailed or conditional content into `references/` files
  within the skill directory.
- Reference them from SKILL.md with conditional prose:
  ```
  If the project uses Lombok, see
  [jdtls-lombok-setup.md](references/jdtls-lombok-setup.md)
  ```
- Claude reads reference files on-demand — they don't consume
  context unless relevant.
- Reference files are plain markdown (no frontmatter needed).

## Structuring Skills for Efficient Claude Use

### What belongs in SKILL.md (always loaded)
- **Rules and constraints** stated as compact bullets — what Claude must
  apply immediately without fetching more context
- **Key commands** — build, test, format commands Claude will run regularly
- **Version/stack baseline** — always relevant when working in the codebase
- **Conditional pointers** to reference files — one line per reference

### What belongs in reference files (on-demand)
- **Code examples** — Claude knows the framework; it needs your specific
  conventions, not demonstrations of how annotations work
- **IDE setup and tooling config** — only needed when setting up or debugging
- **Full rationale and background** — link out for the "why";
  reference files for the "how" when there's enough depth to warrant it
- **Scenario-specific detail** — starter configs, edge cases, advanced patterns

### No examples in SKILL.md
Avoid code blocks in SKILL.md. State the rule — don't show it. Move examples
to a reference file and add a conditional pointer. This keeps SKILL.md
scannable and cheap.

### 1:1 mapping with standards documentation
Reference files should map to sections of any corresponding standards
document where those sections have enough depth to warrant a file. Trivial
sections (a single rule or a short table) can stay inline in SKILL.md.

## User-Invocable Skills

- User-invocable skills use `disable-model-invocation: true` in frontmatter — Claude never triggers them automatically
- Invoked as `/quality:skill-name` or `/dev-standards:skill-name`
- Update cross-references in `full-pr-review` skill when adding/removing user-invocable skills
