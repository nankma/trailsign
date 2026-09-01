# CLAUDE.md

Guidance for Claude Code working in this repo. Kept short — detail
lives in `docs/design.md` and `README.md`, not here.

## Overview

Trailsign is a small, language-independent library for resolving
application settings from a declarative, self-describing config, where
each value declares its own source (a literal, an environment variable,
a vault secret, ...) instead of the caller assuming where to look.
**Python package built out as of 2026-09-01** — `src/trailsign/` is a
real installable package (`pyproject.toml`, src layout) with a test
suite (`tests/`). Not yet published to a package index. A port to a
second language is the remaining open work (see "Immediate next work").

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
- **This library never constructs consumer objects, only resolves values
  to plain data.** Turning a resolved config block into a live object
  (an adaptor, a client, anything) is always the *consumer's* own
  factory, never this library's job — see `docs/design.md`'s "Two jobs,
  two owners" section. Don't add object-construction here even if it
  seems convenient for a first real consumer.
- `_oci_config_from()` in `src/trailsign/settings.py` is a stub
  (`raise NotImplementedError`) — the OCI auth shape (config file vs.
  instance principal vs. explicit key) isn't decided yet.
- **`OracleKeyVaultResolver.resolve()` validates the node's own fields
  (`source`, `secret_ocid`) *before* `import oci`.** This was a real bug
  found while writing tests: `import oci` used to run first, so a
  missing `secret_ocid` raised `ModuleNotFoundError` instead of
  `SettingsError` whenever the `oci` package wasn't installed — breaking
  the "no oci dependency needed unless actually used" guarantee for the
  validation-error paths, not just the happy path. Keep the import after
  field validation if this method is touched again.

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
1. Resolve `docs/design.md`'s "Still open" items as they come up in practice, not speculatively (the OCI auth shape in particular — `_oci_config_from()` is still a stub)
2. Consider a port to a second language now that the Python package is solid, since the whole design's point is being language-independent, not just Python
