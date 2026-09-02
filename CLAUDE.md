# CLAUDE.md

Guidance for Claude Code working in this repo. Kept short — detail
lives in `docs/design.md` and `README.md`, not here.

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
where this design started — see `docs/design.md`'s own "Origin" section
for why it moved here instead of staying bot-specific.

## Landmines

- **`trailsign-resolve:` is the only dispatch key — never rename it back
  to a bare `resolve`, and never let it collide with `type:` or any
  other field.** Two real bugs already happened this way (an overloaded
  `type:` field, then a plain `resolve:` that was still a generic
  collision risk) before landing here — see `docs/design.md`'s "Fixing
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
  factory, never this library's job — see `docs/design.md`'s "Two jobs,
  two owners" section. Don't add object-construction here even if it
  seems convenient for a first real consumer.
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
  refactoring this resolver; see `docs/design.md`'s correction note
  under "The converged design".
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
| Full design: data flow, diagrams, resolved/still-open questions | `docs/design.md` |
| Python reference implementation | `src/trailsign/settings.py` |
| Test suite | `tests/` (`conftest.py` has the shared fixture config) |
| Project status, what's built vs. not | `README.md` |
| How to write/extend design docs like `docs/design.md` | the `writing-system-design-docs` skill (global, not repo-local) |

## Immediate next work

Not built yet, in rough order:
1. Resolve `docs/design.md`'s remaining "Still open" items as they come up in practice, not speculatively (a non-instance-principal OCI auth shape, for consumers running outside an OCI compute instance, is the main one left)
2. Consider a port to a second language now that the Python package is solid, since the whole design's point is being language-independent, not just Python
