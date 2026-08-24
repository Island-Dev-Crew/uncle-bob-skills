#!/usr/bin/env bash
# aliased-file-probe.sh — one file under many spellings is ONE file.
#
# Ships the file-identity rule as a captured run rather than a sentence. Each
# probe hands leak-scan.py two spellings of a SINGLE file. A scanner keying on
# the path string counts two files and reports every literal in that one file as
# a cross-file leak (exit 1, a false red). Keying on (device, inode) collapses
# the spellings, leaving one comparable file, so the scan fail-closes with 2.
#
#   bash scripts/aliased-file-probe.sh
#
# Exit 0 when every spelling collapsed, 1 when any probe saw two files, 2 on a
# setup fault. Case and Unicode-form probes are skipped, out loud, on a
# filesystem that does not fold them.
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

cat > "$tmp/contract.py" <<'EOF'
SIGNATURE_HEADER = "X-Idc-Signature"
MAX_CLOCK_SKEW_SECONDS = 300
EOF
mkdir "$tmp/sub" || exit 2
ln "$tmp/contract.py" "$tmp/hardlink.py" || exit 2
ln -s "$tmp/contract.py" "$tmp/symlink.py" || exit 2
nfc=$(printf 'caf\xc3\xa9.py')
nfd=$(printf 'cafe\xcc\x81.py')
cp "$tmp/contract.py" "$tmp/$nfc" || exit 2

fail=0

probe() {
  python3 "$scan" "$2" "$3" >/dev/null 2>&1
  rc=$?
  echo "$1 EXIT=$rc"
  [ "$rc" -eq 2 ] || fail=1
}

probe "hard-link       " "$tmp/contract.py" "$tmp/hardlink.py"
probe "symlink         " "$tmp/contract.py" "$tmp/symlink.py"
probe "dot-segments    " "$tmp/contract.py" "$tmp/./sub/../contract.py"
probe "double-separator" "$tmp/contract.py" "$tmp//contract.py"

if [ -e "$tmp/CONTRACT.PY" ]; then
  probe "case-variant    " "$tmp/contract.py" "$tmp/CONTRACT.PY"
else
  echo "case-variant     SKIP — case-sensitive filesystem"
fi

if [ "$nfc" != "$nfd" ] && [ -e "$tmp/$nfd" ]; then
  probe "unicode NFC/NFD " "$tmp/$nfc" "$tmp/$nfd"
else
  echo "unicode NFC/NFD  SKIP — filesystem preserves Unicode form"
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS — every spelling collapsed onto one file"
else
  echo "FAIL — at least one spelling was counted as a second file"
fi
exit "$fail"
