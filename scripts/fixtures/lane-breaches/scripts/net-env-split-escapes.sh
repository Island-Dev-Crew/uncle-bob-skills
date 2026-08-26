#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: BSD env -S treats an unquoted \_
# escape as an argument separator before it selects the utility to execute.
env -S 'curl\_https://example.invalid'
env -S '-u\_TOKEN\_/usr/bin/curl\_https://example.invalid'
env -S '--\_/usr/bin/curl\_https://example.invalid'
env '-Scurl\_https://example.invalid'
env -S '"curl"\_https://example.invalid'
