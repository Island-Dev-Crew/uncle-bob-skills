#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: GNU env's argv0 option consumes its
# value before selecting the following utility.
env -a fake curl https://example.invalid
env -afake /usr/bin/curl https://example.invalid
env --argv0 fake curl https://example.invalid
env --argv0=fake /usr/bin/curl https://example.invalid
env -S '-a\_fake\_curl\_https://example.invalid'
