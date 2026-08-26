#!/usr/bin/env bash
# Exit: 0 always. Green controls for BSD env -S quoting, escaping, comments,
# truncation, invalid escapes, and an empty executable position.
env -S '"curl\_https://example.invalid"'
env -S "'curl\_https://example.invalid'"
env -S 'curl\\_https://example.invalid'
env -S 'curl\ https://example.invalid'
env -S 'curl\thttps://example.invalid'
env -S 'curl\nhttps://example.invalid'
env -S '\#curl\_https://example.invalid'
env -S 'printf\c\_curl\_https://example.invalid'
env -S '#\_curl\_https://example.invalid'
env -S 'printf\q\_curl\_https://example.invalid'
env -S "''\_curl\_https://example.invalid"
:
