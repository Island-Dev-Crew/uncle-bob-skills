#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: an empty value for xargs -E remains
# that option's argument; it does not consume the network command that follows.
xargs -E '' curl https://example.invalid
xargs -E '' /usr/bin/curl https://example.invalid
