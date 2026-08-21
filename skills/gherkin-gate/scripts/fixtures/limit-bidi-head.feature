# STORY: STORY-46
Feature: Wishlist

  Scenario: An item is added to the wishlist
    Given a signed-in shopper
    When they add an item to the wishlist
    Then the wishlist holds that item

‪Scenario: NEVER RECORDED AND NEVER SEEN
    Given a signed-in shopper
    When they remove an item
    Then the wishlist no longer holds it
