Feature: Capture payment at checkout

  Scenario: Card is charged once for a two-item cart
    Given a cart holding 2 items at $5.00 each
    And a valid card ending 4242
    When the shopper confirms the order
    Then the card is charged exactly $10.00
    And the order status reads "paid"

  Scenario: Declined card leaves the order unpaid
    Given a cart holding 1 item at $5.00
    And a card that the processor declines
    When the shopper confirms the order
    Then no charge is recorded
    And the order status reads "payment failed"
