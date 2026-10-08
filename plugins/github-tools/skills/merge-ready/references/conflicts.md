# Conflicts that recur

Human PRs only: a bot PR's conflict is resolved by asking the bot to rebase,
never by pushing to its branch.

Most conflicts in an active repo are mechanical, but each has a right answer:

- **Decision-log and changelog rows** (`plan.md` and friends): both sides added
  different rows. Keep both — dropping either loses a decision. Strip the
  markers, re-run the formatter, verify the row count grew.
- **i18n / JSON resources**: both sides added keys to the same object. Keep both
  sets, then **validate the file parses** — the seam between two added blocks
  routinely loses a comma, and a broken JSON resource is not caught by a type
  check. Then confirm key-set parity across languages if the project enforces it.
- **A file the base branch now owns**: if a branch created its own copy of
  something that has since landed on the base, take the base's version and
  **skip** the branch's later commit that deletes it — replaying that deletion
  removes the real file. Verify afterwards that the branch leaves no diff on it.
- **Migration numbering**: two branches both adding `NNNN_*` is invisible to git
  (different filenames) and fatal to the migration runner. The second one to
  merge must renumber — prefer regenerating with the migration tool over hand
  editing, because a hand-edited snapshot chain breaks silently, and re-run the
  migration's verification against a **populated** database afterwards, not a
  fresh one.
- **A formatter that will not converge**: if `format --write` followed by
  `format --check` keeps failing, the file has a construct the formatter is not
  idempotent on (deeply indented nested lists are a common one). Restructure the
  content rather than reformatting again.

