# STORY: STORY-42
Feature: Cart checkout totals

  Scenario: Empty cart shows the empty state
    Given a cart holding 0 items
    When the shopper opens the cart page
    Then the page reads "Your cart is empty"

  Scenario: Two items at $5.00 total $10.00
    Given a cart holding 2 items at $5.00 each
    When the shopper opens the cart page
    Then the order total reads "$10.00"

  Scenario: Removing the last item empties the cart
    Given a cart holding 1 item at $5.00
    When the shopper removes that item
    Then the page reads "Your cart is empty"
