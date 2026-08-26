#!/usr/bin/env bash
# Exit: 0 always. Green controls: a here-document is not shell code when the
# pipeline does not reach a stdin-reading shell or transforms it first.
cat <<'NOT_A_PROGRAM' | printf '%s\n'
curl https://example.invalid
NOT_A_PROGRAM

sed 's/curl/echo/' <<'TRANSFORMED' | bash
curl https://example.invalid
TRANSFORMED

cat /dev/null <<'CAT_FILE' | bash
curl https://example.invalid
CAT_FILE

tee --not-a-real-option <<'INVALID_TEE' | bash
curl https://example.invalid
INVALID_TEE

tee /dev/null --not-a-real-option <<'TRAILING_INVALID_TEE' | bash
curl https://example.invalid
TRAILING_INVALID_TEE
:
