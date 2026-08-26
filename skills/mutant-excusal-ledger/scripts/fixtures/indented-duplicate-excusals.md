# Known-INDENTED-DUPLICATE ledger for fixtures/survivors.txt — the gate must exit 2.
# The same split as duplicate-excusals.md, with one space in front of the second
# M-src/pricing.ts-41-2 header. That single space is the whole fixture: a gate that
# decides what a header is by the column it sits in reads the indented one as more
# argument text, drops the two fields underneath it into the block above, and reports
# one complete excusal and a GREEN gate. A reader still sees two blocks, one of them
# missing an argument. The header is recognised by the id it carries instead, so the
# space changes nothing.

M-src/pricing.ts-41-2  src/pricing.ts:41
  mutation:   `<` flipped to `<=` on the loop bound
  argument:   the loop body indexes items[i] with items.length as the bound, so the
              mutant's extra iteration throws before any observable output differs
              and the mutated program computes the same function.

 M-src/pricing.ts-41-2  src/pricing.ts:41
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
