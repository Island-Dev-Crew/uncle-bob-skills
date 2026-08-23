# Repo agent rules

You are the resident agent for this service. Everything checkable moved to a gate;
what stands here is what has to shape the code as it is written.

## The constraints that shape generation

- Layering: `domain` never imports `adapters` — invert or insert an interface instead.
- Errors are values at the boundary, exceptions only for programmer mistakes.
- Prefer one deep module over three shallow ones at a seam.
- Write the interface comment before the implementation.

## What runs after you, not in your head

The gates below decide; they are not repeated as rules here.

```bash
npm run lint && npm run typecheck   # style, naming, imports, file size
npm test -- --coverage              # coverage floor, snapshot ban
npm run gate:deps                   # layering fence
npm run gate:secrets                # secret scan
```

## Reference

Long-form conventions live in `docs/conventions.md`; open it when a gate flags you.
