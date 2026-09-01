# CLAUDE.md

Guidance for Claude Code working in this repo. Kept short — detail
lives in `docs/design.md` and `README.md`, not here.

## Overview

Trailsign is a small, language-independent library for resolving
application settings from a declarative, self-describing config, where
each value declares its own source (a literal, an environment variable,
a vault secret, ...) instead of the caller assuming where to look.
**Design-only as of 2026-09-01** — `settings.py` is a draft Python
reference implementation: no tests, no package structure, not
published. Turning this into a real, general-purpose library is the
open work.

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
- `_oci_config_from()` in `settings.py` is a stub
  (`raise NotImplementedError`) — the OCI auth shape (config file vs.
  instance principal vs. explicit key) isn't decided yet.

## Where to look

| Need | Where |
|---|---|
| Full design: data flow, diagrams, resolved/still-open questions | `docs/design.md` |
| Python reference implementation | `settings.py` |
| Project status, what's built vs. not | `README.md` |
| How to write/extend design docs like `docs/design.md` | the `writing-system-design-docs` skill (global, not repo-local) |

## Immediate next work

Not built yet, in rough order:
1. Real package structure (`pyproject.toml`, proper layout — `settings.py` is one flat file today)
2. A test suite (none exists yet)
3. Resolve `docs/design.md`'s "Still open" items as they come up in practice, not speculatively
4. Consider a port to a second language once the Python implementation is solid, since the whole design's point is being language-independent, not just Python
