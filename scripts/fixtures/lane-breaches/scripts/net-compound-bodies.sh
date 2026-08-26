#!/usr/bin/env bash
# Exit: 0 always. Deliberate L1 breaches in executable compound-statement
# bodies; only the case patterns, loop word list, and function name are inert.
case "$kind" in
  safe) curl https://example.invalid ;;
esac
for tool in safe; do
  wget https://example.invalid
done
helper() { nc example.invalid 80; }
