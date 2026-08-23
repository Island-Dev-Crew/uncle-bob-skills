# Review record - payments/refund story, seat: reviewer-2
# Convention (advisory, not checked): FOUND text starts with path:line;
# FALSIFIED text states the hypothesis, then how it was checked.
FOUND R1 refund.py:88 partial refund over the captured amount is accepted; no upper bound
FOUND R2 refund_test.py:14 test asserts only that the call returned, never the ledger row
FALSIFIED R3 suspected double-refund on retry - replayed the idempotency key, second call is a no-op
FALSIFIED R4 suspected currency rounding drift - amounts are integer minor units end to end
FALSIFIED R5 suspected the agent skipped the audit log - grep shows the write on every branch
