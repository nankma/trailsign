---
name: writing-system-design-docs
description: Use when writing or updating a design doc for an in-progress, still-being-discussed architecture decision -- a new interface, abstraction, subsystem, or refactor plan that hasn't been built yet. Also applies when asked for a "system design doc", an RFC-style writeup, or any plan doc meant to be handed to a fresh session or a different implementation language.
---

# Writing System Design Docs

## Overview

A system design doc has one job a normal doc doesn't: let someone who
wasn't in the conversation — a teammate, a fresh AI session, or an
implementation in a different language — build the thing correctly
without re-deriving the reasoning or re-litigating settled questions.
That means the design has to survive being separated from both the
conversation that produced it and the language it'll eventually be
built in.

Not the same thing as: a retrospective "what we built and why" record
(an ADR, or a plans-history doc — written after the fact), or
how-to/reference documentation for something that already exists
(general wiki-page authoring). This is for a design that's still being
decided.

## When to use

- Proposing a new interface, abstraction, or subsystem that isn't built
  yet and is still under active discussion
- Explicitly asked for a "design doc," "system design doc," or an
  RFC-style writeup
- The doc needs to survive being handed to a different session or
  reimplemented in a different language than whatever's being discussed
  in chat
- A plan with multiple parts, where some parts will be designed now and
  others later, across more than one sitting

**Don't use for**: a finished feature's history (decided *and built*),
reference docs for using something that already exists, or a one-off
scratch note.

## Core pattern: design stays language-independent, code stays real and separate

The single most common failure mode is letting the design and one
language's implementation blur together. The fix is mechanical: **any
code fence containing actual syntax (a class definition, a method body,
language-specific type hints) does not belong in the design doc.** Move
it to a real source file and link to it. What stays in the doc is the
*contract*, expressed language-neutrally:

```
# ❌ Leaks implementation language into the design
class SettingsResolver(Protocol):
    def resolve(self, node: dict, settings: "Settings") -> str: ...

# ✅ Same contract, no language attached
Resolver interface: one method, `resolve(node, settings) -> value`.
Go: a one-method interface. Rust: a trait. Python: typing.Protocol.
The reference implementation is settings.py -- see resolve() there.
```

Data shapes follow the same rule — show them as plain literals
(`{type: api, url: "...", api-key: "<resolved>"}`), never as a
language's native dict/struct syntax. Diagrams need the same discipline:
a mermaid `classDiagram` stereotype should say `<<interface>>`, not
`<<Protocol>>` (that's Python-specific); method signatures should use
generic types (`value`, `map`) instead of `Any`/`dict`.

**Portability test, before calling a section done**: could a reader
implement this in a language not currently being discussed, using only
this doc? If understanding the *design* requires opening the linked code
file (not just seeing what one language's syntax looks like), an
implementation detail leaked into the design layer — pull it back out.

## Document skeleton

| Section | Purpose |
|---|---|
| Status line | One line: converged / still discussing / date of last decision. Living doc — edited in place, not re-created each round. |
| What exists today | Verified facts (grep/read the actual code), not recalled from memory. Say how you verified it. |
| The converged design | The design itself, language-independent (see Core pattern above) |
| Why, not just what | Alternatives considered and rejected, with the real reasoning — not only the final answer. A future reader needs to judge whether the reasoning still holds, not re-litigate from scratch |
| Data flow | Prose walkthrough of one concrete example end-to-end, paired with a diagram — see Diagrams below |
| Resolved questions | Numbered list: what was open, what it resolved to, when |
| Still open | Explicitly unresolved items, so nothing gets silently assumed decided |
| Link to code | A real, separate source file implementing the design — draft or final, clearly labeled which |

For a plan with multiple parts: one parent/overview doc holds the whole
rough plan and phasing; each part gets its own numbered child doc
(`01-`, `02-`, ...), written only once that part's turn actually comes
— not all speced up front. The parent links to each child; children
link back to the parent, never duplicate its content.

## Diagrams: two kinds, different jobs

- **Structural** (mermaid `classDiagram`): what are the pieces, how do
  they relate — interfaces, implementations, who constructs what. Use
  `<<interface>>`, not a language-specific stereotype.
- **Runtime flow** (mermaid `flowchart`): how data actually moves for
  one concrete case, start to finish — not a generic/abstract path.
  Trace a real example (a real config key, a real value) so a reader
  can follow one request all the way through, the same way the prose
  walkthrough does.

Both stay language-neutral: edge/node labels describe *what happens*
("read env var 'X'", "dispatch to resolver by type"), not one
language's method-call syntax.

## Writing it collaboratively

This kind of doc is normally built across a discussion, not written
once end-to-end: propose a concrete design with reasoning, the other
side confirms/redirects/adds a constraint, update the doc that same
round to reflect what just got settled. Mark newly-confirmed sections
with a date. When a decision gets reconsidered mid-discussion (a
proposal walked back or changed), keep the actual back-and-forth
reasoning in the doc — not just the final answer — because that's what
lets a future reader tell a considered rejection from an untested
assumption.

## Common mistakes

| Mistake | Why it breaks the doc's purpose | Fix |
|---|---|---|
| A full class/function body inlined as a code block in the design section | Ties the design to one language; unreadable as a spec by a different stack | Move to a real source file, link to it |
| Mermaid diagram uses a language-specific stereotype or type (`<<Protocol>>`, `Any`, `dict`) | Same problem, in diagram form | `<<interface>>`, generic `value`/`map` |
| Only the final decision is recorded, not what was considered and rejected | Next reader re-litigates a settled question, or can't tell if the reasoning still applies | Record the alternative and the actual reason it lost |
| One giant doc covers every part of a multi-part plan up front | Specs parts nobody's discussing yet; goes stale before its own turn arrives | Parent (rough, phased) + child docs, written one at a time |
| "What exists today" written from memory/assumption | A wrong baseline poisons every decision built on it | Grep/read the real code, say how you checked |
| No explicit "Still open" section | Undiscussed gaps read as silently decided | List them, even if the list is short |
