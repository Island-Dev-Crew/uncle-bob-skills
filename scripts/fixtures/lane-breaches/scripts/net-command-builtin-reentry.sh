#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: macOS's external command utility
# re-enters shell builtin semantics before dispatching its remaining argv.
/usr/bin/command eval 'curl https://example.invalid'
/usr/bin/command builtin command curl https://example.invalid
