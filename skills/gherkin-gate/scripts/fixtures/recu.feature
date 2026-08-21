# STORY: STORY-70
Feature: Recu de paiement

  Scenario: Le reçu affiche le montant payé
    Given un paiement accepte
    Then le recu affiche le montant
