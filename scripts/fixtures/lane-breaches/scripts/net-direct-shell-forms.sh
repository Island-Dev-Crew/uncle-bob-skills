#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches hidden behind shell constructs that
# still execute the named command.
command curl https://example.invalid
command curl -v https://example.invalid
env -S '/usr/bin/curl -s https://example.invalid'
env -S '-u TOKEN /usr/bin/curl -s https://example.invalid'
env -S '-i /usr/bin/curl -s https://example.invalid'
env -S '-- /usr/bin/curl -s https://example.invalid'
exec -a harmless /usr/bin/curl https://example.invalid
echo "$(wget https://example.invalid)"
cat <(nc example.invalid 80)
echo `curl https://example.invalid`
echo `echo \`curl https://example.invalid\``
