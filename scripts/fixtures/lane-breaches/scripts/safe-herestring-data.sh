#!/usr/bin/env bash
# Exit: 0 always. A here-string passed to an ordinary command, or shell text
# that only prints a client name as data, does not invoke the network client.
cat <<< 'curl https://example.invalid'
bash <<< 'printf "%s\n" curl'

# A genuinely different later input source overrides the curl-bearing here-string.
bash <<< 'curl https://example.invalid' </dev/null

# An unconsumed nonzero descriptor is data, not Bash's program input.
bash 3<<< 'curl https://example.invalid' </dev/null
