#!/usr/bin/env bash
# Exit: 0 always. Exec resolves an external utility; builtin-only names fail as
# executable positions and their later curl-shaped words remain data.
exec builtin command curl https://example.invalid
exec eval 'curl https://example.invalid'
exec source /dev/stdin <<'EXEC_SOURCE_DATA'
curl https://example.invalid
EXEC_SOURCE_DATA
