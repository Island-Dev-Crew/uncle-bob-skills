#!/usr/bin/env bash
# interrupt-probe.sh — a Ctrl-C is a fault, not a verdict.
#
# The last exit-table row with no captured run. An unhandled KeyboardInterrupt
# does not leave through the EXIT_USAGE arm on its own — it is a BaseException,
# so `except Exception` never sees it — and whatever code the interpreter then
# picks is a code this scanner's contract does not own. The probe makes the
# interrupt land deterministically: the report is written into a pipe nobody
# reads, so the scanner blocks on a full pipe buffer, and the signal arrives
# while it is blocked rather than in a race with a fast scan.
#
#   bash scripts/interrupt-probe.sh
#
# Exit 0 when the interrupted run exits 2, 1 when it exits anything else, 2 on a
# setup fault. Skipped, out loud, when SIGINT is ignored in this process group —
# a shell that backgrounds a job sets SIGINT to SIG_IGN and CPython inherits it,
# so the signal would never be delivered and the probe would prove nothing.
set -u

here=$(cd "$(dirname "$0")" && pwd) || exit 2

python3 - "$here/leak-scan.py" <<'PY'
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time

scan = sys.argv[1]
if signal.getsignal(signal.SIGINT) is signal.SIG_IGN:
    print("SKIP interrupt probe: SIGINT is ignored in this process group, so "
          "the signal would never reach the scan")
    raise SystemExit(0)

tree = tempfile.mkdtemp()
body = "\n".join(f'F{i} = "shared-fact-number-{i}"' for i in range(4000))
for name in ("alpha.py", "beta.py"):
    pathlib.Path(tree, name).write_text(body, encoding="utf-8")

read_end, write_end = os.pipe()          # read end is never read from
proc = subprocess.Popen([sys.executable, scan, tree], stdout=write_end,
                        stderr=subprocess.PIPE, text=True)
os.close(write_end)
time.sleep(1.0)                          # 4000 leaks >> one pipe buffer
proc.send_signal(signal.SIGINT)
err = proc.communicate()[1].strip()
os.close(read_end)
print(f"interrupt EXIT={proc.returncode}")
if err:
    print(f"  stderr: {err}")
raise SystemExit(0 if proc.returncode == 2 else 1)
PY
