# Steering rules (imperative prose)

Three rules below wear a list marker. The other thirty-seven are the same
kind of rule written as bare imperative sentences: no marker, no table pipe,
no modal verb. The counter sees three.

- keep every module under two hundred lines.
- name booleans with an is or has prefix.
- run the formatter before every commit.

Use two-space indentation everywhere.
Snapshot tests are banned.
Mocks live in test/doubles.
Handlers return a Result, not an exception.
Config reads happen once, at boot.
The repository layer owns every SQL string.
Feature flags expire after one release.
Public types carry a doc comment.
Errors carry the request id.
Retries use jitter.
Timeouts are configured per call site.
The build runs offline.
Generated code lands in gen/.
Migrations ship in their own commit.
Secrets come from the environment.
Logs are structured JSON.
Metrics use the shared registry.
Background jobs are idempotent.
Queues drain oldest-first.
Caches expire in under an hour.
HTTP clients share one connection pool.
Tests run in random order.
Fixtures are built by factories.
Assertions name the behaviour under test.
Coverage gates at eighty percent.
Lint runs on the whole tree.
Formatting is checked in CI.
Dead code is deleted, not commented.
Branches rebase before merge.
Commits follow conventional prefixes.
Reviews take under a day.
Releases are tagged.
Rollbacks are one command.
Dashboards live beside the service.
Alerts page a human only for user-visible breakage.
Runbooks link from the alert.
Dependencies update weekly.
