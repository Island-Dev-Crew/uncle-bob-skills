#!/usr/bin/env bash
# Fixture gate. Exits 1 on "dirty" and emits one deliberately output-shaped line otherwise.
trap 'exit 2' PIPE
set -u
[ "${1:-}" = "dirty" ] && exit 1
printf '%s\n' '| PASS nothing dirty'
exit 0
