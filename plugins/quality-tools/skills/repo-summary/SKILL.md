---
name: repo-summary
description: Generate an executive summary of recent repository activity — commits, merged PRs, and contributors grouped by workspace.
disable-model-invocation: true
---

# Repo Summary

Generate a concise executive summary of repository activity for a given time period, grouped by workspace area.

## Workflow

### 1. Collect data

Run the bundled collection script from the repo root:

```bash
bash SKILL_DIR/scripts/collect_repo_data.sh --since "<period>"
```

**Default period:** `"1 week ago"` (when the user doesn't specify).

**Examples of valid `--since` values:**
- `"1 week ago"`, `"2 weeks ago"`, `"1 month ago"`, `"3 days ago"`
- `"2026-01-01"` (absolute date)

### 2. Synthesize the summary

Using the script output, produce a markdown summary printed directly in the conversation with this structure:

```
## Executive Summary — [repo name] ([date range])

### Highlights
- 3-5 bullet points of the most important changes across the whole repo

### [Workspace Name]
- Bullet points summarizing what changed, referencing PR numbers where available

### [Workspace Name]
- ...

(repeat for each workspace that had activity)

### Contributors
- List of contributors and their focus areas for this period
```

**Guidelines:**
- Lead with business impact, not implementation details
- Group related commits into single bullet points (e.g. multiple commits for one PR = one bullet)
- Reference PR numbers as `#123` when available
- Use concise language — each bullet should be one line
- Skip workspaces with no activity
- For the date range header, use the actual dates from the git log (first and last commit dates)
