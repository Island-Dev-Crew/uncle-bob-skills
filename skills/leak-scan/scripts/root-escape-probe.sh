#!/usr/bin/env bash
# root-escape-probe.sh — a scan reads what the CALLER named, not what a link
# names.
#
# A symlink inside a scanned tree can point anywhere on the machine: a sibling
# checkout, a home directory, /etc. Following one made this scanner open files
# outside the root it was pointed at and PRINT their path:line into the report —
# path authority taken from a link rather than from the caller. Documenting the
# behaviour is not the same as being authorized to take it.
#
# So an entry whose canonical target escapes every authorized root is refused BY
# NAME and fail-closes (exit 2). It is not pruned in silence: a silently skipped
# subtree is exactly the false green os.walk's followlinks default already
# produced, which symlinked-dir-probe.sh captures. --allow-root is the
# deliberate expansion, and the third probe proves it still finds the leak.
#
#   bash scripts/root-escape-probe.sh
#
# Exit 0 when the escaping directory link and the escaping file link are both
# refused (2) and the authorized run still reports the leak (1), 1 when any
# verdict is wrong, 2 on a setup fault. Skipped, out loud, where symlinks
# cannot be made.
# A dead stdout must not become the verdict. `gate.sh … | head` closes the pipe early, the
# next write takes SIGPIPE, and the shell dies at 128+13 = 141 — a code this script's table
# does not name, arriving after the work was already done correctly. Handling the signal
# turns that into the usage/IO code 2, which is the one that means "no verdict here".
trap 'exit 2' PIPE
set -u

here=$(cd "$(dirname "$0")" && pwd) || exit 2
scan="$here/leak-scan.py"
tmp=$(mktemp -d) || exit 2
trap 'rm -rf "$tmp"' EXIT

# The counterpart module is OUTSIDE the scanned root. Nothing but a link reaches
# it, and the caller never named it.
mkdir -p "$tmp/outside" "$tmp/repo" || exit 2
cat > "$tmp/outside/webhook_contract.py" <<'EOF'
SIGNATURE_HEADER = "X-Idc-Signature"
MAX_CLOCK_SKEW_SECONDS = 300
EOF
cat > "$tmp/repo/webhook_client.py" <<'EOF'
SIGNATURE_HEADER = "X-Idc-Signature"
MAX_CLOCK_SKEW_SECONDS = 300
EOF
# A second in-root module so the run has >= 2 comparable files on its own and
# reaches a VERDICT rather than fail-closing on the two-file floor.
cat > "$tmp/repo/alpha.py" <<'EOF'
ALPHA_ONLY_FACT = "alpha-only-fact"
EOF

if ! ln -s ../outside "$tmp/repo/shared" 2>/dev/null; then
  echo "SKIP root escape: this filesystem cannot create symlinks"
  exit 0
fi

fail=0

probe() {
  label=$1; want=$2; shift 2
  python3 "$scan" "$@" >/dev/null 2>&1
  rc=$?
  echo "$label EXIT=$rc"
  [ "$rc" -eq "$want" ] || fail=1
}

# It used to exit 1 here, having read and printed lines from $tmp/outside.
probe "escaping dir link " 2 "$tmp/repo"
probe "authorized target " 1 --allow-root "$tmp/outside" "$tmp/repo"

# A linked FILE escapes the same way and is refused the same way.
rm "$tmp/repo/shared" || exit 2
ln -s ../outside/webhook_contract.py "$tmp/repo/webhook_contract.py" || exit 2
probe "escaping file link" 2 "$tmp/repo"

if [ "$fail" -eq 0 ]; then
  echo "PASS — the escape was refused by name, and --allow-root still scanned it"
else
  echo "FAIL — a link took path authority the caller never gave"
fi
exit "$fail"
