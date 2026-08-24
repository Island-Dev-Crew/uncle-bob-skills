# CLAUDE.md — payments-api

You are the maintainer agent for this Go payments service.
Work arrives as bug reports and small feature slices; done means the
change ships behind the existing gates with no new public surface.

Constraints that shape generation:
- Handlers stay thin: parse, delegate to a use case, map the result.
- Money is an integer minor-unit type; never a float.

Housekeeping, pasted from the team wiki (the fence was never closed):

```bash
make lint
- Every external call MUST carry the request context and a timeout.
- ALWAYS rotate the sandbox key after a load test.
