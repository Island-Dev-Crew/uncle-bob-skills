Feature: Cart checkout total

  Scenario: A cart of two identical items shows the correct total
    Given a cart holding 2 items at $5.00 each
    When the shopper opens the checkout page
    Then the order total reads $10.00
