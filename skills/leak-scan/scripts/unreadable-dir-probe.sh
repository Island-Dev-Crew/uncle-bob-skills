#!/usr/bin/env bash
# unreadable-dir-probe.sh — a directory the scan cannot READ is a fault, not a
# clean tree.
#
# os.walk's default swallows every OSError and yields nothing for that subtree,
# so before the onerror hook a chmod-000 subdirectory holding the leaking pair
# turned a red run green in silence: the gate certified a tree it never read.
# A chmod-000 FILE already fail-closed; this probe is the directory twin.
#
#   bash scripts/unreadable-dir-probe.sh
#
# Exit 0 when the readable tree is red (1) and the unreadable one fail-closes
# (2), 1 when either verdict is wrong, 2 on a setup fault. The unreadable half
# is skipped, out loud, when the run is root — root reads a chmod-000 directory
# anyway, so the probe would prove nothing.
# A dead stdout must not become the verdict. `gate.sh … | head` closes the pipe early, the
# next write takes SIGPIPE, and the shell dies at 128+13 = 141 — a code this script's table
# does not name, arriving after the work was already done correctly. Handling the signal
# turns that into the usage/IO code 2, which is the one that means "no verdict here".
trap 'exit 2' PIPE
set -u

here=$(cd "$(dirname "$0")" && pwd) || exit 2
scan="$here/leak-scan.py"
tmp=$(mktemp -d) || exit 2
cleanup() { chmod 755 "$tmp/locked" 2>/dev/null; rm -rf "$tmp"; }
trap cleanup EXIT

mkdir "$tmp/locked" || exit 2
cat > "$tmp/webhook_contract.py" <<'EOF'
SIGNATURE_HEADER = "X-Idc-Signature"
MAX_CLOCK_SKEW_SECONDS = 300
EOF
cat > "$tmp/webhook_client.py" <<'EOF'
from webhook_contract import SIGNATURE_HEADER


def sign(digest):
    return {SIGNATURE_HEADER: digest}
EOF
cat > "$tmp/locked/legacy_client.py" <<'EOF'
LEGACY_SIGNATURE_HEADER = "X-Idc-Legacy-Signature"
LEGACY_SKEW = 900
EOF
cat > "$tmp/locked/legacy_server.py" <<'EOF'
HEADER = "X-Idc-Legacy-Signature"
SKEW = 900
EOF

fail=0

probe() {
  python3 "$scan" "$tmp" >/dev/null 2>&1
  rc=$?
  echo "$1 EXIT=$rc"
  [ "$rc" -eq "$2" ] || fail=1
}

# Readable: the pair inside locked/ restates two facts, so the scan is red.
probe "readable subtree" 1

if [ "$(id -u)" -eq 0 ]; then
  echo "SKIP unreadable subtree: running as root, which reads a chmod-000 directory anyway"
  exit "$fail"
fi

chmod 000 "$tmp/locked" || exit 2
# Unreadable: the same tree must FAIL-CLOSE, never report a clean 0.
probe "unreadable subtree" 2

exit "$fail"
