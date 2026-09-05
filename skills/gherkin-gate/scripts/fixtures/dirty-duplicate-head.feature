# STORY: STORY-31
Feature: Gift wrapping

  Scenario: Gift wrap adds $2.00 to the total
    Given a cart totalling $10.00
    When the shopper selects gift wrap
    Then the total reads "$12.00"

  Scenario: Gift wrap adds $2.00 to the total
    Given a cart totalling $30.00
    When the shopper selects gift wrap
    Then the total reads "$32.00"
