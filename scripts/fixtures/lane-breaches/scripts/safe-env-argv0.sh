#!/usr/bin/env bash
# Exit: 0 always. Green controls: a missing utility after an argv0 value cannot
# execute the network-looking option value, and echo consumes curl as data.
env -a curl
env -acurl
env --argv0 curl
env --argv0=curl
env -a fake echo curl https://example.invalid
:
