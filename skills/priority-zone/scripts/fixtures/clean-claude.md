# CLAUDE.md — payments-api

You are the maintainer agent for this Go payments service.
Work arrives as bug reports and small feature slices; done means the
change ships behind the existing gates with no new public surface.

Constraints that shape generation:
- Handlers stay thin: parse, delegate to a use case, map the result.
- Money is an integer minor-unit type; NEVER a float.
- Every external call MUST carry the request context and a timeout.
- New packages live under internal/ unless an outside caller needs them.

Reference, on demand: docs/architecture.md, docs/testing.md.
Gates run after generation: make lint, make test, make crap.
