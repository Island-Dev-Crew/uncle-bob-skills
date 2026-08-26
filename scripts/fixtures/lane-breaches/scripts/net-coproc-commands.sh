#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1/L2 breaches through unnamed simple coprocesses
# and unnamed/named compound coprocess bodies.
coproc curl https://example.invalid
coproc /usr/bin/curl https://example.invalid
coproc env curl https://example.invalid
coproc eval 'curl https://example.invalid'
coproc { curl https://example.invalid; }
coproc FETCH { curl https://example.invalid; }
