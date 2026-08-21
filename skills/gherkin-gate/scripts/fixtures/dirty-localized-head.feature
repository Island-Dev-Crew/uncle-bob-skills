# language: de
# STORY: STORY-58
Funktionalitaet: Bezahlung

  Scenario: The English head is the one that got recorded
    Given a cart holding 1 item
    Then the total reads "5.00"

  Szenario: Der deutsche Kopf wurde nie ausgefuehrt
    Gegeben sei ein Warenkorb mit 1 Artikel
    Dann steht dort "5,00"
