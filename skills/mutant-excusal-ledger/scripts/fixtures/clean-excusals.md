# Known-CLEAN ledger for fixtures/survivors.txt — the gate must exit 0.
# Every survivor carries mutation, argument, excused-by, head; every argument
# claims equivalence about the program, not effort by the author.

M-src/pricing.ts-41-2  src/pricing.ts:41
  mutation:   `<` flipped to `<=` on the loop bound
  argument:   the loop body indexes items[i] with items.length as the bound, so the
              mutant's extra iteration throws before any observable output differs
              and the mutated program computes the same function.
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
