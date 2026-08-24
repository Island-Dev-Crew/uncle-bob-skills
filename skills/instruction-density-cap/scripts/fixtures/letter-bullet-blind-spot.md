# Steering rules (markers outside the D-a class)

Forty rules, every one of them wearing a marker a human reads as a bullet or a
number: an Outlook `o`, a Word `x`, a lower-case roman numeral, a circled digit
pasted out of a document. None of those four shapes is in the class D-a
recognises, so the counter sees zero.

## Outlook bullets

o keep every module under two hundred lines
o name booleans with an is or has prefix
o run the formatter before every commit
o rebase before opening a pull request
o squash fixup commits
o write imperative commit subjects
o put snapshot tests behind a flag
o keep mocks in test/doubles
o return a Result from every handler
o read config once, at boot

## Word bullets

x let the repository layer own every SQL string
x expire feature flags after one release
x give public types a doc comment
x carry the request id on every error
x use jitter on retries
x cap the connection pool at sixteen
x log the correlation id first
x keep migrations reversible
x pin the toolchain in the lockfile
x review the generated diff before merging

## Roman numerals

ii. delete dead code in the same commit
iii. keep the public surface under twenty symbols
vi. name the decision each module hides
vii. budget one cross-module edge per change
viii. record the fixture that proved the bug
ix. measure before optimising
xi. keep the hot path allocation free
xii. prefer a table to a nested branch
xiii. fail closed on a missing secret
xiv. rotate credentials on every release

## Circled digits

① sign the release artefact
② attach the SBOM to the tag
③ keep the CI job under ten minutes
④ cache the dependency graph, not the build
⑤ run the linter in the same container
⑥ pin the base image by digest
⑦ keep the runbook next to the service
⑧ page on symptom, not on cause
⑨ write the postmortem within a week
⑩ close the incident with a test
