#!/usr/bin/env bash
# qa-bind-check.sh — enforced gate: a generated QA script carries its story binding.
#
# Usage: qa-bind-check.sh <generated-script> <qa-doc>
# Exit 0 iff the generated script names a story id, names the QA doc, carries the
# QA doc's CURRENT sha256, and is syntax-clean — so an unbound or stale script
# cannot pose as the story's gate.
set -euo pipefail

script="${1:?usage: qa-bind-check.sh <generated-script> <qa-doc>}"
qadoc="${2:?usage: qa-bind-check.sh <generated-script> <qa-doc>}"

[ -f "$script" ] || { echo "FAIL no such script: $script" >&2; exit 1; }
[ -f "$qadoc" ]  || { echo "FAIL no such QA doc: $qadoc" >&2; exit 1; }

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi | awk '{print $1}'
}

# Every header check below is LINE-ANCHORED at both ends and read as a whole line.
# Unanchored substring matching (grep -F on a bare string) passed three forged
# scripts in testing: one whose only "headers" sat inside an echo argument and a
# variable assignment, one bound to <doc>.OLD-REVISION, and one whose hash was the
# real hash plus a suffix. A binding gate that a superstring satisfies is not a gate.
resolve() { python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1"; }

grep -Eq '^# STORY: [A-Za-z0-9._-]+$' "$script" \
  || { echo "FAIL missing '# STORY: <id>' header line in $script" >&2; exit 1; }

doc_hdr="$(sed -n 's/^# QA-DOC: \(.*\)$/\1/p' "$script" | head -1)"
[ -n "$doc_hdr" ] \
  || { echo "FAIL missing '# QA-DOC: <path>' header line in $script" >&2; exit 1; }
# Compare resolved paths, not raw strings: ./doc.md, doc.md and /abs/doc.md are the
# same binding, while <doc>.OLD-REVISION resolves elsewhere and is correctly rejected.
[ "$(resolve "$doc_hdr")" = "$(resolve "$qadoc")" ] \
  || { echo "FAIL QA-DOC header binds '$doc_hdr', not '$qadoc'" >&2; exit 1; }

want="$(hash_file "$qadoc")"
grep -Eq "^# QA-SHA256: ${want}$" "$script" \
  || { echo "FAIL QA-SHA256 header absent or stale (QA doc now hashes to $want)" >&2; exit 1; }

case "$script" in
  *.sh) bash -n "$script" || { echo "FAIL bash -n: $script" >&2; exit 1; } ;;
  # compile() not py_compile: py_compile exists to WRITE bytecode, so it would drop
  # __pycache__/ into the repo this gate is checking. This form writes nothing.
  *.py) python3 -c 'import sys; compile(open(sys.argv[1]).read(), sys.argv[1], "exec")' "$script" \
          || { echo "FAIL python syntax: $script" >&2; exit 1; } ;;
esac

echo "OK bound: $(basename "$script") -> $qadoc ($want)"
