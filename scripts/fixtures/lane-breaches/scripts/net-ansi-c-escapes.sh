#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches: ANSI-C escapes still form literal
# executable names, and an escaped quote keeps a following hash inside data.
$'cur\x6c' https://example.invalid
$'cur\154' https://example.invalid
printf '%s\n' $'\' #'; curl https://example.invalid
