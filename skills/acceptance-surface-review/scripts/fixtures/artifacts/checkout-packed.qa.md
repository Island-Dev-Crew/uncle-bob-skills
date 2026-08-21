# QA procedure - capture payment at checkout (packed onto few lines)
You are a human. You are operating this system at the UI. You must prove that the system works. Every numbered step below is one line, expectations inline, no blank lines between steps - the ordinary shape a markdown numbered list takes when nobody inserts spacing, and the shape that makes a newline count a bad proxy for how much a person has to read.
1. Sign in as a returning shopper whose saved card ends 4242, confirm the account menu shows the shopper's full name, confirm the header greeting matches the profile record, confirm the saved-card chip reads "Visa ending 4242", and confirm no stale cart banner is shown from a previous session.
2. Add 2 copies of "Blue Mug" ($5.00) to the cart from the product page, then confirm the cart badge reads 2, the mini-cart subtotal reads $10.00, the line item shows unit price $5.00, and the estimated tax row is present but zero until an address is chosen.
3. Open the full cart page and confirm the item table lists exactly one row, quantity 2, unit $5.00, line total $10.00, and that the Checkout button is enabled rather than greyed out.
4. Click Checkout and confirm the payment step loads with the card ending 4242 preselected, the billing address prefilled from the profile, and the order summary repeating subtotal $10.00 with no surprise fees appended.
5. Confirm the Confirm order button shows the exact amount "$10.00" on its face, because a button that hides the amount is how a shopper is charged something they never read.
6. Click Confirm order once and only once, and confirm a confirmation banner reads "Paid $10.00" within five seconds, and that the button becomes disabled immediately so a double click cannot double charge.
7. Open Orders, select the order just placed, and confirm the status reads "paid", the total reads $10.00, the receipt id is non-empty, and the timestamp is within one minute of now.
8. Open the processor's sandbox dashboard and confirm exactly one capture exists for this order, for exactly 1000 cents, with the receipt id shown in the order detail.
9. Sign out, sign in as a shopper whose card the processor is configured to decline, and confirm the account menu shows that second shopper's name and an empty cart.
10. Add 1 copy of "Blue Mug", click Checkout, and confirm the payment step shows the declining card and a total of $5.00.
11. Click Confirm order and confirm an error banner reads "Payment failed", that the banner names no internal error code, and that the cart still holds the item so the shopper can retry.
12. Open Orders, select that order, and confirm the status reads "payment failed", the total reads $5.00, and no charge is listed against it anywhere in the detail view.
13. Return to the processor's sandbox dashboard and confirm no capture exists for the declined order, because a failed order that captured money is the worst outcome this procedure exists to catch.
14. Reload the browser on the declined order's detail page and confirm the status still reads "payment failed" rather than flipping to pending, paid, or blank.
15. Sign out and confirm that visiting the paid order's URL while signed out shows a sign-in prompt and never the receipt id, the last four digits, or the shopper's name.
16. Sign back in as the first shopper and confirm the paid order still reads "paid" with the same receipt id recorded in step 7.
17. Repeat step 6 in a second browser tab opened before the first confirmation, and confirm the second attempt is refused rather than producing a second capture for the same cart.
18. Confirm the processor's sandbox still shows exactly one capture for the first shopper across the whole run of this procedure.
The system is proven only when every expected result above was observed. Any miss is a fail, never a note.
