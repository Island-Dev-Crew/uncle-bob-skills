# STORY: STORY-77
Feature: Refund a delivered order

  Scenario: A refund inside the window is approved
    Given an order delivered 3 days ago
    When the shopper requests a refund
    Then the refund is approved

  Example: A refund outside the window is declined
    Given an order delivered 45 days ago
    When the shopper requests a refund
    Then the refund is declined
