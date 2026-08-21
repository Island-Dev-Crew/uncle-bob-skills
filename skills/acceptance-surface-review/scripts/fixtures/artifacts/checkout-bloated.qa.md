# QA procedure - capture payment at checkout (revision 4, expanded)

## Purpose and scope of this document

This procedure exists to establish, beyond reasonable doubt, that the
checkout capture path behaves correctly under both the approved and the
declined branch, and to serve as the source for the executable QA script.

## Preconditions and environment notes

The staging environment must be seeded with the standard catalogue, the
processor sandbox must be reachable, and the feature flag capture_v2
must be enabled for the test tenant before any step below is attempted.

You are a human. You are operating this system at the UI. You must prove
that the system works.

## Steps

1. Sign in as a returning shopper with a saved card ending 4242.
   Expected: the account menu shows the shopper's name.
2. Add 2 copies of "Blue Mug" ($5.00) to the cart.
   Expected: the cart badge reads 2 and the subtotal reads $10.00.
3. Open the cart and click Checkout.
   Expected: the payment step shows the card ending 4242.
4. Click Confirm order.
   Expected: a confirmation banner reads "Paid $10.00".
5. Open Orders and select the order just placed.
   Expected: the order status reads "paid" and the total reads $10.00.

The system is proven only when every expected result above was observed.
