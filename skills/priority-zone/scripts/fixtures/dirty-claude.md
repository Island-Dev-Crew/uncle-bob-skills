# CLAUDE.md — payments-api

You are the maintainer agent for this Go payments service.
Work arrives as bug reports and small feature slices; done means the
change ships behind the existing gates with no new public surface.

Constraints that shape generation:
- Handlers stay thin: parse, delegate to a use case, map the result.
- Money is an integer minor-unit type; never a float.
- New packages live under internal/ unless an outside caller needs them.

Background: this service was split out of the monolith in 2023 and still
carries two legacy adapters, which the team retires once the billing
migration lands; the migration doc holds the current status and owners.
The team prefers small pull requests and squash merges, and the release
train leaves on Tuesdays unless the on-call engineer holds it back.

Housekeeping notes:
- Run gofmt before committing, and keep imports grouped stdlib first.
- Update the changelog whenever observable behaviour changes.
- Every external call MUST carry the request context and a timeout.
- ALWAYS rotate the sandbox key after a load test.
- Test fixtures live under testdata/ and regenerate via make golden.
