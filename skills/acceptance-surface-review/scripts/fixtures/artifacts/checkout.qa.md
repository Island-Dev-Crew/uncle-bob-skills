# QA procedure - capture payment at checkout

You are a human. You are operating this system at the UI. You must prove
that the system works.

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
6. Sign in as a shopper whose card the processor declines.
   Expected: the account menu shows that shopper's name.
7. Add 1 copy of "Blue Mug" and click Confirm order.
   Expected: an error banner reads "Payment failed".
8. Open Orders and select that order.
   Expected: the status reads "payment failed" and no charge is listed.

The system is proven only when every expected result above was observed.
Any miss is a fail, never a note.
