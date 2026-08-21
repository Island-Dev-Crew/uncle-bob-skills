# reviewed by the specifier seat
﻿# language: de
# STORY: STORY-35
Funktionalitaet: Warenkorb

  Scenario: An empty cart shows the empty state
    Given an empty cart
    When the shopper opens it
    Then the page reads "Your cart is empty"

  Szenario: Ein Artikel erscheint im Warenkorb
    Gegeben sei ein leerer Warenkorb
    Wenn ein Artikel gelegt wird
    Dann zeigt die Seite den Artikel
