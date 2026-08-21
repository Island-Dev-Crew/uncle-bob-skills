# STORY: STORY-42
Feature: Panier de commande

  Scenario: Panier vide affiche l'état vide
    Given un panier contenant 0 article
    When l'acheteur ouvre la page du panier
    Then la page affiche "Votre panier est vide"
