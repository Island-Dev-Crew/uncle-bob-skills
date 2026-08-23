#!/usr/bin/env bash
# fault-probes.sh - the fault paths a repo cannot store as a fixture.
#
# A permission bit and a hostile stdout encoding are process facts, not file contents,
# so they are captured here as runs instead of as trees. Each probe asserts the gate
# leaves through 2 - never through 0 or 1, which are verdicts this run never computed.
# Exits 0 when every probe held, 1 when one did not, 2 on probe-harness trouble.
set -u
here="$(cd "$(dirname "$0")/.." && pwd)"
gate="$here/scripts/plan-decay.py"
fail=0

expect() { # expect <want> <label> ; reads the actual code from $rc
  if [ "$rc" = "$1" ]; then
    echo "OK   $2 exited $rc"
  else
    echo "FAIL $2 exited $rc, wanted $1"
    fail=1
  fi
}

# 1. An unreadable subdirectory on the path the assumption names. Without a guard this
#    is a PermissionError escaping as an unhandled exception.
if [ "$(id -u)" = "0" ]; then
  echo "SKIP unreadable-directory probe: running as root, chmod 000 does not deny us"
else
  t="$(mktemp -d)" || exit 2
  mkdir -p "$t/sub" || exit 2
  : > "$t/sub/module.py" || exit 2
  printf 'exists\tsub/module.py\n' > "$t/plan.tsv" || exit 2
  chmod 000 "$t/sub" || exit 2
  python3 "$gate" --root "$t" "$t/plan.tsv" > /dev/null 2>&1
  rc=$?
  chmod 755 "$t/sub" 2>/dev/null
  rm -rf "$t"
  expect 2 "unreadable subdirectory"
fi

# 2. A stdout that cannot encode the report. UnicodeEncodeError is not an OSError, so
#    it walks past every in-run handler and lands on the seal at the bottom of the file
#    - the only proof that the BaseException arm of that seal is live.
PYTHONIOENCODING=ascii python3 "$gate" \
  --root "$here/scripts/fixtures/unicode-nfd" \
  "$here/scripts/fixtures/unicode-nfd/assumptions.tsv" > /dev/null 2>&1
rc=$?
expect 2 "un-encodable report (BaseException seal)"

# 3. An assumptions file that is a directory. IsADirectoryError is an OSError, but it
#    arrives from the read rather than from a check, so it gets its own capture.
python3 "$gate" --root "$here/scripts/fixtures/plan-holds" "$here/scripts/fixtures" > /dev/null 2>&1
rc=$?
expect 2 "assumptions file is a directory"

# 4. Two directory entries that normalise to the same name. Only a case-sensitive,
#    normalisation-PRESERVING filesystem can hold both at once, so this tree cannot be
#    stored in the repo - and on macOS the second create collides, which is the skip.
t="$(mktemp -d)" || exit 2
python3 - "$t" <<'PY'
import os, sys, unicodedata
root = sys.argv[1]
name = "café.py"                      # NFC
twin = unicodedata.normalize("NFD", name)  # canonically equal, different bytes
try:
    for n in (name, twin):
        with open(os.path.join(root, n), "x", encoding="utf-8") as fh:
            fh.write("x\n")
except (FileExistsError, OSError):
    sys.exit(3)                            # the filesystem folds them: nothing to probe
if len(os.listdir(root)) != 2:
    sys.exit(3)
with open(os.path.join(root, "plan.tsv"), "w", encoding="utf-8") as fh:
    fh.write("exists\t" + name + "\n")
PY
setup=$?
if [ "$setup" = "3" ]; then
  echo "SKIP normalisation-collision probe: this filesystem folds NFC and NFD into one entry"
elif [ "$setup" != "0" ]; then
  rm -rf "$t"; echo "FAIL normalisation-collision probe: setup exited $setup"; exit 2
else
  python3 "$gate" --root "$t" "$t/plan.tsv" > /dev/null 2>&1
  rc=$?
  expect 2 "two entries normalising to one name"
fi
rm -rf "$t"

exit "$fail"
