#!/usr/bin/env bash
# Exit: 0 always. Wrapper option values remain data even when they happen to
# spell a network-client name; the literal command after them is non-networked.
env -P curl printf '%s\n' safe
xargs -J curl printf '%s\n' safe
xargs -R curl printf '%s\n' safe
xargs -S curl printf '%s\n' safe
xargs -E '' printf '%s\n' safe
