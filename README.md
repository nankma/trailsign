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

**Python package built out, as of 2026-09-01.** `src/trailsign/` is a
real installable package (`pyproject.toml`, src layout) with a test
suite covering the resolve walk, the three built-in resolvers
(`OracleKeyVaultResolver` verified against a real OCI Vault secret —
see `tools/verify_oracle_vault.py`), `validate()`'s combined-error
behavior, and the `trailsign-resolve` vs. `type` non-collision
regression. MIT licensed (see `LICENSE`). Public on GitHub; CI runs the
test suite on every push/PR. Not yet published to PyPI. A port to at
least one other language is still open, since the design's whole point
is being language-independent, not just Python.

### Installing it

Not on PyPI yet — until then, install straight from GitHub, ideally
pinned to a tag once one exists:

```
pip install git+https://github.com/nankma/trailsign.git@main
```

Install for development on this repo: `pip install -e ".[test]"`, then
`pytest`.

## Start here

- [`docs/design.md`](docs/design.md) — the core design: the config
  shape, the resolve/dispatch contract (holds equally for a Go
  `interface`, a Rust `trait`, or a Python `typing.Protocol`), why it's
  shaped this way, two worked examples with diagrams, and what's still
  undecided.
- [`src/trailsign/settings.py`](src/trailsign/settings.py) — the Python
  reference implementation, matching `docs/design.md` exactly.
- [`tests/`](tests/) — the test suite; `tests/conftest.py` has a shared
  fixture config mirroring `docs/design.md`'s worked examples.
- the `writing-system-design-docs` skill (global, not repo-local) — the
  doc-writing convention `docs/design.md` follows, carried over
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

See `docs/design.md`'s own "Still open" section for full detail:

- A non-instance-principal auth shape for `oracleKeyVault` (today it only
  works from inside an OCI compute instance)
- Validation-timing default (eager vs. lazy)
- A port to a second language
