# Known-CLEAN ledger for fixtures/survivors.txt — the gate must exit 0.
# Every entry is complete; the point of this one is the argument that cites its
# sources. Two of its wrapped lines open with a URL and one opens with a bare
# 'note:', so a parser that treats any indented 'word:' as a field reads three
# fields nobody wrote and refuses the ledger as stating 'https:' twice. Only the
# four field names this island defines are fields; the rest is argument text.

M-src/pricing.ts-41-2  src/pricing.ts:41
  mutation:   `<` flipped to `<=` on the loop bound
  argument:   the loop body indexes items[i] with items.length as the bound, so the
              mutant's extra iteration throws before any observable output differs;
              https://example.invalid/pricing-spec#L41 fixes the bound and
              https://example.invalid/adr/0007 records why it cannot move, and the
              note: filed against both says the same in one line.
  excused-by: Claude Fable 5
  head:       4f2c1ab9d3e7c0b58a61d2f4e9c73b0a1d6e5f28

M-src/pricing.ts-58-1  src/pricing.ts:58
  mutation:   `+` swapped to `-` in the discount accumulator
  argument:   the accumulator is seeded at zero and the swapped operand is always
              zero on this branch, so the mutated program computes the same total.
  excused-by: Claude Fable 5
  head:       4f2c1ab9d3e7c0b58a61d2f4e9c73b0a1d6e5f28

M-src/cart.ts-12-3  src/cart.ts:12
  mutation:   `<` flipped to `<=` on the item-count guard
  argument:   the count is a non-negative integer the type system pins below the
              guard's constant, so no input reaches the boundary the mutant moves.
  excused-by: Claude Fable 5
  head:       4f2c1ab9d3e7c0b58a61d2f4e9c73b0a1d6e5f28
