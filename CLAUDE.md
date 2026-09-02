# CLAUDE.md

Guidance for Claude Code working in this repo. Kept short — detail
lives in `docs/architecture.md`, `docs/internal/design.md` (see note
below), and `README.md`, not here.

**`docs/internal/` is a private git submodule (`trailsign-internal`) —
check it before assuming design history/rationale doesn't exist.** A
plain `git clone` of this repo leaves `docs/internal/` as an empty
directory; if you have access to the private repo, run
`git submodule update --init` to populate it. If it stays empty after
that (permission denied), you don't have access — that's expected for
an external contributor, not a bug. Treat `docs/architecture.md` as the
design reference in that case instead. This split is deliberate (see
"Where to look" below): the full design doc is written for a Claude
session's own use, not for a public audience, and was moved out of the
public repo 2026-09-02 for that reason, not because it held anything
newly sensitive.

## Overview

Trailsign is a small, language-independent library for resolving
application settings from a declarative, self-describing config, where
each value declares its own source (a literal, an environment variable,
a vault secret, ...) instead of the caller assuming where to look.
**Published on PyPI as of 2026-09-01 (v0.1.0)** — `pip install
trailsign` works. `src/trailsign/` is a real installable package
(`pyproject.toml`, src layout) with a test suite (`tests/`). MIT
licensed, public on GitHub (https://github.com/nankma/trailsign), CI
(`.github/workflows/test.yml`) runs on push/PR, `main` requires a
passing PR before merge. Cutting a new GitHub Release triggers
`.github/workflows/publish.yml` to auto-publish to PyPI (Trusted
Publishing, no stored token) — bump `version` in `pyproject.toml` first.
A port to a second language is the main remaining open work.

Extracted from a Telegram news-trend bot (Auguring, formerly Argus)
where this design started — see `docs/internal/design.md`'s own
"Origin" section for why it moved here instead of staying bot-specific.

## Landmines

- **`trailsign-resolve:` is the only dispatch key — never rename it back
  to a bare `resolve`, and never let it collide with `type:` or any
  other field.** Two real bugs already happened this way (an overloaded
  `type:` field, then a plain `resolve:` that was still a generic
  collision risk) before landing here — see `docs/internal/design.md`'s "Fixing
  an ambiguity" section before touching the dispatch key.
- **`trailsign-credential-sources` is the reserved top-level key for
  named vault connections — never rename it back to bare
  `credential_sources`.** Same collision reasoning as `trailsign-resolve`
  (see "Fixing an ambiguity"'s "Round three"), applied one release late
  (v0.1.0 shipped with the bare name; renamed for v0.2.0, before any real
  consumer migrated onto the old schema).
- **This library never constructs consumer objects, only resolves values
  to plain data.** Turning a resolved config block into a live object
  (an adaptor, a client, anything) is always the *consumer's* own
  factory, never this library's job — see `docs/architecture.md`'s "Two
  jobs, two owners" section (public — this rule applies to any
  contributor, not just internal ones). Don't add object-construction
  here even if it seems convenient for a first real consumer.
- **`OracleKeyVaultResolver` uses instance-principal auth
  (`_oci_secrets_client()` in `src/trailsign/settings.py`) — not a
  static config file, not an explicit key.** Verified 2026-09-01 against
  a real OCI Vault secret from a compute instance (see
  `tools/verify_oracle_vault.py`); only works from inside an OCI compute
  instance (requires a dynamic-group IAM policy granting `read
  secret-bundles` — a real gap hit during that verification, not a code
  bug). `trailsign-credential-sources`' `region`/`vault_ocid`/`compartment_ocid`
  fields are validated to exist via `source:` but are **not** actually
  consumed by this auth shape — don't assume they're load-bearing if
  refactoring this resolver; see `docs/architecture.md`'s note under
  "The config shape" (public — same reasoning: don't overclaim what a
  field does).
- **`OracleKeyVaultResolver.resolve()` validates the node's own fields
  (`source`, `secret_ocid`) *before* `import oci`.** This was a real bug
  found while writing tests: `import oci` used to run first, so a
  missing `secret_ocid` raised `ModuleNotFoundError` instead of
  `SettingsError` whenever the `oci` package wasn't installed — breaking
  the "no oci dependency needed unless actually used" guarantee for the
  validation-error paths, not just the happy path. Keep the import after
  field validation if this method is touched again.
- **Secret hygiene**: never commit real infrastructure values (VM IPs,
  SSH key paths, live OCIDs). `local-infra/infrastructure.yaml` holds
  them and is gitignored; `tools/verify_oracle_vault.py` takes everything
  sensitive via CLI arg only and stays secret-free so it's safe to
  commit. (The repo went public 2026-09-01, after running
  `D:\SR\MyFirstAgent\.claude\skills\audit-before-going-public`'s scan
  across full git history — clean. Re-run it before publishing anything
  new that was written under "private repo, no one else will see this.")

## Where to look

| Need | Where |
|---|---|
| Full design: data flow, diagrams, resolved/still-open questions | `docs/internal/design.md` |
| Python reference implementation | `src/trailsign/settings.py` |
| Test suite | `tests/` (`conftest.py` has the shared fixture config) |
| Project status, what's built vs. not | `README.md` |
| How to write/extend design docs like `docs/internal/design.md` | the `writing-system-design-docs` skill (global, not repo-local) |

## Immediate next work

Not built yet, in rough order:
1. Resolve `docs/internal/design.md`'s remaining "Still open" items as they come up in practice, not speculatively (a non-instance-principal OCI auth shape, for consumers running outside an OCI compute instance, is the main one left)
2. Consider a port to a second language now that the Python package is solid, since the whole design's point is being language-independent, not just Python
