#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: BSD/macOS value-taking wrapper options
# do not turn the command that follows their values into data.
env -P /usr/bin curl https://example.invalid
xargs -J % curl https://example.invalid
xargs -R 1 curl https://example.invalid
xargs -S 4096 curl https://example.invalid
