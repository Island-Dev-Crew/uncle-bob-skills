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
#   bash scripts/symlinked-dir-probe.sh
#
# Exit 0 when the linked subtree is red (1) and the looping tree is red (1),
# 1 when either verdict is wrong, 2 on a setup fault. Skipped, out loud, on a
# filesystem that cannot create symlinks.
set -u

here=$(cd "$(dirname "$0")" && pwd) || exit 2
scan="$here/leak-scan.py"
tmp=$(mktemp -d) || exit 2
trap 'rm -rf "$tmp"' EXIT

# The shared package lives OUTSIDE the scanned root and is reached by a link,
# which is the whole point: nothing but the link connects them.
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

if ! ln -s ../../shared "$tmp/repo/svc/shared" 2>/dev/null; then
  echo "SKIP symlinked subtree: this filesystem cannot create symlinks"
  exit 0
fi

fail=0

probe() {
  python3 "$scan" "$2" >/dev/null 2>&1
  rc=$?
  echo "$1 EXIT=$rc"
  [ "$rc" -eq "$3" ] || fail=1
}

# The leak is real and the only path to its second site is the link.
probe "symlinked subtree" "$tmp/repo" 1

# A link loop must terminate on a verdict, not spin: the walk enters each
# directory once per (device, inode).
mkdir -p "$tmp/loop" || exit 2
cat > "$tmp/loop/queue_client.py" <<'EOF'
QUEUE = "payments-inbound"
EOF
cat > "$tmp/loop/queue_server.py" <<'EOF'
QUEUE = "payments-inbound"
EOF
ln -s . "$tmp/loop/self" || exit 2
ln -s .. "$tmp/loop/up" || exit 2
probe "link loop       " "$tmp/loop" 1

if [ "$fail" -eq 0 ]; then
  echo "PASS — the linked subtree was read, and the loop still answered"
else
  echo "FAIL — a linked subtree was skipped, or the loop did not answer"
fi
exit "$fail"
