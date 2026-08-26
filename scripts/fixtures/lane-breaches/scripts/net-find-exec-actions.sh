#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: find executes the command following
# -exec/-execdir through its literal semicolon or batch-plus terminator.
find . -maxdepth 0 -exec curl https://example.invalid {} \;
find . -maxdepth 0 -execdir /usr/bin/curl https://example.invalid {} +
find . -maxdepth 0 -exec env curl https://example.invalid {} \;
find . -maxdepth 0 -exec sh -c 'curl https://example.invalid' {} \;
find . -maxdepth 0 -execdir command curl https://example.invalid {} \;
find . -maxdepth 0 -ok curl https://example.invalid {} \;
find . -maxdepth 0 -okdir /usr/bin/curl https://example.invalid {} \;
