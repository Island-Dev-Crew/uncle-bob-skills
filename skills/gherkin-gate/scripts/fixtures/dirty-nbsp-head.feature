# STORY: STORY-91
Feature: Password reset

  Scenario: A known address receives a reset link
    Given a registered address
    When the shopper requests a reset
    Then a reset link is sent

  Scenario: An unknown address reveals nothing
    Given an unregistered address
    When the shopper requests a reset
    Then the page reads "Check your inbox"
