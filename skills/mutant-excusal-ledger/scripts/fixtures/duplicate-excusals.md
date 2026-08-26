# Known-DUPLICATE ledger for fixtures/survivors.txt — the gate must exit 2.
# M-src/pricing.ts-41-2 appears TWICE, with the four required fields split
# across the two blocks: mutation+argument in the first, excused-by+head in
# the second. Merging them by id manufactures one complete-looking excusal out
# of two incomplete ones. Two blocks claiming the same mutant is a ledger no
# human can read the same way twice, so it is malformed input, not a verdict.

M-src/pricing.ts-41-2  src/pricing.ts:41
  mutation:   `<` flipped to `<=` on the loop bound
  argument:   the loop body indexes items[i] with items.length as the bound, so the
              mutant's extra iteration throws before any observable output differs
              and the mutated program computes the same function.

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

M-src/pricing.ts-41-2  src/pricing.ts:41
  excused-by: Claude Fable 5
  head:       4f2c1ab9d3e7c0b58a61d2f4e9c73b0a1d6e5f28
