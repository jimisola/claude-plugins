# Bot PRs: checking the version goes forward

## Read the bot's own summary first

- **Renovate** puts a table in the body with an `Update` column (`major`,
  `minor`, `patch`, `pin`, `digest`, `replacement`…) and a `Change` column of
  the form `` `from` → `to` ``.
- **Dependabot** opens with `Bumps <pkg> from <a> to <b>.` (or
  `Updates the requirements on …`), one line per package in a grouped PR.

Then confirm the diff matches it — a summary that disagrees with the diff is a
reason to stop, not to trust either.

Compare versions as versions, not strings: `sort -V` orders `1.10.0` after
`1.9.0`. It gets pre-releases wrong, though — it puts `1.0.0-rc1` after
`1.0.0`, where semver puts it before — so compare those by hand.

## Per ecosystem

| Ecosystem | Where the version changes | What to compare |
|---|---|---|
| npm / pnpm / yarn | `package.json`, lockfile | the range's lower bound and the locked version |
| Maven | `<version>` in `pom.xml`, or a `<properties>` entry it references | the property value, not just the element |
| Gradle | `gradle/libs.versions.toml`, `build.gradle(.kts)`, `gradle-wrapper.properties` | the catalog entry or the literal |
| Go | `go.mod`, `go.sum` | semver; a pseudo-version (`v0.0.0-<date>-<sha>`) by its timestamp |
| Python | `pyproject.toml`, `requirements*.txt`, lockfile | the pin or lower bound |
| GitHub Actions | `uses: owner/action@<sha> # vX.Y.Z` | the tag in the comment, and that the SHA is that tag's commit |
| Container images | `image:tag@sha256:<digest>` | the tag; for a digest-only update, that the digest is the tag's current one |

## Update types that need more than "it goes up"

- **major** — read the release notes or changelog for breaking changes before
  merging, and name what was read in the report.
- **replacement** — a different package replaces the old one; treat it as a
  human change and check the call sites.
- **digest / pin** — there is no version number to compare; confirm the digest
  or SHA resolves to the tag the comment or table names.
- **downgrade** (`to` older than `from`) — never merge; report it. It usually
  means a yanked release or a constraint elsewhere forcing it back.
