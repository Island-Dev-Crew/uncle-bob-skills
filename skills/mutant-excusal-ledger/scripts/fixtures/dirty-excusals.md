# Known-DIRTY ledger for fixtures/survivors.txt — the gate must exit 1.
# One violation class per survivor:
#   missing entry: M-src/pricing.ts-41-2            -> UNEXCUSED
#   incomplete entry: M-src/pricing.ts-58-1         -> missing 'head'
#   thin argument: M-src/cart.ts-12-3               -> effort worn as equivalence

M-src/pricing.ts-58-1  src/pricing.ts:58
  mutation:   `+` swapped to `-` in the discount accumulator
  argument:   the accumulator is seeded at zero and the swapped operand is always
              zero on this branch, so the mutated program computes the same total.
  excused-by: Claude Fable 5

M-src/cart.ts-12-3  src/cart.ts:12
  mutation:   `<` flipped to `<=` on the item-count guard
  argument:   could not kill it
  excused-by: Claude Fable 5
  head:       4f2c1ab9d3e7c0b58a61d2f4e9c73b0a1d6e5f28
