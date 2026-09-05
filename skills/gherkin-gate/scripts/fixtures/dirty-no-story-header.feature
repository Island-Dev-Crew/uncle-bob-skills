Feature: Order history

  Scenario: A placed order appears in the history
    Given a shopper with one placed order
    When they open order history
    Then that order is listed
