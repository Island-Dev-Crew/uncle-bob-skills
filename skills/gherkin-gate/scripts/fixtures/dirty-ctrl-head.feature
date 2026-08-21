# STORY: STORY-24
Feature: Address book

  Scenario: A new address is saved
    Given a signed-in shopper
    When they add an address
    Then it appears in the address book

  Scenario: A duplicate address is not saved twice
    Given an address already saved
    When they add the same address
    Then the address book still holds one copy
