#!/usr/bin/env bash
# Exit: 0 always. Green controls: command-looking words in here-doc data,
# arrays, arithmetic, script arguments, and quoted semicolon data do not run.
cat <<'SAFE_DATA'
curl https://example.invalid
rm -rf .
SAFE_DATA

commands=(curl wget "rm -rf .")
value=$((curl + 1))
((curl += 1))
bash safe-script.sh -c curl
printf '%s\n' 'safe; curl' 'rm -rf .; wget'

case "$kind" in
  curl) printf '%s\n' 'pattern data' ;;
  wget) printf '%s\n' 'more pattern data' ;;
esac
for tool in curl wget; do
  printf '%s\n' "$tool"
done
curl() { printf '%s\n' 'function name, not a network invocation'; }
