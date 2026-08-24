#!/usr/bin/env bash
# symlinked-dir-probe.sh — a subdirectory reached through a SYMLINK is part of
# the tree, not a hole in it.
#
# os.walk's followlinks default is False: a symlinked subdirectory is skipped
# WHOLE, with no error and no mention. That is the ordinary monorepo layout — a
# service reaching its shared package through a link (workspaces, vendor/, a
# checked-in link to a sibling repo) — so the entire counterpart module went
# unread and the leak between it and the client came back 0. A false GREEN on
# realistic input, and the twin of the chmod-000 directory the other probe
# covers: a directory the walk does not read, changing the verdict in silence.
#
# Following links needs a cycle guard or a link loop walks forever, so the
# second probe below builds one and asserts the scan still answers.
#
# Both links here point INSIDE the scanned root, which is the only place a link
# is followed: a link whose canonical target escapes every authorized root is
# refused by name instead (exit 2) — root-escape-probe.sh captures that one.
#
#   bash scripts/symlinked-dir-probe.sh
#
# Exit 0 when the linked subtree is red (1) and the looping tree is red (1),
# 1 when either verdict is wrong, 2 on a setup fault. Skipped, out loud, on a
# filesystem that cannot create symlinks.
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

# The shared package sits in a sibling directory of the service and is reached
# ONLY by a link, which is the whole point: nothing but the link connects them,
# so os.walk's default leaves the counterpart module unread.
mkdir -p "$tmp/shared" "$tmp/repo/svc" || exit 2
cat > "$tmp/shared/webhook_contract.py" <<'EOF'
SIGNATURE_HEADER = "X-Idc-Signature"
MAX_CLOCK_SKEW_SECONDS = 300
EOF
cat > "$tmp/repo/svc/webhook_client.py" <<'EOF'
SIGNATURE_HEADER = "X-Idc-Signature"
MAX_CLOCK_SKEW_SECONDS = 300
EOF
# Two unrelated modules so the pre-fix run had >= 2 comparable files and could
# reach a VERDICT: without them it fail-closed on 2 and hid nothing.
cat > "$tmp/repo/svc/alpha.py" <<'EOF'
ALPHA_ONLY_FACT = "alpha-only-fact"
EOF
cat > "$tmp/repo/svc/beta.py" <<'EOF'
BETA_ONLY_FACT = "beta-only-fact"
EOF

if ! ln -s "$tmp/shared" "$tmp/repo/svc/shared" 2>/dev/null; then
  echo "SKIP symlinked subtree: this filesystem cannot create symlinks"
  exit 0
fi

fail=0

probe() {
  label=$1; path=$2; want=$3; shift 3
  python3 "$scan" "$path" "$@" >/dev/null 2>&1
  rc=$?
  echo "$label EXIT=$rc"
  [ "$rc" -eq "$want" ] || fail=1
}

# The leak is real and the only path to its second site is the link.
probe "symlinked subtree" "$tmp/repo" 1 --allow-root "$tmp/shared"

# A link loop must terminate on a verdict, not spin: the walk enters each
# directory once per (device, inode). Both loop links resolve back into the
# scanned root, so the cycle guard is what stops them, not the root check.
mkdir -p "$tmp/loop/sub" || exit 2
cat > "$tmp/loop/queue_client.py" <<'EOF'
QUEUE = "payments-inbound"
EOF
cat > "$tmp/loop/queue_server.py" <<'EOF'
QUEUE = "payments-inbound"
EOF
ln -s . "$tmp/loop/self" || exit 2
ln -s .. "$tmp/loop/sub/back" || exit 2
probe "link loop       " "$tmp/loop" 1

if [ "$fail" -eq 0 ]; then
  echo "PASS — the linked subtree was read, and the loop still answered"
else
  echo "FAIL — a linked subtree was skipped, or the loop did not answer"
fi
exit "$fail"
