Feature: sign in
  Scenario: a known user signs in
    Given a registered user
    When they submit valid credentials
    Then they land on the dashboard
