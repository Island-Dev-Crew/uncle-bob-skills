# STORY: STORY-27
Feature: Coupon codes

  Scenario: A valid code reduces the total
    Given a cart totalling $20.00
    When the shopper applies code SAVE5
    Then the total reads "$15.00"

  Scenario:
    Given a cart totalling $20.00
    When the shopper applies code NOPE
    Then the total still reads "$20.00"
