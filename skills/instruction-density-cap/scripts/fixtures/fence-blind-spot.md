# Fence blind spot — a captured limit, not a passing grade

This fixture documents a hole this island chose not to close. Fenced code blocks are
excluded from the count so that example commands do not inflate it; the price is that
a rules list moved inside a fence goes uncounted. Counted units outside the fence: 4 —
the three rules plus this paragraph, which carries a modal. The proxy is literal.

- Layering: `domain` never imports `adapters`.
- Errors are values at the boundary.
- Write the interface comment first.

```text
- Use two-space indentation everywhere.
- Prefer named exports over default exports.
- Keep functions under fifty lines.
- File names are kebab-case.
- Components are PascalCase.
- Hooks start with `use`.
- Constants are UPPER_SNAKE_CASE.
- Comments explain why, never what.
- Every new module ships a test file next to it.
- Unit tests cover the happy path and one failure path.
- Snapshot tests are banned.
- Coverage never drops below eighty percent.
- Mocks live in `test/doubles`.
- Commit subjects use the conventional-commit prefix.
- One logical change per commit.
- Never force-push a shared branch.
- Squash fixup commits before review.
- Secrets come from the environment, never from source.
- Validate every request body at the boundary.
- Rate-limit each public endpoint.
```

Twenty directives sit above, inside the fence, and the gate consents at a cap of 5.
A reviewer who reads the file sees them; the counter does not. That is the boundary,
captured rather than claimed.
