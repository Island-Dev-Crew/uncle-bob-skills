# Repo agent rules

You are the resident agent for this service. Read every rule below before you write code.

## Style

- Use two-space indentation everywhere.
- Prefer named exports over default exports.
- Keep functions under fifty lines.
- Do not introduce a new dependency without a note in the PR body.
- File names are kebab-case.
- Components are PascalCase.
- Hooks start with `use`.
- Constants are UPPER_SNAKE_CASE.
- Booleans read as `is`, `has`, `should`, or `can`.
- Comments explain why, never what.

## Testing

Every new module MUST ship a test file next to it.

- Unit tests cover the happy path and one failure path.
- Integration tests hit a real database in CI only.
- Snapshot tests are banned.
- Coverage never drops below eighty percent.
  - Nested exception: generated clients are exempt.
    - And their fixtures are exempt too.
- Mocks live in `test/doubles`.

## Git

You should rebase, not merge, before opening a PR.

- Commit subjects use the conventional-commit prefix.
- One logical change per commit.
- Never force-push a shared branch.
- Squash fixup commits before review.

> Quoted from the old handbook, still binding:
> - Tag releases with a signed annotated tag.
> - Always update the changelog in the same commit.

## Security

- Secrets come from the environment, never from source.
- Validate every request body at the boundary.
- Rate-limit each public endpoint.
- Error messages must not leak internal identifiers.

Avoid logging request headers in production.

## Running things

Example commands, not rules — the fence keeps them out of the count:

```bash
- npm run dev
- npm test -- --watch
- you must never edit dist/ by hand
- always run the linter first
```

## Performance

- Bundle budget is 150kb gzipped for the landing route.
- Images ship as AVIF with a WebP fallback.
- Animate transform and opacity only.
