# STORY: STORY-13
Feature: Gift card redemption

  Scenario: A valid card is redeemed once
    Given a gift card with balance
    When the shopper redeems it
    Then the balance is applied

﻿Scenario: A spent card is rejected
    Given a gift card with no balance
    When the shopper redeems it
    Then the page reads "This card is spent"
