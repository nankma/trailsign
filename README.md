# Trailsign

A small, language-independent library for resolving application
settings from a declarative, self-describing config — where each value
states its own source (a literal, an environment variable, a vault
secret, ...) instead of the calling code assuming where to look.

```yaml
api-key:
  trailsign-resolve: environment-variable
  name: GNEWS_API_KEY
```

`trailsign-resolve:` is a reserved, namespaced key — deliberately not a
bare word like `resolve` — so it can never collide with a consuming
project's own field names. It dispatches to a pluggable resolver;
whatever it resolves to is handed to the consumer as a plain value, with
no trace of where it came from left in the shape.

## Status

**Design-only, as of 2026-09-01.** `settings.py` is a draft Python
reference implementation — not tested, not packaged, not published. This
is meant to be picked up by a dedicated work session next, to turn it
into a real general-purpose library: a proper package layout, a test
suite, and likely a port to at least one other language, since the
design's whole point is being language-independent, not just Python.

## Start here

- [`docs/design.md`](docs/design.md) — the core design: the config
  shape, the resolve/dispatch contract (holds equally for a Go
  `interface`, a Rust `trait`, or a Python `typing.Protocol`), why it's
  shaped this way, two worked examples with diagrams, and what's still
  undecided.
- [`settings.py`](settings.py) — the Python reference implementation,
  matching `docs/design.md` exactly.
- [`.claude/skills/writing-system-design-docs/`](.claude/skills/writing-system-design-docs/SKILL.md)
  — the doc-writing convention `docs/design.md` follows, carried over
  from where this project started in case future design docs here want
  the same discipline (language-independent contracts, diagrams, a
  "still open" section that's actually kept honest).

## Origin

This design started inside a Telegram news-trend bot (Auguring, formerly
Argus) while building a settings abstraction so that bot could run
standalone as well as on its current cloud deployment. The design turned
out to be genuinely content-independent — nothing in it assumes anything
bot-specific — so it's being extracted into its own project rather than
staying bot-only. `docs/design.md`'s own "Origin" section has the
originating project's actual settings inventory, kept for context on why
the design has the shape it has.

## The split that makes this portable

Two jobs, two owners, and only one of them is this library's job:

1. **Resolving a marked value to a plain value** — Trailsign's job, and
   only Trailsign's job. Nothing here knows or cares what the resolved
   value is *for*.
2. **Turning a resolved config block into a live object** — never
   Trailsign's job. Each consumer owns its own small factory (a plain
   name→constructor map) that builds whatever it needs from the
   already-resolved values this library hands it.

Full reasoning for the split, plus two complete worked examples (a news
source's API key from an environment variable, a telemetry backend's
credential from a vault) with diagrams, is in `docs/design.md`.

## What's not decided yet

See `docs/design.md`'s own "Still open" section — carried over from
where this design started, still accurate as of 2026-09-01:

- Package structure (this is one flat file today, not an installable
  library)
- Exact auth-config shape for vault-backed resolvers
- Validation-timing default (eager vs. lazy)
